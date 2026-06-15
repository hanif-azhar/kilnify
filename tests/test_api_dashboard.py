import pytest

from backend.constants import SCOPE3_ONLY


def _add(client, cid, **over):
    """Default to a Scope 3 outbound-transport entry."""
    base = {
        "company_id": cid, "scope": "3", "category": "transport_outbound",
        "sub_category": "truck_heavy_over_32t", "activity_data": 1000,
        "activity_unit": "tonne_km", "emission_factor": 0.062,
        "emission_factor_source": "test", "period_start": "2025-01-01",
        "period_end": "2025-01-31", "data_quality": "calculated",
    }
    base.update(over)
    r = client.post("/api/emissions/", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def test_empty_dashboard(client, cement_company):
    resp = client.get(f"/api/dashboard/?company_id={cement_company['id']}")
    assert resp.status_code == 200
    assert resp.json()["total_tco2e"] == 0.0


def test_scope3_math(client, cement_company):
    cid = cement_company["id"]
    # transport: 100,000 * 0.062 = 6,200 kg = 6.2 t
    _add(client, cid, activity_data=100000)
    # business travel: 10,000 * 0.041 = 410 kg = 0.41 t
    _add(client, cid, category="business_travel", sub_category="train",
         activity_data=10000, activity_unit="passenger_km", emission_factor=0.041)
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    assert data["scope3_tco2e"] == 6.61
    assert data["total_tco2e"] == 6.61


@pytest.mark.skipif(SCOPE3_ONLY, reason="Scope 1/2 intensity hidden in Scope 3-only mode")
def test_intensity_and_ratio(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid, scope="1", category="clinker_calcination", sub_category="method_a",
         activity_unit="tonnes_clinker", emission_factor=525.0)
    client.post("/api/production/", json={
        "company_id": cid, "period_start": "2025-01-01", "period_end": "2025-01-31",
        "clinker_produced_tonnes": 1000, "cement_produced_tonnes": 1200,
        "clinker_purchased_tonnes": 0, "cement_dispatched_tonnes": 1100,
    })
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    assert data["clinker_to_cement_ratio"] == round(1000 / 1200, 4)
    assert data["intensity_kgco2e_per_tonne_clinker"] == 525.0


def test_scope3_by_category(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid)  # transport_outbound -> Cat 9
    _add(client, cid, category="business_travel", sub_category="train",
         activity_data=500, activity_unit="passenger_km", emission_factor=0.041)  # Cat 6
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    cats = {c["ghg_category"] for c in data["scope3_by_category"]}
    assert 9 in cats
    assert 6 in cats


def test_hotspots_and_quality(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid, activity_data=100000)
    _add(client, cid, category="business_travel", sub_category="train",
         activity_data=1000, activity_unit="passenger_km", emission_factor=0.041,
         data_quality="measured")
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    assert data["top_hotspots"][0]["category"] == "transport_outbound"
    assert data["data_quality_summary"]["calculated"] == 1
    assert data["data_quality_summary"]["measured"] == 1


def test_company_isolation(client, cement_company, grinding_company):
    _add(client, cement_company["id"])
    data = client.get(f"/api/dashboard/?company_id={grinding_company['id']}").json()
    assert data["total_tco2e"] == 0.0


def test_monthly_trend(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid, period_start="2025-01-01", period_end="2025-01-31")
    _add(client, cid, period_start="2025-02-01", period_end="2025-02-28")
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    months = [m["month"] for m in data["monthly_trend"]]
    assert months == ["2025-01", "2025-02"]
