import uuid

from app.core.config import settings


def test_storage_does_not_expose_generic_bucket_or_presign_routes(client):
    assert client.get("/api/v1/storage/buckets").status_code == 404
    assert client.post("/api/v1/storage/presigned-url?key=private/object").status_code == 404


def test_sms_test_endpoint_is_hidden_outside_development(client, admin_auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "env", "production")
    response = client.post(
        "/api/v1/notifications/test-sms",
        json={"phone": "9820019061", "message": "test"},
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_buyer_list_does_not_claim_unpersisted_offer_or_distance(client):
    response = client.get("/api/v1/users/buyers")
    assert response.status_code == 200
    for buyer in response.json()["data"]:
        assert buyer["offer_price"] is None
        assert buyer["distance_km"] is None


def test_registration_does_not_convert_district_into_exact_coordinates(client, db_session):
    from app.models import User

    email = f"geo-{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Location Test",
            "role": "farmer",
            "district": "Nashik",
        },
    )
    assert response.status_code == 201
    user = db_session.query(User).filter(User.email == email).one()
    assert user.location_geog is None


def test_reservations_are_scoped_by_role(client, db_session, auth_headers, buyer_auth_headers, fpo_auth_headers, admin_auth_headers):
    lot = client.post(
        "/api/v1/lots",
        json={"crop": "Wheat", "grade": "A", "quantity": 10, "asking_price": 2200, "location_text": "Farm"},
        headers=auth_headers,
    ).json()["data"]["id"]
    offer = client.post(
        "/api/v1/offers", json={"lot_id": lot, "quantity": 5, "price_per_unit": 2200}, headers=buyer_auth_headers
    ).json()["data"]["id"]
    reservation_id = client.post(f"/api/v1/offers/{offer}/accept", headers=auth_headers).json()["data"][
        "reservation_id"
    ]

    farmer_items = client.get("/api/v1/reservations", headers=auth_headers).json()["data"]["items"]
    buyer_items = client.get("/api/v1/reservations", headers=buyer_auth_headers).json()["data"]["items"]
    fpo_items = client.get("/api/v1/reservations", headers=fpo_auth_headers).json()["data"]["items"]
    admin_items = client.get("/api/v1/reservations", headers=admin_auth_headers).json()["data"]["items"]
    assert reservation_id in {row["id"] for row in farmer_items}
    assert reservation_id in {row["id"] for row in buyer_items}
    assert reservation_id not in {row["id"] for row in fpo_items}
    assert reservation_id in {row["id"] for row in admin_items}

    from app.core.security import create_access_token
    from app.models import User

    operator_user = User(
        id=uuid.uuid4(),
        email=f"operator-{uuid.uuid4().hex}@example.com",
        full_name="Operator",
        role="operator",
        state="Maharashtra",
        is_active=True,
    )
    db_session.add(operator_user)
    db_session.commit()
    operator = {"Authorization": f"Bearer {create_access_token(str(operator_user.id), 'operator')}"}
    assert client.get("/api/v1/reservations", headers=operator).status_code == 403
