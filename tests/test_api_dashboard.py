def _add(client, cid, **over):
    base = {
        "company_id": cid, "scope": "1", "category": "clinker_calcination", "sub_category": "method_a",
        "activity_data": 1000, "activity_unit": "tonnes_clinker", "emission_factor": 525.0,
        "emission_factor_source": "test", "period_start": "2025-01-01", "period_end": "2025-01-31",
        "data_quality": "calculated",
    }
    base.update(over)
    r = client.post("/api/emissions/", json=base)
    assert r.status_code == 201, r.text
    return r.json()


def test_empty_dashboard(client, cement_company):
    resp = client.get(f"/api/dashboard/?company_id={cement_company['id']}")
    assert resp.status_code == 200
    assert resp.json()["total_tco2e"] == 0.0


def test_scope_math(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid)  # process: 525,000 kg = 525 t
    _add(client, cid, scope="2", category="electricity", sub_category="national",
         activity_data=100000, activity_unit="kWh", emission_factor=0.87)  # 87 t
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    assert data["scope1_process_tco2e"] == 525.0
    assert data["scope2_tco2e"] == 87.0
    assert data["total_tco2e"] == 612.0


def test_intensity_and_ratio(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid)
    client.post("/api/production/", json={
        "company_id": cid, "period_start": "2025-01-01", "period_end": "2025-01-31",
        "clinker_produced_tonnes": 1000, "cement_produced_tonnes": 1200,
        "clinker_purchased_tonnes": 0, "cement_dispatched_tonnes": 1100,
    })
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    assert data["clinker_to_cement_ratio"] == round(1000 / 1200, 4)
    # per tonne clinker = 525,000 / 1000 = 525
    assert data["intensity_kgco2e_per_tonne_clinker"] == 525.0


def test_hotspots_and_quality(client, cement_company):
    cid = cement_company["id"]
    _add(client, cid)
    _add(client, cid, scope="2", category="electricity", sub_category="national",
         activity_data=1000, activity_unit="kWh", emission_factor=0.87, data_quality="measured")
    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    assert data["top_hotspots"][0]["category"] == "clinker_calcination"
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
