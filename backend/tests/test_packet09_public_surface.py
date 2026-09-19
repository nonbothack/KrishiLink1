"""Packet 09 public discovery privacy and route contracts."""

import uuid

from app.models import BuyerProfile, DataSourceRegistry, Market, User
from app.modules.markets.router import public_market_slug


def test_public_buyer_directory_requires_business_review_and_hides_account_identity(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    verified_user = User(
        id=uuid.uuid4(), email=f"public-buyer-{suffix}@example.test", phone=f"8{uuid.uuid4().int % 10**9:09d}",
        full_name="Private Contact Name", role="buyer", location="Exact street location", district="Nashik",
        state="Maharashtra", is_active=True,
    )
    unverified_user = User(
        id=uuid.uuid4(), email=f"unverified-buyer-{suffix}@example.test", phone=f"7{uuid.uuid4().int % 10**9:09d}",
        full_name="Unverified Contact Name", role="buyer", location="Private location", district="Pune",
        state="Maharashtra", is_active=True,
    )
    db_session.add_all([verified_user, unverified_user])
    db_session.flush()
    db_session.add_all([
        BuyerProfile(
            id=uuid.uuid4(), user_id=verified_user.id, business_name="Reviewed Produce Co", business_type="trader",
            crops_interested=["Onion"], business_verification_status="VERIFIED",
        ),
        BuyerProfile(
            id=uuid.uuid4(), user_id=unverified_user.id, business_name="Unreviewed Co", business_type="processor",
            crops_interested=["Tomato"], business_verification_status="UNVERIFIED",
        ),
    ])
    db_session.commit()

    response = client.get("/api/v1/users/buyers")
    assert response.status_code == 200
    items = response.json()["data"]
    by_business = {item["business_name"]: item for item in items}
    assert "Reviewed Produce Co" in by_business
    assert "Unreviewed Co" not in by_business
    item = by_business["Reviewed Produce Co"]
    assert item["business_verification"] == "verified"
    for private_field in ("id", "user_id", "name", "full_name", "email", "phone", "location", "latitude", "longitude", "rating"):
        assert private_field not in item
    assert not any(
        private_value in str(public_item)
        for public_item in items
        for private_value in ("Private Contact Name", "Exact street location", verified_user.email, verified_user.phone)
    )


def test_public_market_slug_resolves_only_reviewed_outlet_projection(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    market = Market(
        id=uuid.uuid4(), name=f"Reviewed Yard {suffix}", district="Nashik", state="Maharashtra",
        latitude=19.1, longitude=73.1, outlet_type="apmc_principal", verification_status="verified", is_active=True,
        coordinate_source="manual_review", coordinate_confidence=0.95, source_confidence=0.95,
    )
    source = DataSourceRegistry(
        id=uuid.uuid4(), source_key=f"packet09-source-{suffix}", name="Reviewed source record",
        url="javascript:alert(1)", license_status="approved", license_name="Test license", is_active=True,
    )
    market.source_registry_id = source.id
    db_session.add_all([source, market])
    db_session.commit()

    listed = client.get("/api/v1/markets", params={"search": suffix}).json()["data"]["items"]
    assert len(listed) == 1
    slug = listed[0]["slug"]
    assert slug == public_market_slug(market)
    assert "source_ref" not in listed[0]
    assert listed[0]["source_url"] is None
    detail = client.get(f"/api/v1/markets/slug/{slug}")
    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["name"] == market.name
    assert body["source_name"] == source.name
    assert body["source_url"] is None
    assert body["verification_status"] == "verified"
    for private_field in ("verified_by", "verification_method", "source_ref", "metadata_json", "external_identifier"):
        assert private_field not in body
    assert client.get("/api/v1/markets/slug/not-an-outlet").status_code == 404


def test_public_map_cannot_enumerate_private_buyer_fpo_or_storage_layers(client):
    public = client.get("/api/v1/markets/locations?category=all")
    assert public.status_code == 200
    assert {item["type"] for item in public.json()["data"]["locations"]} <= {"mandi"}
    for layer in ("buyer", "storage", "fpo"):
        assert client.get("/api/v1/markets/locations", params={"category": layer}).status_code == 403
