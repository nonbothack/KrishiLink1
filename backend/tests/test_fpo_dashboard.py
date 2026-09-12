import pytest


def test_fpo_summary(client, fpo_auth_headers):
    r = client.get("/api/v1/fpo/summary", headers=fpo_auth_headers)
    assert r.status_code == 200
    res = r.json()
    assert res["success"] is True
    data = res["data"]
    assert "total_members" in data
    assert data["total_members"] >= 6
    assert "active_lots" in data
    assert "total_volume_qtl" in data
    assert "pending_offers" in data


def test_fpo_members_list_and_create(client, fpo_auth_headers):
    # List members
    r = client.get("/api/v1/fpo/members", headers=fpo_auth_headers)
    assert r.status_code == 200
    res = r.json()
    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) >= 6

    # Create new member
    new_member_payload = {
        "farmer_name": "Tukaram Shinde",
        "phone": "9820019999",
        "village": "Ozar",
        "district": "Nashik",
        "land_acres": 5.5,
        "primary_crop": "Onion",
        "ready_quantity_qtl": 180.0,
        "grade": "A",
    }
    r2 = client.post("/api/v1/fpo/members", json=new_member_payload, headers=fpo_auth_headers)
    assert r2.status_code == 201
    res2 = r2.json()
    assert res2["success"] is True
    assert res2["data"]["farmer_name"] == "Tukaram Shinde"
    assert res2["data"]["ready_quantity_qtl"] == 180.0


def test_fpo_aggregate_lot(client, fpo_auth_headers):
    # Retrieve members to aggregate
    r_members = client.get("/api/v1/fpo/members", headers=fpo_auth_headers)
    member_ids = [m["id"] for m in r_members.json()["data"][:2]]

    aggregate_payload = {
        "crop": "Onion",
        "quantity": 500.0,
        "unit": "quintal",
        "grade": "A",
        "asking_price": 1950.0,
        "location_text": "Nashik FPO Central Hub",
        "district": "Nashik",
        "member_ids": member_ids,
        "notes": "Bulk Grade A Onion collection from certified members",
    }
    r = client.post("/api/v1/fpo/aggregate-lot", json=aggregate_payload, headers=fpo_auth_headers)
    assert r.status_code == 201
    res = r.json()
    assert res["success"] is True
    data = res["data"]
    assert data["public_id"].startswith("KL-LOT-")
    assert data["crop"] == "Onion"
    assert data["quantity"] == 500.0
    assert data["asking_price"] == 1950.0

    # Verify lot appears in FPO's lots list
    r_lots = client.get("/api/v1/fpo/lots", headers=fpo_auth_headers)
    assert r_lots.status_code == 200
    lots = r_lots.json()["data"]
    assert any(l["id"] == data["id"] for l in lots)


def test_fpo_endpoints_rbac_protection(client, auth_headers):
    # Standard farmer should NOT be allowed to manage FPO endpoints
    r = client.get("/api/v1/fpo/summary", headers=auth_headers)
    assert r.status_code == 403

    r_unauth = client.get("/api/v1/fpo/summary")
    assert r_unauth.status_code == 401
