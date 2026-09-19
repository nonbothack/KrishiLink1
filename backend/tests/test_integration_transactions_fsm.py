import uuid


def test_transaction_fsm(client, auth_headers, buyer_auth_headers):
    # Ensure lot exists
    r = client.get("/api/v1/lots", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    if not items:
        r_lot = client.post("/api/v1/lots", json={
            "crop": "Wheat", "grade": "A", "quantity": 100.0,
            "location_text": "Nashik Market", "district": "Nashik"
        }, headers=auth_headers)
        assert r_lot.status_code == 201
        lot_id = r_lot.json()["data"]["id"]
    else:
        lot_id = items[0]["id"]

    # Buyer creates offer
    r2 = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 10.0, "price_per_unit": 2000.0
    }, headers=buyer_auth_headers)
    assert r2.status_code == 201
    offer_id = r2.json()["data"]["id"]

    # Farmer accepts -> creates reservation
    r3 = client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers)
    assert r3.status_code == 200
    reservation_id = r3.json()["data"]["reservation_id"]
    assert reservation_id is not None

    # Buyer creates transaction from reservation
    r4 = client.post("/api/v1/transactions", json={
        "reservation_id": reservation_id
    }, headers=buyer_auth_headers)
    assert r4.status_code == 201
    txn_data = r4.json()["data"]
    txn_id = txn_data["id"]
    # Contractual pricing check: 10 qty * 2000 price = 20000.0 (not hardcoded 10*10)
    assert float(txn_data["gross_value"]) == 20000.0

    # Payment references are participant reports; only a configured provider may
    # mark a payment confirmed. This installation has no provider.
    transitions = ["PAYMENT_PENDING"]
    for status in transitions:
        r5 = client.post(f"/api/v1/transactions/{txn_id}/transition", json={
            "to_status": status
        }, headers=buyer_auth_headers)
        assert r5.status_code == 200
        assert r5.json()["data"]["status"] == status

    rejected = client.post(f"/api/v1/transactions/{txn_id}/transition", json={
        "to_status": "PAYMENT_CONFIRMED"
    }, headers=buyer_auth_headers)
    assert rejected.status_code == 409
    assert "payment provider" in rejected.json()["detail"].lower()

def test_transaction_ownership_rejection(client, auth_headers, buyer_auth_headers):
    # Ensure lot exists
    r_lot = client.post("/api/v1/lots", json={
        "crop": "Wheat", "grade": "A", "quantity": 50.0,
        "location_text": "Nashik Market", "district": "Nashik"
    }, headers=auth_headers)
    assert r_lot.status_code == 201
    lot_id = r_lot.json()["data"]["id"]

    # Buyer creates offer
    r2 = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 5.0, "price_per_unit": 2200.0
    }, headers=buyer_auth_headers)
    assert r2.status_code == 201
    offer_id = r2.json()["data"]["id"]

    # Farmer accepts -> creates reservation for buyer
    r3 = client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers)
    assert r3.status_code == 200
    reservation_id = r3.json()["data"]["reservation_id"]

    # Attempt to consume reservation as farmer (mismatched user) -> must be rejected with 403 Forbidden
    r4 = client.post("/api/v1/transactions", json={
        "reservation_id": reservation_id
    }, headers=auth_headers)
    assert r4.status_code == 403
    assert "Forbidden" in r4.json()["detail"]

def test_transactions_list(client, buyer_auth_headers):
    r = client.get("/api/v1/transactions", headers=buyer_auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True

def test_invalid_transition(client, buyer_auth_headers):
    fake_id = str(uuid.uuid4())
    r = client.post(f"/api/v1/transactions/{fake_id}/transition", json={
        "to_status": "INVALID_STATUS"
    }, headers=buyer_auth_headers)
    assert r.status_code in (404, 409, 422)
