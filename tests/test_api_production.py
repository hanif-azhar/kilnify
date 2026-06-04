def _payload(company_id, **over):
    base = {
        "company_id": company_id,
        "period_start": "2025-01-01",
        "period_end": "2025-01-31",
        "clinker_produced_tonnes": 150000,
        "clinker_purchased_tonnes": 0,
        "cement_produced_tonnes": 185000,
        "cement_dispatched_tonnes": 180000,
    }
    base.update(over)
    return base


def test_ratio_autocalc(client, cement_company):
    resp = client.post("/api/production/", json=_payload(cement_company["id"]))
    assert resp.status_code == 201
    # 150000 / 185000 = 0.8108
    assert resp.json()["clinker_to_cement_ratio"] == 0.8108


def test_ratio_includes_purchased(client, grinding_company):
    resp = client.post(
        "/api/production/",
        json=_payload(
            grinding_company["id"],
            clinker_produced_tonnes=0,
            clinker_purchased_tonnes=80000,
            cement_produced_tonnes=100000,
        ),
    )
    assert resp.status_code == 201
    assert resp.json()["clinker_to_cement_ratio"] == 0.8


def test_ratio_out_of_bounds_rejected(client, cement_company):
    # clinker 200000 / cement 100000 = 2.0 -> out of 0.50-1.00 bound
    resp = client.post(
        "/api/production/",
        json=_payload(cement_company["id"], clinker_produced_tonnes=200000, cement_produced_tonnes=100000),
    )
    assert resp.status_code == 422


def test_bad_date_range_rejected(client, cement_company):
    resp = client.post(
        "/api/production/",
        json=_payload(cement_company["id"], period_start="2025-02-01", period_end="2025-01-01"),
    )
    assert resp.status_code == 422


def test_filter_by_company(client, cement_company, grinding_company):
    client.post("/api/production/", json=_payload(cement_company["id"]))
    resp = client.get(f"/api/production/?company_id={grinding_company['id']}")
    assert resp.json() == []


def test_negative_value_rejected(client, cement_company):
    resp = client.post(
        "/api/production/",
        json=_payload(cement_company["id"], clinker_produced_tonnes=-5),
    )
    assert resp.status_code == 422
