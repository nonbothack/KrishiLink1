import uuid


def test_create_transaction_generates_trade_aggregates(client, auth_headers, buyer_auth_headers):
    # 1. Farmer creates lot
    r_lot = client.post("/api/v1/lots", json={
        "crop": "Soybean", "grade": "A", "quantity": 50.0,
        "location_text": "Nashik Rural Center", "district": "Nashik"
    }, headers=auth_headers)
    assert r_lot.status_code == 201, f"Lot creation failed: {r_lot.status_code} - {r_lot.text}"
    lot_id = r_lot.json()["data"]["id"]

    # 2. Buyer creates offer
    r_off = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 50.0, "price_per_unit": 4150.0
    }, headers=buyer_auth_headers)
    assert r_off.status_code == 201, f"Offer creation failed: {r_off.status_code} - {r_off.text}"
    offer_id = r_off.json()["data"]["id"]

    # 3. Farmer accepts offer -> generates reservation
    r_acc = client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers)
    assert r_acc.status_code == 200, f"Offer accept failed: {r_acc.status_code} - {r_acc.text}"
    res_id = r_acc.json()["data"]["reservation_id"]

    # 4. Buyer creates transaction from reservation
    r_txn = client.post("/api/v1/transactions", json={
        "reservation_id": res_id
    }, headers=buyer_auth_headers)
    assert r_txn.status_code == 201, f"Txn create failed: {r_txn.status_code} - {r_txn.text}"
    data = r_txn.json()["data"]
    assert "id" in data
    assert "public_id" in data
    assert data["public_id"].startswith("KL-TRD-")


def test_get_trade_room_and_idor_protection(client, auth_headers, buyer_auth_headers):
    # 1. Create lot, offer, acceptance, transaction
    r_lot = client.post("/api/v1/lots", json={
        "crop": "Wheat", "grade": "A", "quantity": 40.0,
        "location_text": "Pune Hub", "district": "Pune"
    }, headers=auth_headers)
    lot_id = r_lot.json()["data"]["id"]

    r_off = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 40.0, "price_per_unit": 2300.0
    }, headers=buyer_auth_headers)
    offer_id = r_off.json()["data"]["id"]

    r_acc = client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers)
    res_id = r_acc.json()["data"]["reservation_id"]

    r_txn = client.post("/api/v1/transactions", json={"reservation_id": res_id}, headers=buyer_auth_headers)
    txn_id = r_txn.json()["data"]["id"]

    # 2. Buyer accesses trade room
    r_room = client.get(f"/api/v1/trades/{txn_id}/room", headers=buyer_auth_headers)
    assert r_room.status_code == 200
    room = r_room.json()["data"]
    assert room["id"] == txn_id
    assert room["public_id"].startswith("KL-TRD-")
    assert room["terms"]["crop_name"] == "Wheat"
    assert room["terms"]["grade"] == "A"
    assert room["payment"]["provider_connected"] is False
    assert room["payment"]["provider_verified"] is False
    assert room["payment"]["status"] == "NO_PROVIDER_DATA"
    assert "do not prove funds moved" in room["payment"]["note"]
    assert room["terms"]["delivery_window"] is None
    assert room["terms"]["delivery_location"] is None
    assert room["payment"].get("transport_cost") is None
    assert room["payment"].get("platform_fee") is None
    assert room["quality"]["agreed_grade"] == "A"
    assert "No verified assay" in room["quality"]["note"]
    assert room["next_action"]["action_type"] == "REPORT_PAYMENT_SENT"
    assert room["next_action"]["is_current_user_action"] is True
    assert len(room["timeline"]) >= 1

    # 3. Farmer accesses trade room
    r_farmer = client.get(f"/api/v1/trades/{txn_id}/room", headers=auth_headers)
    assert r_farmer.status_code == 200
    farmer_room = r_farmer.json()["data"]
    assert farmer_room["next_action"]["is_current_user_action"] is False  # Action is on buyer to pay

    # 4. Third-party stranger user cannot access (IDOR protection)
    unique_email = f"stranger-{uuid.uuid4().hex[:6]}@example.com"
    r_reg = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Stranger User",
        "role": "farmer",
    })
    stranger_token = r_reg.json()["data"]["access_token"]
    r_idor = client.get(f"/api/v1/trades/{txn_id}/room", headers={"Authorization": f"Bearer {stranger_token}"})
    assert r_idor.status_code == 403
    assert "Forbidden" in r_idor.json().get("detail", "")


def test_trade_fsm_lifecycle_and_rbac(client, auth_headers, buyer_auth_headers):
    # Setup trade
    r_lot = client.post("/api/v1/lots", json={
        "crop": "Onion", "grade": "B", "quantity": 60.0,
        "location_text": "Lasalgaon Market", "district": "Nashik"
    }, headers=auth_headers)
    lot_id = r_lot.json()["data"]["id"]

    r_off = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 60.0, "price_per_unit": 1800.0
    }, headers=buyer_auth_headers)
    offer_id = r_off.json()["data"]["id"]

    r_acc = client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers)
    res_id = r_acc.json()["data"]["reservation_id"]

    r_txn = client.post("/api/v1/transactions", json={"reservation_id": res_id}, headers=buyer_auth_headers)
    txn_id = r_txn.json()["data"]["id"]

    # Neither participant nor the legacy transaction endpoint can manufacture
    # provider-confirmed payment. A user-entered reference remains a report.
    denied = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=auth_headers,
        json={"to_status": "PAYMENT_CONFIRMED"},
    )
    assert denied.status_code == 409
    denied_buyer = client.post(
        f"/api/v1/transactions/{txn_id}/transition",
        headers=buyer_auth_headers,
        json={"to_status": "PAYMENT_CONFIRMED"},
    )
    assert denied_buyer.status_code == 409

    payment = client.post(
        f"/api/v1/trades/{txn_id}/payment-reports",
        headers={**buyer_auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"amount": "108000.00", "reference": "USER-ENTERED-UTR-42", "currency": "INR"},
    )
    assert payment.status_code == 201, payment.text
    buyer_room = client.get(f"/api/v1/trades/{txn_id}/room", headers=buyer_auth_headers).json()["data"]
    assert buyer_room["payment"]["provider_verified"] is False
    assert buyer_room["payment"]["reports"][0]["reference"] == "USER-ENTERED-UTR-42"
    assert buyer_room["status"] == "CREATED"
    payment_id = buyer_room["payment"]["reports"][0]["id"]

    ack = client.post(
        f"/api/v1/trades/{txn_id}/payment-reports/{payment_id}/acknowledge",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert ack.status_code == 201, ack.text
    acknowledged = client.get(f"/api/v1/trades/{txn_id}/room", headers=auth_headers).json()["data"]
    assert acknowledged["payment"]["status"] == "SELLER_ACKNOWLEDGED_REPORTED"
    assert acknowledged["payment"]["provider_verified"] is False

    dispatch = client.post(
        f"/api/v1/trades/{txn_id}/logistics-updates",
        headers={**auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"kind": "DISPATCH_REPORTED", "details": "Seller statement only"},
    )
    receipt = client.post(
        f"/api/v1/trades/{txn_id}/logistics-updates",
        headers={**buyer_auth_headers, "Idempotency-Key": str(uuid.uuid4())},
        json={"kind": "RECEIPT_CONFIRMED", "details": "Buyer statement only"},
    )
    assert dispatch.status_code == 201
    assert receipt.status_code == 201
    room = client.get(f"/api/v1/trades/{txn_id}/room", headers=buyer_auth_headers).json()["data"]
    assert room["status"] == "CREATED"
    assert room["logistics"]["provider_connected"] is False
    assert {event["event_type"] for event in room["timeline"]} >= {
        "PAYMENT_REPORTED_SENT", "PAYMENT_RECEIPT_ACKNOWLEDGED", "LOGISTICS_DISPATCH_REPORTED", "LOGISTICS_RECEIPT_CONFIRMED"
    }


def test_add_trade_note(client, auth_headers, buyer_auth_headers):
    r_lot = client.post("/api/v1/lots", json={
        "crop": "Tomato", "grade": "A", "quantity": 30.0,
        "location_text": "Nashik Farm", "district": "Nashik"
    }, headers=auth_headers)
    lot_id = r_lot.json()["data"]["id"]

    r_off = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 30.0, "price_per_unit": 1500.0
    }, headers=buyer_auth_headers)
    offer_id = r_off.json()["data"]["id"]

    r_acc = client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers)
    res_id = r_acc.json()["data"]["reservation_id"]

    r_txn = client.post("/api/v1/transactions", json={"reservation_id": res_id}, headers=buyer_auth_headers)
    txn_id = r_txn.json()["data"]["id"]

    # Add note as buyer
    r_note = client.post(
        f"/api/v1/trades/{txn_id}/notes",
        headers=buyer_auth_headers,
        json={"note": "Please pack with extra cushioning crates."},
    )
    assert r_note.status_code == 201
    note_data = r_note.json()["data"]
    assert note_data["event_type"] == "USER_NOTE"
    assert "extra cushioning crates" in note_data["description"]

    # Verify note appears in Trade Room timeline
    r_room = client.get(f"/api/v1/trades/{txn_id}/room", headers=auth_headers)
    timeline = r_room.json()["data"]["timeline"]
    assert any(ev["event_type"] == "USER_NOTE" and "extra cushioning crates" in ev["description"] for ev in timeline)
