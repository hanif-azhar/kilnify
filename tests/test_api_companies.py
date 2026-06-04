def test_create_and_get_company(client):
    resp = client.post(
        "/api/companies/",
        json={"name": "Test Plant", "facility_type": "cement_plant", "grid_region": "national"},
    )
    assert resp.status_code == 201
    cid = resp.json()["id"]

    got = client.get(f"/api/companies/{cid}")
    assert got.status_code == 200
    assert got.json()["facility_type"] == "cement_plant"


def test_invalid_facility_type_rejected(client):
    resp = client.post(
        "/api/companies/",
        json={"name": "Bad", "facility_type": "steel_plant"},
    )
    assert resp.status_code == 422


def test_list_companies(client, cement_company, grinding_company):
    resp = client.get("/api/companies/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_missing_company_404(client):
    assert client.get("/api/companies/nope").status_code == 404


def test_delete_company(client, cement_company):
    cid = cement_company["id"]
    assert client.delete(f"/api/companies/{cid}").status_code == 204
    assert client.get(f"/api/companies/{cid}").status_code == 404
