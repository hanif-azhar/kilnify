def test_list_all_factors(client):
    resp = client.get("/api/factors/")
    assert resp.status_code == 200
    assert len(resp.json()) > 10


def test_categories(client):
    resp = client.get("/api/factors/categories")
    cats = resp.json()
    assert "clinker_process" in cats
    assert "electricity" in cats
    assert "packaging" in cats


def test_filter_by_category(client):
    resp = client.get("/api/factors/?category=electricity")
    data = resp.json()
    assert all(f["category"] == "electricity" for f in data)
    subs = {f["sub_category"] for f in data}
    assert "java_bali" in subs


def test_grid_factor_value(client):
    data = client.get("/api/factors/?category=electricity").json()
    java = next(f for f in data if f["sub_category"] == "java_bali")
    assert java["factor_value"] == 0.85


def test_filter_by_facility_type(client):
    # Packaging factors should not be applicable to cement_plant.
    data = client.get("/api/factors/?facility_type=cement_plant").json()
    assert all("cement_plant" in f["applicable_facility_types"] for f in data)
    assert not any(f["category"] == "packaging" for f in data)


def test_search(client):
    data = client.get("/api/factors/?search=coal").json()
    assert any("coal" in (f["sub_category"] or "") for f in data)


def test_clinker_default_ef(client):
    data = client.get("/api/factors/?category=clinker_process").json()
    method_a = next(f for f in data if f["sub_category"] == "method_a")
    assert method_a["factor_value"] == 525.0
