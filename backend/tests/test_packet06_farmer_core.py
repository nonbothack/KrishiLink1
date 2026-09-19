"""Persisted API contract checks for the Packet 06 farmer journey."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.security import hash_password
from app.models import Crop, Notification, Offer, Transaction, User


def _crop(db_session, *, units=("quintal", "kg")):
    crop = Crop(
        id=uuid.uuid4(),
        name=f"Packet 06 crop {uuid.uuid4().hex[:8]}",
        category="test",
        unit="quintal",
        valid_units=list(units),
        is_active=True,
        is_tradable=True,
    )
    db_session.add(crop)
    db_session.commit()
    return crop


def _other_farmer_headers(client, db_session):
    email = f"packet06-{uuid.uuid4().hex[:8]}@example.test"
    db_session.add(
        User(
            id=uuid.uuid4(),
            email=email,
            phone=f"9{uuid.uuid4().int % 10**9:09d}",
            full_name="Other Farmer",
            password_hash=hash_password("test-password-06"),
            role="farmer",
            is_active=True,
            is_verified=True,
        )
    )
    db_session.commit()
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "test-password-06"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _create_lot(client, headers, crop, *, quantity="500", unit="kg", key=None):
    request_headers = dict(headers)
    if key:
        request_headers["Idempotency-Key"] = key
    return client.post(
        "/api/v1/lots",
        headers=request_headers,
        json={
            "crop": str(crop.id),
            "quantity": quantity,
            "unit": unit,
            "asking_price": "2450.00",
            "location_text": "Nashik District",
            "district": "Nashik",
        },
    )


def _create_offer(client, buyer_headers, lot_id, *, quantity="5", price="2520.00", key=None):
    request_headers = dict(buyer_headers)
    if key:
        request_headers["Idempotency-Key"] = key
    return client.post(
        "/api/v1/offers",
        headers=request_headers,
        json={"lot_id": lot_id, "quantity": quantity, "price_per_unit": price, "unit": "quintal"},
    )


def test_farmer_lot_units_are_normalized_and_idempotent(client, auth_headers, db_session):
    crop = _crop(db_session)
    headers = {**auth_headers, "Idempotency-Key": f"packet06-lot-{uuid.uuid4()}"}
    before = client.get("/api/v1/lots/mine", headers=auth_headers).json()["data"]["total"]

    first = _create_lot(client, headers, crop)
    second = _create_lot(client, headers, crop)

    assert first.status_code == second.status_code == 201
    assert first.json()["data"]["id"] == second.json()["data"]["id"]
    assert first.json()["data"]["quantity"] == "5.00"
    assert first.json()["data"]["unit"] == "quintal"
    mine = client.get("/api/v1/lots/mine", headers=auth_headers).json()["data"]
    persisted = next(item for item in mine["items"] if item["id"] == first.json()["data"]["id"])
    assert Decimal(persisted["original_quantity"]) == Decimal("500")
    assert persisted["original_unit"] == "kg"
    assert mine["total"] == before + 1

    unsupported = _create_lot(client, auth_headers, crop, quantity="1", unit="bag")
    too_precise = _create_lot(client, auth_headers, crop, quantity="1.234", unit="kg")
    assert unsupported.status_code == 422
    assert too_precise.status_code == 422


def test_farmer_lot_and_offer_actions_are_owner_scoped(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session)
    lot = _create_lot(client, auth_headers, crop).json()["data"]
    offer = _create_offer(client, buyer_auth_headers, lot["id"]).json()["data"]
    other_farmer = _other_farmer_headers(client, db_session)

    assert client.get(f"/api/v1/lots/{lot['id']}", headers=other_farmer).status_code == 404
    assert client.patch(
        f"/api/v1/lots/{lot['id']}", headers=other_farmer, json={"asking_price": "2600.00"}
    ).status_code == 404
    assert client.post(f"/api/v1/offers/{offer['id']}/accept", headers=other_farmer).status_code == 403
    assert client.post(f"/api/v1/offers/{offer['id']}/counter", headers=buyer_auth_headers, json={"price_per_unit": "2600.00"}).status_code == 403
    assert client.post(f"/api/v1/offers/{offer['id']}/reject", headers=buyer_auth_headers).status_code == 403


def test_counter_keeps_parent_terms_and_accept_creates_one_trade(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session)
    lot = _create_lot(client, auth_headers, crop).json()["data"]
    offer = _create_offer(client, buyer_auth_headers, lot["id"], quantity="5", price="2520.00").json()["data"]
    parent_before = db_session.get(Offer, uuid.UUID(offer["id"]))
    assert parent_before.quantity == Decimal("5")
    assert parent_before.price_per_unit == Decimal("2520.00")

    counter = client.post(
        f"/api/v1/offers/{offer['id']}/counter",
        headers={**auth_headers, "Idempotency-Key": f"packet06-counter-{uuid.uuid4()}"},
        json={"quantity": "4", "price_per_unit": "2600.00"},
    )
    assert counter.status_code == 200
    db_session.refresh(parent_before)
    assert parent_before.status == "COUNTERED"
    assert parent_before.quantity == Decimal("5")
    assert parent_before.price_per_unit == Decimal("2520.00")

    counter_id = counter.json()["data"]["id"]
    history = client.get(f"/api/v1/offers/{counter_id}/history", headers=auth_headers)
    assert history.status_code == 200
    assert any(item["id"] == counter_id for item in history.json()["data"])

    accept_key = f"packet06-accept-{uuid.uuid4()}"
    accepted = client.post(f"/api/v1/offers/{counter_id}/accept", headers={**auth_headers, "Idempotency-Key": accept_key})
    accepted_retry = client.post(f"/api/v1/offers/{counter_id}/accept", headers={**auth_headers, "Idempotency-Key": accept_key})
    assert accepted.status_code == accepted_retry.status_code == 200
    transaction_id = accepted.json()["data"]["transaction_id"]
    assert accepted_retry.json()["data"]["transaction_id"] == transaction_id
    assert db_session.query(Transaction).filter(Transaction.offer_id == uuid.UUID(counter_id)).count() == 1

    farmer_trades = client.get("/api/v1/transactions", headers=auth_headers).json()["data"]["items"]
    trade = next(item for item in farmer_trades if item["id"] == transaction_id)
    assert trade["gross_value"] == 10400
    room = client.get(f"/api/v1/trades/{transaction_id}/room", headers=auth_headers)
    assert room.status_code == 200
    assert room.json()["data"]["terms"]["quantity"] == 4
    assert room.json()["data"]["terms"]["price_per_unit"] == 2600

    notices = client.get("/api/v1/notifications", headers=auth_headers).json()["data"]["items"]
    created = next(item for item in notices if item["type"] == "trade_created" and item["related_id"] == transaction_id)
    assert created
    unrelated = _other_farmer_headers(client, db_session)
    assert client.get(f"/api/v1/trades/{transaction_id}/room", headers=unrelated).status_code in (403, 404)
    assert client.post(f"/api/v1/notifications/{created['id']}/read", headers=unrelated).status_code == 404


def test_expired_or_declined_offer_cannot_be_accepted(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session)
    lot = _create_lot(client, auth_headers, crop).json()["data"]
    expired_offer = _create_offer(client, buyer_auth_headers, lot["id"]).json()["data"]
    row = db_session.get(Offer, uuid.UUID(expired_offer["id"]))
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()
    response = client.post(f"/api/v1/offers/{expired_offer['id']}/accept", headers=auth_headers)
    assert response.status_code == 409
    db_session.refresh(row)
    assert row.status == "EXPIRED"

    declined = _create_offer(client, buyer_auth_headers, lot["id"], key=f"packet06-decline-source-{uuid.uuid4()}").json()["data"]
    assert client.post(f"/api/v1/offers/{declined['id']}/reject", headers=auth_headers, json={"reason": "price too low"}).status_code == 200
    assert client.post(f"/api/v1/offers/{declined['id']}/accept", headers=auth_headers).status_code == 409


def test_withdrawal_retains_history_and_closes_pending_offers(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session)
    lot = _create_lot(client, auth_headers, crop).json()["data"]
    offer = _create_offer(client, buyer_auth_headers, lot["id"]).json()["data"]

    withdrawn = client.post(f"/api/v1/lots/{lot['id']}/withdraw", headers=auth_headers)

    assert withdrawn.status_code == 200
    assert withdrawn.json()["data"]["status"] == "CANCELLED"
    assert client.get(f"/api/v1/lots/{lot['id']}", headers=auth_headers).json()["data"]["status"] == "CANCELLED"
    db_session.expire_all()
    assert db_session.get(Offer, uuid.UUID(offer["id"])).status == "CANCELLED"
    assert db_session.query(Notification).filter_by(user_id=uuid.UUID(client.get("/api/v1/auth/me", headers=buyer_auth_headers).json()["data"]["id"]), type="lot_withdrawn").count() >= 1
