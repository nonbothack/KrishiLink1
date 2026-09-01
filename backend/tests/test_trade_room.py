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
    assert room["payment"]["is_sandbox"] is True
    assert "Sandbox" in room["payment"]["note"]
    assert room["quality"]["agreed_grade"] == "A"
    assert "scheduled in Phase 7" in room["quality"]["note"]
    assert room["next_action"]["action_type"] == "CONFIRM_PAYMENT"
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

    # 1. Farmer attempting to authorize buyer payment -> 403
    r_fail1 = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=auth_headers,
        json={"to_status": "PAYMENT_CONFIRMED"},
    )
    assert r_fail1.status_code == 403

    # 2. Buyer authorizes sandbox payment -> 200
    r_pay = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=buyer_auth_headers,
        json={"to_status": "PAYMENT_CONFIRMED", "reason": "Simulated sandbox payment authorized."},
    )
    assert r_pay.status_code == 200
    assert r_pay.json()["data"]["status"] == "PAYMENT_CONFIRMED"
    assert r_pay.json()["data"]["next_action"]["action_type"] == "PREPARE_DISPATCH"

    # 3. Seller marks ready for dispatch -> 200
    r_ready = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=auth_headers,
        json={"to_status": "READY_FOR_DISPATCH", "reason": "Produce packed and ready."},
    )
    assert r_ready.status_code == 200
    assert r_ready.json()["data"]["status"] == "READY_FOR_DISPATCH"

    # 4. Seller marks dispatched / in transit -> 200
    r_transit = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=auth_headers,
        json={"to_status": "IN_TRANSIT", "reason": "Dispatched towards buyer facility."},
    )
    assert r_transit.status_code == 200
    assert r_transit.json()["data"]["status"] == "IN_TRANSIT"

    # 5. Buyer confirms delivery arrival -> 200
    r_deliv = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=buyer_auth_headers,
        json={"to_status": "DELIVERED", "reason": "Shipment arrived at destination."},
    )
    assert r_deliv.status_code == 200
    assert r_deliv.json()["data"]["status"] == "DELIVERED"

    # 6. Buyer finalizes acceptance & completion -> 200
    r_comp = client.post(
        f"/api/v1/trades/{txn_id}/transition",
        headers=buyer_auth_headers,
        json={"to_status": "COMPLETED", "reason": "Accepted quality and quantity."},
    )
    assert r_comp.status_code == 200
    assert r_comp.json()["data"]["status"] == "COMPLETED"
    assert r_comp.json()["data"]["next_action"]["action_required"] is False


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
