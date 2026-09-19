import pytest
from fastapi.testclient import TestClient
import uuid

from app.models import Crop


def _unpriced_crop(db_session):
    crop = Crop(
        id=uuid.uuid4(), name=f"Lot earnings crop {uuid.uuid4().hex[:8]}",
        category="test", unit="quintal", valid_units=["quintal"],
    )
    db_session.add(crop)
    db_session.commit()
    return str(crop.id)

def test_create_lot(client, auth_headers):
    r = client.post("/api/v1/lots", json={
        "crop": "Wheat", "grade": "A", "quantity": 100.0,
        "location_text": "Nashik Market", "district": "Nashik"
    }, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["public_id"].startswith("KL-LOT-")
    assert data["crop"] == "Wheat"
    assert data["grade"] == "A"

def test_list_lots(client):
    r = client.get("/api/v1/lots")
    assert r.status_code == 200
    assert r.json()["success"] == True
    assert "items" in r.json()["data"]

def test_get_lot(client, auth_headers):
    r = client.get("/api/v1/lots", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    if items:
        lot_id = items[0]["id"]
        r2 = client.get(f"/api/v1/lots/{lot_id}", headers=auth_headers)
        assert r2.status_code == 200
        assert r2.json()["success"] == True
        buyer_login = client.post("/api/v1/auth/login", json={"email": "buyer@demo.com", "password": "demo123!"})
        buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['data']['access_token']}"}
        assert client.get(f"/api/v1/lots/{lot_id}", headers=buyer_headers).status_code == 404

def test_public_lot(client):
    r = client.get("/api/v1/lots")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    if items:
        public_id = items[0]["public_id"]
        r2 = client.get(f"/api/v1/lots/public/{public_id}")
        assert r2.status_code == 200
        assert r2.json()["success"] == True
        assert r2.json()["data"]["public_id"] == public_id

def test_create_lot_unauthorized(client):
    r = client.post("/api/v1/lots", json={
        "crop": "Wheat", "grade": "A", "quantity": 100.0,
        "location_text": "Test", "district": "Test"
    })
    assert r.status_code == 401

def test_create_lot_duplicate_idempotency(client, auth_headers):
    headers = {**auth_headers, "Idempotency-Key": "dup-test-key-001"}
    r = client.post("/api/v1/lots", json={
        "crop": "Wheat", "grade": "A", "quantity": 100.0,
        "location_text": "Nashik", "district": "Nashik"
    }, headers=headers)
    assert r.status_code == 201
    r2 = client.post("/api/v1/lots", json={
        "crop": "Wheat", "grade": "A", "quantity": 100.0,
        "location_text": "Nashik", "district": "Nashik"
    }, headers=headers)
    assert r2.status_code == 201
    assert r.json()["data"]["public_id"] == r2.json()["data"]["public_id"]

def test_get_lot_earnings_no_offers(client, auth_headers, db_session):
    # Create lot
    r = client.post("/api/v1/lots", json={
        "crop": _unpriced_crop(db_session), "grade": "A", "quantity": 100.0,
        "location_text": "Nashik", "district": "Nashik",
        "market_reference_price": 2800.0
    }, headers=auth_headers)
    assert r.status_code == 201
    lot_id = r.json()["data"]["id"]

    # Request earnings without offers -> 400 with message
    r2 = client.get(f"/api/v1/lots/{lot_id}/earnings", headers=auth_headers)
    assert r2.status_code == 400
    assert "No recent official comparable market price is available" in r2.json()["detail"]

def test_get_lot_earnings_with_offer(client, auth_headers, db_session):
    # Create lot with market reference price
    r = client.post("/api/v1/lots", json={
        "crop": _unpriced_crop(db_session), "grade": "A", "quantity": 50.0,
        "location_text": "Nashik", "district": "Nashik",
        "market_reference_price": 2000.0
    }, headers=auth_headers)
    assert r.status_code == 201
    lot_id = r.json()["data"]["id"]

    # Login as buyer and make offer
    buyer_login = client.post("/api/v1/auth/login", json={"email": "buyer@demo.com", "password": "demo123!"})
    assert buyer_login.status_code == 200
    buyer_headers = {"Authorization": f"Bearer {buyer_login.json()['data']['access_token']}"}

    offer_resp = client.post("/api/v1/offers", json={
        "lot_id": lot_id,
        "quantity": 50.0,
        "price_per_unit": 2400.0
    }, headers=buyer_headers)
    assert offer_resp.status_code == 201

    # Farmer requests earnings
    earnings_resp = client.get(f"/api/v1/lots/{lot_id}/earnings", headers=auth_headers)
    assert earnings_resp.status_code == 400
    assert "No recent official comparable market price is available" in earnings_resp.json()["detail"]
