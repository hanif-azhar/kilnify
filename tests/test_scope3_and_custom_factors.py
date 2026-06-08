"""Tests for the expanded Scope 3 categories, TSR metrics, and custom factors."""


def _emit(client, company_id, **overrides):
    body = {
        "company_id": company_id,
        "scope": "3",
        "category": "capital_goods",
        "sub_category": "machinery_spend",
        "activity_data": 1000.0,
        "activity_unit": "USD",
        "emission_factor": 0.4,
        "emission_factor_unit": "kgCO2e/USD",
        "emission_factor_source": "EXIOBASE EEIO",
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "data_quality": "estimated",
    }
    body.update(overrides)
    return client.post("/api/emissions/", json=body)


# --------------------------- Scope 3 factor library ---------------------------
def test_scope3_factors_loaded(client):
    cats = client.get("/api/factors/categories").json()
    for c in [
        "purchased_goods", "capital_goods", "fuel_energy_related",
        "upstream_transport", "waste_generated", "downstream_transport",
        "processing_sold_products", "use_sold_products",
    ]:
        assert c in cats


def test_capital_goods_spend_factor(client):
    data = client.get("/api/factors/?category=capital_goods").json()
    machinery = next(f for f in data if f["sub_category"] == "machinery_spend")
    assert machinery["factor_value"] == 0.40
    assert machinery["unit"] == "kgCO2e/USD"


# --------------------------- Scope 3 category breakdown ---------------------------
def test_scope3_category_breakdown(client, cement_company):
    cid = cement_company["id"]
    _emit(client, cid, category="capital_goods", sub_category="machinery_spend")
    _emit(client, cid, category="waste_generated", sub_category="ckd_landfill",
          activity_data=10.0, activity_unit="tonnes", emission_factor=20.0)
    _emit(client, cid, category="business_travel", sub_category="train",
          activity_data=500.0, activity_unit="passenger_km", emission_factor=0.041)

    data = client.get(f"/api/dashboard/?company_id={cid}").json()
    by_cat = {c["ghg_category"]: c for c in data["scope3_by_category"]}
    assert 2 in by_cat   # capital goods
    assert 5 in by_cat   # waste
    assert 6 in by_cat   # business travel
    assert by_cat[2]["label"].startswith("Cat 2")


# --------------------------- TSR / alternative fuel ---------------------------
def test_thermal_substitution_rate(client, cement_company):
    cid = cement_company["id"]
    # 100 t coal (26.85 GJ/t = 2685 GJ) + 100 t RDF (18 GJ/t = 1800 GJ).
    client.post("/api/emissions/", json={
        "company_id": cid, "scope": "1", "category": "kiln_fuel", "sub_category": "coal",
        "activity_data": 100.0, "activity_unit": "tonnes_fuel", "emission_factor": 2540.0,
        "emission_factor_source": "IPCC 2006", "period_start": "2025-01-01",
        "period_end": "2025-01-31", "data_quality": "measured",
    })
    client.post("/api/emissions/", json={
        "company_id": cid, "scope": "1", "category": "kiln_fuel", "sub_category": "rdf",
        "activity_data": 100.0, "activity_unit": "tonnes_fuel", "emission_factor": 495.0,
        "emission_factor_source": "Variable", "biogenic_co2_kgco2": 30000.0,
        "period_start": "2025-01-01", "period_end": "2025-01-31", "data_quality": "estimated",
    })

    m = client.get(f"/api/dashboard/?company_id={cid}").json()["alternative_fuel_metrics"]
    # TSR = 1800 / (2685 + 1800) = 40.13%
    assert round(m["thermal_substitution_rate_pct"], 1) == 40.1
    assert m["total_thermal_gj"] == 4485.0
    assert m["biogenic_share_pct"] > 0


# --------------------------- Facility gating ---------------------------
def test_processing_sold_products_cement_only(client, cement_company, grinding_company):
    ok = _emit(client, cement_company["id"], scope="3", category="processing_sold_products",
               sub_category="third_party_grinding", activity_data=1000.0,
               activity_unit="tonnes_clinker", emission_factor=34.0)
    assert ok.status_code == 201

    blocked = _emit(client, grinding_company["id"], scope="3",
                    category="processing_sold_products", sub_category="third_party_grinding",
                    activity_data=1000.0, activity_unit="tonnes_clinker", emission_factor=34.0)
    assert blocked.status_code == 422


# --------------------------- Custom factor CRUD ---------------------------
def test_custom_factor_crud_and_merge(client, cement_company):
    cid = cement_company["id"]
    payload = {
        "company_id": cid,
        "scope": "3",
        "category": "purchased_goods",
        "sub_category": "supplier_x_slag",
        "factor_value": 65.0,
        "unit": "kgCO2e/tonne",
        "activity_unit": "tonnes",
        "source": "Supplier EPD 2025",
        "year": 2025,
        "applicable_facility_types": ["cement_plant"],
    }
    created = client.post("/api/factors/custom", json=payload)
    assert created.status_code == 201, created.text
    fid = created.json()["id"]
    assert created.json()["editable"] is True
    assert created.json()["applicable_facility_types"] == ["cement_plant"]

    # Appears in the merged library, flagged editable.
    lib = client.get(f"/api/factors/?company_id={cid}").json()
    mine = next(f for f in lib if f.get("id") == fid)
    assert mine["editable"] is True
    assert mine["factor_value"] == 65.0

    # Update.
    payload["factor_value"] = 70.0
    updated = client.put(f"/api/factors/custom/{fid}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["factor_value"] == 70.0

    # Delete.
    assert client.delete(f"/api/factors/custom/{fid}").status_code == 204
    assert client.get(f"/api/factors/custom?company_id={cid}").json() == []


def test_global_custom_factor_visible_to_all(client, cement_company, grinding_company):
    client.post("/api/factors/custom", json={
        "company_id": None, "category": "purchased_goods", "sub_category": "global_additive",
        "factor_value": 12.0, "unit": "kgCO2e/tonne", "applicable_facility_types": [],
    })
    lib = client.get(f"/api/factors/?company_id={grinding_company['id']}").json()
    assert any(f["sub_category"] == "global_additive" for f in lib if f.get("editable"))


def test_company_custom_factor_scoped(client, cement_company, grinding_company):
    client.post("/api/factors/custom", json={
        "company_id": cement_company["id"], "category": "purchased_goods",
        "sub_category": "cement_only_item", "factor_value": 5.0, "unit": "kgCO2e/tonne",
    })
    other = client.get(f"/api/factors/custom?company_id={grinding_company['id']}").json()
    assert all(f["sub_category"] != "cement_only_item" for f in other)
