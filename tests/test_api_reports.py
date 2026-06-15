import pytest

from backend.constants import SCOPE3_ONLY


def _seed_cement(client, cid):
    """Seed a cement plant with a spread of Scope 3 value-chain entries + production."""
    entries = [
        # Cat 1 — purchased goods (SCM)
        dict(scope="3", category="purchased_goods", sub_category="ggbfs_slag",
             activity_data=10000, activity_unit="tonnes", emission_factor=80.0),
        # Cat 4 — upstream transport
        dict(scope="3", category="upstream_transport", sub_category="truck_heavy_over_32t",
             activity_data=500000, activity_unit="tonne_km", emission_factor=0.062),
        # Cat 6 — business travel
        dict(scope="3", category="business_travel", sub_category="flight_short_haul",
             activity_data=20000, activity_unit="passenger_km", emission_factor=0.255),
        # Cat 9 — downstream transport
        dict(scope="3", category="transport_outbound", sub_category="truck_heavy_over_32t",
             activity_data=1_000_000, activity_unit="tonne_km", emission_factor=0.062),
    ]
    for e in entries:
        e.update(company_id=cid, emission_factor_source="test", emission_factor_unit="x",
                 period_start="2025-03-01", period_end="2025-03-31", data_quality="calculated")
        r = client.post("/api/emissions/", json=e)
        assert r.status_code == 201, r.text

    client.post("/api/production/", json={
        "company_id": cid, "period_start": "2025-03-01", "period_end": "2025-03-31",
        "clinker_produced_tonnes": 150000, "clinker_purchased_tonnes": 0,
        "cement_produced_tonnes": 185000, "cement_dispatched_tonnes": 180000,
    })


def test_generate_report_scope3_total(client, cement_company):
    cid = cement_company["id"]
    _seed_cement(client, cid)
    resp = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-03", "period_start": "2025-03-01",
        "period_end": "2025-03-31", "status": "draft",
    })
    assert resp.status_code == 201
    r = resp.json()
    # Cat1: 10000*80=800,000 ; Cat4: 500000*0.062=31,000 ; Cat6: 20000*0.255=5,100 ;
    # Cat9: 1e6*0.062=62,000 -> total 898,100 kg = 898.1 t
    assert r["total_scope3"] == 898.1
    if SCOPE3_ONLY:
        # No Scope 1/2 entries can exist, so those totals are zero.
        assert r["total_scope1"] == 0.0
        assert r["total_scope2_lb"] == 0.0


def test_report_detail_and_disclaimer(client, cement_company):
    cid = cement_company["id"]
    _seed_cement(client, cid)
    rep = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-03", "period_start": "2025-03-01",
        "period_end": "2025-03-31", "status": "final",
    }).json()
    detail = client.get(f"/api/reports/{rep['id']}/detail").json()
    assert "disclaimer" in detail and detail["disclaimer"]
    assert len(detail["methodology_notes"]) > 0
    assert len(detail["entries"]) == 4
    assert len(detail["top_hotspots"]) <= 5
    # Scope 3 category breakdown is always present in the detail payload.
    assert len(detail["scope3_by_category"]) >= 1


def test_csv_export(client, cement_company):
    cid = cement_company["id"]
    _seed_cement(client, cid)
    rep = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-03", "period_start": "2025-03-01",
        "period_end": "2025-03-31", "status": "draft",
    }).json()
    resp = client.get(f"/api/reports/{rep['id']}/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "transport_outbound" in resp.text


def test_biogenic_excluded_from_total(client, cement_company):
    cid = cement_company["id"]
    # Scope 3 entry with biogenic CO2 declared separately.
    client.post("/api/emissions/", json={
        "company_id": cid, "scope": "3", "category": "purchased_goods", "sub_category": "ggbfs_slag",
        "activity_data": 10000, "activity_unit": "tonnes", "emission_factor": 80.0,
        "emission_factor_source": "test", "biogenic_co2_kgco2": 200000,
        "period_start": "2025-04-01", "period_end": "2025-04-30", "data_quality": "calculated",
    })
    rep = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-04", "period_start": "2025-04-01",
        "period_end": "2025-04-30", "status": "draft",
    }).json()
    # total = 10000*80/1000 = 800 tCO2e; biogenic disclosed separately = 200 tCO2
    assert rep["total_scope3"] == 800.0
    assert rep["biogenic_co2_total"] == 200.0
