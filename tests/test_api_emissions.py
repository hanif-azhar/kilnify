import pytest

from backend.constants import SCOPE3_ONLY


def _entry(company_id, **over):
    """Default to a Scope 3 outbound-transport entry (allowed for all facilities)."""
    base = {
        "company_id": company_id,
        "scope": "3",
        "category": "transport_outbound",
        "sub_category": "truck_heavy_over_32t",
        "activity_data": 1000.0,
        "activity_unit": "tonne_km",
        "emission_factor": 0.062,
        "emission_factor_unit": "kgCO2e/tonne_km",
        "emission_factor_source": "DEFRA 2024",
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "data_quality": "calculated",
    }
    base.update(over)
    return base


def test_entry_math(client, cement_company):
    resp = client.post("/api/emissions/", json=_entry(cement_company["id"]))
    assert resp.status_code == 201
    assert resp.json()["total_emissions_kgco2e"] == 1000.0 * 0.062


@pytest.mark.skipif(not SCOPE3_ONLY, reason="Scope 3-only gating disabled")
def test_scope1_rejected(client, cement_company):
    resp = client.post(
        "/api/emissions/",
        json=_entry(cement_company["id"], scope="1", category="clinker_calcination",
                    sub_category="method_a", activity_unit="tonnes_clinker", emission_factor=525.0),
    )
    assert resp.status_code == 422
    assert "Scope 3" in resp.json()["detail"]


@pytest.mark.skipif(not SCOPE3_ONLY, reason="Scope 3-only gating disabled")
def test_scope2_rejected(client, packing_company):
    resp = client.post(
        "/api/emissions/",
        json=_entry(packing_company["id"], scope="2", category="electricity",
                    sub_category="java_bali", activity_unit="kWh", emission_factor=0.85),
    )
    assert resp.status_code == 422
    assert "Scope 3" in resp.json()["detail"]


def test_purchased_clinker_allowed_for_grinding(client, grinding_company):
    resp = client.post(
        "/api/emissions/",
        json=_entry(grinding_company["id"], category="purchased_clinker_upstream",
                    sub_category="supplier_default", activity_data=80000,
                    activity_unit="tonnes_clinker", emission_factor=842.0),
    )
    assert resp.status_code == 201
    assert resp.json()["total_emissions_kgco2e"] == 80000 * 842.0


def test_purchased_clinker_blocked_for_cement(client, cement_company):
    """purchased_clinker_upstream is a grinding-plant-only Scope 3 category."""
    resp = client.post(
        "/api/emissions/",
        json=_entry(cement_company["id"], category="purchased_clinker_upstream",
                    sub_category="supplier_default", activity_data=80000,
                    activity_unit="tonnes_clinker", emission_factor=842.0),
    )
    assert resp.status_code == 422
    assert "not available" in resp.json()["detail"]


def test_packaging_accepted_by_backend_for_cement(client, cement_company):
    """packaging is restricted to grinding/packing in the frontend catalog only.
    It is not in FACILITY_RESTRICTED_CATEGORIES, so the backend accepts it."""
    resp = client.post(
        "/api/emissions/",
        json=_entry(cement_company["id"], category="packaging", sub_category="paper_bag_50kg",
                    activity_data=100, activity_unit="units", emission_factor=0.55),
    )
    assert resp.status_code == 201


def test_outlier_warning(client, cement_company):
    cid = cement_company["id"]
    # Two baseline entries averaging 62 kg.
    client.post("/api/emissions/", json=_entry(cid))
    client.post("/api/emissions/", json=_entry(cid))
    # A 100,000 tonne_km entry = 6,200 kg = 100x average -> warning.
    resp = client.post("/api/emissions/", json=_entry(cid, activity_data=100000))
    assert resp.status_code == 201
    assert resp.json()["warning"] is not None
    assert "Outlier" in resp.json()["warning"]


def test_negative_activity_rejected(client, cement_company):
    resp = client.post("/api/emissions/", json=_entry(cement_company["id"], activity_data=-5))
    assert resp.status_code == 422


def test_filter_by_scope(client, cement_company):
    cid = cement_company["id"]
    client.post("/api/emissions/", json=_entry(cid))
    client.post("/api/emissions/", json=_entry(cid, category="business_travel",
                                               sub_category="train", activity_unit="passenger_km",
                                               emission_factor=0.041))
    resp = client.get(f"/api/emissions/?company_id={cid}&scope=3")
    assert len(resp.json()) == 2
    assert all(e["scope"] == "3" for e in resp.json())
