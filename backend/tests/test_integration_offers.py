import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def _get_auth_headers(client, email, password):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        pytest.skip(f"Cannot authenticate {email}")
    return {"Authorization": f"Bearer {r.json()['data']['access_token']}"}

def _create_test_lot(client, farmer_h, crop="Wheat", quantity=100.0):
    r = client.post("/api/v1/lots", json={
        "crop": crop, "grade": "A", "quantity": quantity,
        "asking_price": 2200.0, "location_text": "Nashik Market", "district": "Nashik"
    }, headers=farmer_h)
    if r.status_code == 201:
        return r.json()["data"]["id"]
    r_list = client.get("/api/v1/lots", headers=farmer_h)
    items = r_list.json()["data"]["items"]
    return items[0]["id"]

def test_create_offer(client):
    farmer_h = _get_auth_headers(client, "ramesh@demo.com", "demo123!")
    buyer_h = _get_auth_headers(client, "mehta@demo.com", "demo123!")
    lot_id = _create_test_lot(client, farmer_h, "Wheat", 100.0)
    r2 = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 10.0, "price_per_unit": 2000.0
    }, headers=buyer_h)
    assert r2.status_code == 201
    assert r2.json()["success"] == True
    assert r2.json()["data"]["status"] == "PENDING"

def test_create_offer_unauthorized(client):
    r = client.post("/api/v1/offers", json={
        "lot_id": str(uuid.uuid4()), "quantity": 10.0, "price_per_unit": 2000.0
    })
    assert r.status_code == 401

def test_list_offers(client):
    h = _get_auth_headers(client, "mehta@demo.com", "demo123!")
    r = client.get("/api/v1/offers", headers=h)
    assert r.status_code == 200
    assert r.json()["success"] == True

def test_counter_offer(client):
    farmer_h = _get_auth_headers(client, "ramesh@demo.com", "demo123!")
    buyer_h = _get_auth_headers(client, "mehta@demo.com", "demo123!")
    lot_id = _create_test_lot(client, farmer_h, "Wheat", 100.0)
    r2 = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 10.0, "price_per_unit": 2000.0
    }, headers=buyer_h)
    assert r2.status_code == 201
    offer_id = r2.json()["data"]["id"]
    # Farmer counters
    r3 = client.post(f"/api/v1/offers/{offer_id}/counter", json={
        "quantity": 15.0, "price_per_unit": 2100.0
    }, headers=farmer_h)
    assert r3.status_code == 200
    assert r3.json()["success"] == True

def test_accept_offer(client):
    farmer_h = _get_auth_headers(client, "ramesh@demo.com", "demo123!")
    buyer_h = _get_auth_headers(client, "mehta@demo.com", "demo123!")
    lot_id = _create_test_lot(client, farmer_h, "Wheat", 100.0)
    r2 = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 10.0, "price_per_unit": 2000.0
    }, headers=buyer_h)
    assert r2.status_code == 201
    offer_id = r2.json()["data"]["id"]
    # Farmer accepts
    r3 = client.post(f"/api/v1/offers/{offer_id}/accept", headers=farmer_h)
    assert r3.status_code == 200
    assert r3.json()["success"] == True
    assert r3.json()["data"]["status"] == "ACCEPTED"

def test_reject_offer(client):
    farmer_h = _get_auth_headers(client, "ramesh@demo.com", "demo123!")
    buyer_h = _get_auth_headers(client, "mehta@demo.com", "demo123!")
    lot_id = _create_test_lot(client, farmer_h, "Wheat", 100.0)
    r2 = client.post("/api/v1/offers", json={
        "lot_id": lot_id, "quantity": 10.0, "price_per_unit": 2000.0
    }, headers=buyer_h)
    assert r2.status_code == 201
    offer_id = r2.json()["data"]["id"]
    # Farmer rejects
    r3 = client.post(f"/api/v1/offers/{offer_id}/reject", headers=farmer_h)
    assert r3.status_code == 200
    assert r3.json()["success"] == True
    assert r3.json()["data"]["status"] == "REJECTED"
