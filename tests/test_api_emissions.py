def _entry(company_id, **over):
    base = {
        "company_id": company_id,
        "scope": "1",
        "category": "clinker_calcination",
        "sub_category": "method_a",
        "activity_data": 1000.0,
        "activity_unit": "tonnes_clinker",
        "emission_factor": 525.0,
        "emission_factor_unit": "kgCO2e/tonne_clinker",
        "emission_factor_source": "WBCSD CSI 2022",
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "data_quality": "calculated",
    }
    base.update(over)
    return base


def test_entry_math(client, cement_company):
    resp = client.post("/api/emissions/", json=_entry(cement_company["id"]))
    assert resp.status_code == 201
    assert resp.json()["total_emissions_kgco2e"] == 525_000.0


def test_calcination_blocked_for_grinding(client, grinding_company):
    resp = client.post("/api/emissions/", json=_entry(grinding_company["id"]))
    assert resp.status_code == 422
    assert "not available" in resp.json()["detail"]


def test_calcination_blocked_for_packing(client, packing_company):
    resp = client.post("/api/emissions/", json=_entry(packing_company["id"]))
    assert resp.status_code == 422


def test_kiln_fuel_blocked_for_packing(client, packing_company):
    resp = client.post(
        "/api/emissions/",
        json=_entry(packing_company["id"], category="kiln_fuel", sub_category="coal",
                    activity_unit="tonnes_fuel", emission_factor=2540.0),
    )
    assert resp.status_code == 422


def test_purchased_clinker_allowed_for_grinding(client, grinding_company):
    resp = client.post(
        "/api/emissions/",
        json=_entry(grinding_company["id"], scope="3", category="purchased_clinker_upstream",
                    sub_category="supplier_default", activity_data=80000, emission_factor=842.0),
    )
    assert resp.status_code == 201
    assert resp.json()["total_emissions_kgco2e"] == 80000 * 842.0


def test_electricity_allowed_all_facilities(client, packing_company):
    resp = client.post(
        "/api/emissions/",
        json=_entry(packing_company["id"], scope="2", category="electricity",
                    sub_category="java_bali", activity_unit="kWh", emission_factor=0.85),
    )
    assert resp.status_code == 201


def test_outlier_warning(client, cement_company):
    cid = cement_company["id"]
    # Two baseline entries averaging 525,000 kg.
    client.post("/api/emissions/", json=_entry(cid))
    client.post("/api/emissions/", json=_entry(cid))
    # A 10,000 t entry = 5,250,000 kg = 10x average -> warning.
    resp = client.post("/api/emissions/", json=_entry(cid, activity_data=10000))
    assert resp.status_code == 201
    assert resp.json()["warning"] is not None
    assert "Outlier" in resp.json()["warning"]


def test_negative_activity_rejected(client, cement_company):
    resp = client.post("/api/emissions/", json=_entry(cement_company["id"], activity_data=-5))
    assert resp.status_code == 422


def test_filter_by_scope(client, cement_company):
    cid = cement_company["id"]
    client.post("/api/emissions/", json=_entry(cid))
    client.post("/api/emissions/", json=_entry(cid, scope="2", category="electricity",
                                               sub_category="national", activity_unit="kWh", emission_factor=0.87))
    resp = client.get(f"/api/emissions/?company_id={cid}&scope=2")
    assert len(resp.json()) == 1
    assert resp.json()[0]["scope"] == "2"
