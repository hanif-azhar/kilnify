def _seed_cement(client, cid):
    """Seed a cement plant with process, combustion, scope2, scope3 entries + production."""
    entries = [
        # Scope 1 process
        dict(scope="1", category="clinker_calcination", sub_category="method_a",
             activity_data=150000, activity_unit="tonnes_clinker", emission_factor=525.0),
        # Scope 1 combustion
        dict(scope="1", category="kiln_fuel", sub_category="coal",
             activity_data=20000, activity_unit="tonnes_fuel", emission_factor=2540.0),
        # Scope 1 mobile
        dict(scope="1", category="mobile_equipment", sub_category="diesel",
             activity_data=10000, activity_unit="liters", emission_factor=2.68),
        # Scope 1 fugitive
        dict(scope="1", category="refrigerants", sub_category="r410a",
             activity_data=10, activity_unit="kg", emission_factor=2088.0),
        # Scope 2
        dict(scope="2", category="electricity", sub_category="java_bali",
             activity_data=1_000_000, activity_unit="kWh", emission_factor=0.85),
        # Scope 3
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


def test_generate_report_scope_subtypes(client, cement_company):
    cid = cement_company["id"]
    _seed_cement(client, cid)
    resp = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-03", "period_start": "2025-03-01",
        "period_end": "2025-03-31", "status": "draft",
    })
    assert resp.status_code == 201
    r = resp.json()
    # Process: 150000*525/1000 = 78,750 tCO2e
    assert r["total_scope1_process"] == 78750.0
    # Combustion: 20000*2540/1000 = 50,800
    assert r["total_scope1_combustion"] == 50800.0
    # Mobile: 10000*2.68/1000 = 26.8
    assert r["total_scope1_mobile"] == 26.8
    # Fugitive: 10*2088/1000 = 20.88
    assert r["total_scope1_fugitive"] == 20.88
    # Scope 2: 1e6 * 0.85 / 1000 = 850
    assert r["total_scope2_lb"] == 850.0
    # Scope 3: 1e6 * 0.062 / 1000 = 62
    assert r["total_scope3"] == 62.0


def test_intensity_metrics(client, cement_company):
    cid = cement_company["id"]
    _seed_cement(client, cid)
    resp = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-03", "period_start": "2025-03-01",
        "period_end": "2025-03-31", "status": "draft",
    })
    r = resp.json()
    assert r["clinker_to_cement_ratio"] == 0.8108
    # per tonne clinker = process kg / clinker = 78,750,000 / 150,000 = 525
    assert r["specific_emissions_per_tonne_clinker"] == 525.0


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
    assert len(detail["entries"]) == 6
    assert len(detail["top_hotspots"]) <= 5


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
    assert "clinker_calcination" in resp.text


def test_biogenic_excluded_from_total(client, cement_company):
    cid = cement_company["id"]
    # Single entry with biogenic CO2 declared.
    client.post("/api/emissions/", json={
        "company_id": cid, "scope": "1", "category": "kiln_fuel", "sub_category": "rdf",
        "activity_data": 1000, "activity_unit": "tonnes_fuel", "emission_factor": 495.0,
        "emission_factor_source": "test", "biogenic_co2_kgco2": 200000,
        "period_start": "2025-04-01", "period_end": "2025-04-30", "data_quality": "calculated",
    })
    rep = client.post("/api/reports/generate", json={
        "company_id": cid, "report_period": "2025-04", "period_start": "2025-04-01",
        "period_end": "2025-04-30", "status": "draft",
    }).json()
    # total = 1000*495/1000 = 495 tCO2e; biogenic disclosed separately = 200 tCO2
    assert rep["total_emissions"] == 495.0
    assert rep["biogenic_co2_total"] == 200.0
