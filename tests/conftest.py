"""Shared pytest fixtures.

Uses a session-scoped in-memory SQLite DB, truncated between tests for isolation.
The production get_db dependency is overridden with the test session.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app

# StaticPool keeps a single shared in-memory connection across sessions.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _truncate_tables():
    """Clear all tables between tests for isolation."""
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_company(client, facility_type, name):
    resp = client.post(
        "/api/companies/",
        json={
            "name": name,
            "facility_type": facility_type,
            "country": "Indonesia",
            "grid_region": "java_bali",
            "reporting_year": 2025,
            "headcount": 100,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def cement_company(client):
    return _make_company(client, "cement_plant", "Tuban Cement Plant")


@pytest.fixture
def grinding_company(client):
    return _make_company(client, "grinding_plant", "Surabaya Grinding Plant")


@pytest.fixture
def packing_company(client):
    return _make_company(client, "packing_plant", "Makassar Packing Plant")


@pytest.fixture
def production_entry(client, cement_company):
    resp = client.post(
        "/api/production/",
        json={
            "company_id": cement_company["id"],
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "clinker_produced_tonnes": 150000,
            "clinker_purchased_tonnes": 0,
            "cement_produced_tonnes": 185000,
            "cement_dispatched_tonnes": 180000,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def emission_entry(client, cement_company):
    resp = client.post(
        "/api/emissions/",
        json={
            "company_id": cement_company["id"],
            "scope": "1",
            "category": "clinker_calcination",
            "sub_category": "method_a",
            "activity_data": 150000.0,
            "activity_unit": "tonnes_clinker",
            "emission_factor": 525.0,
            "emission_factor_unit": "kgCO2e/tonne_clinker",
            "emission_factor_source": "WBCSD CSI 2022",
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "data_quality": "calculated",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
