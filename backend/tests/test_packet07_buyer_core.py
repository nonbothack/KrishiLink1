"""Packet 07 buyer ownership, privacy and procurement-quantity contracts."""

import uuid
from decimal import Decimal

from app.core.security import hash_password
from app.models import BuyerRequirement, Crop, Offer, User


def _crop(db):
    row = Crop(id=uuid.uuid4(), name=f"Buyer crop {uuid.uuid4().hex[:8]}", category="test", unit="quintal", valid_units=["quintal", "kg"], is_active=True, is_tradable=True)
    db.add(row); db.commit(); return row


def _lot(client, headers, crop, quantity="10"):
    result = client.post("/api/v1/lots", headers=headers, json={"crop": str(crop.id), "quantity": quantity, "unit": "quintal", "asking_price": "2500", "location_text": "Nashik District", "district": "Nashik"})
    assert result.status_code == 201, result.text
    return result.json()["data"]


def _second_buyer(client, db):
    email = f"buyer-07-{uuid.uuid4().hex[:8]}@example.test"
    db.add(User(id=uuid.uuid4(), email=email, phone=f"8{uuid.uuid4().int % 10**9:09d}", full_name="Other Buyer", password_hash=hash_password("packet07-password"), role="buyer", is_active=True))
    db.commit()
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "packet07-password"})
    return {"Authorization": f"Bearer {login.json()['data']['access_token']}"}


def _requirement(client, headers, crop, quantity="8"):
    response = client.post("/api/v1/requirements", headers=headers, json={"crop_id": str(crop.id), "quantity": quantity, "unit": "quintal", "location_text": "Nashik", "status": "ACTIVE"})
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_requirements_are_owner_scoped_and_discovery_minimizes_farmer_data(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); lot = _lot(client, auth_headers, crop); requirement = _requirement(client, buyer_auth_headers, crop)
    other = _second_buyer(client, db_session)
    assert client.get("/api/v1/requirements", headers=other).json()["data"]["total"] == 0
    assert client.post(f"/api/v1/requirements/{requirement['id']}/close", headers=other).status_code == 404
    discovery = client.get(f"/api/v1/requirements/discover/lots?requirement_id={requirement['id']}", headers=buyer_auth_headers)
    assert discovery.status_code == 200
    item = next(row for row in discovery.json()["data"]["items"] if row["id"] == lot["id"])
    assert item["seller_label"] == "Farmer listing"
    for private in ("phone", "email", "owner_id", "latitude", "longitude", "full_name"):
        assert private not in item


def test_requirement_commitment_is_server_authoritative_and_cannot_overfill(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); lot = _lot(client, auth_headers, crop, "10"); requirement = _requirement(client, buyer_auth_headers, crop, "8")
    created = client.post("/api/v1/offers", headers={**buyer_auth_headers, "Idempotency-Key": str(uuid.uuid4())}, json={"lot_id": lot["id"], "quantity": "8", "unit": "quintal", "price_per_unit": "2500", "buyer_requirement_id": requirement["id"]})
    assert created.status_code == 201, created.text
    offer_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/offers/{offer_id}/accept", headers=auth_headers).status_code == 200
    db_session.expire_all(); row = db_session.get(BuyerRequirement, uuid.UUID(requirement["id"]))
    assert row.committed_quantity == Decimal("8") and row.status == "FILLED"
    second = client.post("/api/v1/offers", headers=buyer_auth_headers, json={"lot_id": lot["id"], "quantity": "1", "unit": "quintal", "price_per_unit": "2500", "buyer_requirement_id": requirement["id"]})
    assert second.status_code == 409
    assert db_session.query(Offer).filter(Offer.buyer_requirement_id == row.id, Offer.status == "ACCEPTED").count() == 1


def test_counter_recipient_can_accept_but_foreign_buyer_cannot(client, auth_headers, buyer_auth_headers, db_session):
    crop = _crop(db_session); lot = _lot(client, auth_headers, crop); original = client.post("/api/v1/offers", headers=buyer_auth_headers, json={"lot_id": lot["id"], "quantity": "2", "unit": "quintal", "price_per_unit": "2400"}).json()["data"]
    counter = client.post(f"/api/v1/offers/{original['id']}/counter", headers=auth_headers, json={"price_per_unit": "2500"}).json()["data"]
    other = _second_buyer(client, db_session)
    assert client.post(f"/api/v1/offers/{counter['id']}/accept", headers=other).status_code == 403
    assert client.post(f"/api/v1/offers/{counter['id']}/accept", headers=buyer_auth_headers).status_code == 200
