import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import settings
from app.core.security import decode_token
from app.main import app
from app.models import (
    AuditLog,
    AuthSession,
    BuyerProfile,
    ConsentRecord,
    FPOProfile,
    OtpChallenge,
    OutboxEvent,
    User,
    VerificationRecord,
)
from app.modules.auth import otp_service
from app.modules.auth.identity import CURRENT_POLICIES, canonicalize_indian_mobile, phone_hash
from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import register_user


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_indian_phone_canonicalization_and_strict_country_support():
    assert canonicalize_indian_mobile("098765 43210") == ("+919876543210", "9876543210")
    assert canonicalize_indian_mobile("+91 (98765) 43210") == ("+919876543210", "9876543210")
    with pytest.raises(ValueError):
        canonicalize_indian_mobile("+1 415 555 0100")
    with pytest.raises(ValueError):
        canonicalize_indian_mobile("12345")


def test_self_registration_rejects_privileged_roles_and_gps_without_consent():
    with pytest.raises(ValidationError):
        RegisterRequest(full_name="Admin User", email="admin@example.test", role="admin")
    with pytest.raises(ValidationError):
        RegisterRequest(
            full_name="Farmer User",
            email="farmer@example.test",
            latitude=19.0,
            longitude=73.0,
        )


def test_otp_is_hashed_single_use_and_returns_short_lived_registration_ticket(
    client, monkeypatch, db_session
):
    monkeypatch.setattr(settings, "otp_development_code_exposure_enabled", True)
    monkeypatch.setattr(otp_service, "get_redis", lambda: None)
    phone = f"+91987{uuid.uuid4().int % 10_000_000:07d}"
    requested = client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert requested.status_code == 200
    response = requested.json()["data"]
    code = response["development_code"]
    challenge = db_session.query(OtpChallenge).filter_by(phone_hash=phone_hash(phone)).one()
    assert code not in challenge.code_hash
    assert challenge.code_hash
    assert challenge.phone_hash == phone_hash(phone)
    assert not hasattr(challenge, "phone_e164")
    cooldown = client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert cooldown.status_code == 200
    assert "development_code" not in cooldown.json()["data"]
    assert cooldown.json()["data"]["resend_after_seconds"] > 0

    verified = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})
    assert verified.status_code == 200
    ticket = verified.json()["data"]["registration_ticket"]
    ticket_payload = decode_token(ticket)
    assert ticket_payload["type"] == "registration_ticket"
    assert ticket_payload["phone"] == phone
    assert "access_token" not in verified.json()["data"]
    db_session.expire_all()
    assert db_session.query(OtpChallenge).filter_by(phone_hash=phone_hash(phone)).one().consumed_at

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "New Farmer",
            "phone": f"+91 {phone[3:]}",
            "role": "farmer",
            "verification_ticket": ticket,
            "policy_versions": {
                key: value["version"] for key, value in verified.json()["data"]["policy_versions"].items()
            },
        },
    )
    assert registration.status_code == 201
    assert registration.json()["data"]["user"]["email"] is None
    assert registration.json()["data"]["user"]["phone_verified_at"]
    assert "is_verified" not in registration.json()["data"]["user"]
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Duplicate Farmer",
            "phone": f"0{phone[3:]}",
            "role": "farmer",
            "verification_ticket": ticket,
        },
    )
    assert duplicate.status_code == 409

    replay = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})
    assert replay.status_code == 401
    otp_audits = db_session.query(AuditLog).filter(AuditLog.action.like("auth.otp_%")).all()
    assert all(code not in str(audit.after) and phone not in str(audit.after) for audit in otp_audits)
    assert db_session.query(OutboxEvent).filter(OutboxEvent.event_type.like("auth.otp_%")).count() == 0

    expired_phone = f"+91989{uuid.uuid4().int % 10_000_000:07d}"
    expired_request = client.post("/api/v1/auth/otp/request", json={"phone": expired_phone})
    expired_code = expired_request.json()["data"]["development_code"]
    expired_challenge = db_session.query(OtpChallenge).filter_by(phone_hash=phone_hash(expired_phone)).one()
    expired_challenge.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    assert client.post(
        "/api/v1/auth/otp/verify", json={"phone": expired_phone, "code": expired_code}
    ).status_code == 401
    db_session.refresh(expired_challenge)
    assert expired_challenge.revoked_at

    replace_phone = f"+91990{uuid.uuid4().int % 10_000_000:07d}"
    first_challenge_response = client.post("/api/v1/auth/otp/request", json={"phone": replace_phone})
    first_challenge = db_session.query(OtpChallenge).filter_by(phone_hash=phone_hash(replace_phone)).one()
    first_challenge.created_at = datetime.now(timezone.utc) - timedelta(seconds=60)
    db_session.commit()
    replacement = client.post("/api/v1/auth/otp/request", json={"phone": replace_phone})
    assert replacement.status_code == 200
    db_session.refresh(first_challenge)
    assert first_challenge.revoked_at
    assert first_challenge_response.status_code == 200

    hourly_phone = f"+91991{uuid.uuid4().int % 10_000_000:07d}"
    for _ in range(5):
        accepted = client.post("/api/v1/auth/otp/request", json={"phone": hourly_phone})
        assert accepted.status_code == 200
        active = (
            db_session.query(OtpChallenge)
            .filter_by(phone_hash=phone_hash(hourly_phone))
            .order_by(OtpChallenge.created_at.desc())
            .first()
        )
        active.created_at = datetime.now(timezone.utc) - timedelta(seconds=60)
        db_session.commit()
    over_limit = client.post("/api/v1/auth/otp/request", json={"phone": hourly_phone})
    assert over_limit.status_code == 429

    limited_phone = f"+91988{uuid.uuid4().int % 10_000_000:07d}"
    limited_request = client.post("/api/v1/auth/otp/request", json={"phone": limited_phone})
    limited_code = limited_request.json()["data"]["development_code"]
    wrong_code = ("0" if limited_code[0] != "0" else "1") + limited_code[1:]
    for _ in range(3):
        invalid = client.post(
            "/api/v1/auth/otp/verify", json={"phone": limited_phone, "code": wrong_code}
        )
        assert invalid.status_code == 401
    exhausted = db_session.query(OtpChallenge).filter_by(phone_hash=phone_hash(limited_phone)).one()
    assert exhausted.attempt_count == 3 and exhausted.revoked_at
    assert client.post(
        "/api/v1/auth/otp/verify", json={"phone": limited_phone, "code": limited_code}
    ).status_code == 401


def test_password_refresh_replay_revokes_the_rotated_session_family(client, ensure_test_users, db_session):
    login = client.post(
        "/api/v1/auth/login", json={"email": "ramesh@demo.com", "password": "demo123!"}
    )
    old_refresh = login.json()["data"]["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    new_access = rotated.json()["data"]["access_token"]
    old_payload = decode_token(old_refresh)

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401
    assert db_session.get(AuthSession, old_payload["sid"]).revoked_at
    assert client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"}
    ).status_code == 401


def test_production_otp_and_registration_fail_closed_without_real_provider_or_approved_policy(
    monkeypatch, db_session
):
    monkeypatch.setattr(settings, "env", "production")
    monkeypatch.setattr(settings, "otp_development_code_exposure_enabled", True)
    monkeypatch.setattr(otp_service, "get_redis", lambda: type("Redis", (), {"eval": lambda *_args: 1})())
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/otp/request",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
            "state": {},
        }
    )
    phone = f"+91976{uuid.uuid4().int % 10_000_000:07d}"
    with pytest.raises(HTTPException) as unavailable:
        otp_service.request_otp(db_session, phone, request)
    assert unavailable.value.status_code == 503
    assert db_session.query(OtpChallenge).filter_by(phone_hash=phone_hash(phone)).count() == 0

    data = RegisterRequest(
        full_name="New Farmer",
        email="new-farmer@example.com",
        phone="9876543210",
        verification_ticket="not-a-real-ticket",
    )
    with pytest.raises(HTTPException) as policy_pending:
        register_user(db_session, data, request)
    assert policy_pending.value.status_code == 503


def test_registration_records_separate_consents_and_withdraws_optional_marketing(client, db_session):
    policy_versions = {key: value["version"] for key, value in CURRENT_POLICIES.items()}
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Buyer Organization",
            "email": f"buyer-{uuid.uuid4().hex[:12]}@example.com",
            "password": "Password1234!",
            "role": "buyer",
            "business_name": "Local Produce Buyer",
            "policy_versions": policy_versions,
            "marketing_consent": True,
            "latitude": 19.0,
            "longitude": 73.0,
            "coordinate_accuracy_m": 35,
            "location_consent": True,
        },
    )
    assert registration.status_code == 201, registration.text
    data = registration.json()["data"]
    assert "is_verified" not in data["user"]
    user_id = data["user"]["id"]
    authorization = {"Authorization": f"Bearer {data['access_token']}"}
    records = db_session.query(ConsentRecord).filter_by(user_id=uuid.UUID(user_id)).all()
    assert {record.policy_type for record in records} == {
        "terms",
        "privacy_notice",
        "marketing",
        "location_gps",
    }
    assert len({record.policy_version for record in records}) == 3

    consent_history = client.get("/api/v1/privacy/consents", headers=authorization)
    assert consent_history.json()["data"]["marketing_enabled"] is True
    withdrawn = client.post("/api/v1/privacy/consents/marketing/withdraw", headers=authorization)
    assert withdrawn.status_code == 200
    db_session.expire_all()
    refreshed_history = client.get("/api/v1/privacy/consents", headers=authorization)
    assert refreshed_history.json()["data"]["marketing_enabled"] is False
    marketing_record = next(record for record in records if record.policy_type == "marketing")
    assert marketing_record.accepted_at
    assert marketing_record.withdrawn_at

    verifications = client.get("/api/v1/users/me/verifications", headers=authorization)
    business = next(item for item in verifications.json()["data"]["items"] if item["dimension"] == "business")
    assert business["status"] == "UNVERIFIED"


def test_fpo_onboarding_creates_an_unverified_organization_profile(client, db_session):
    email = f"fpo-{uuid.uuid4().hex[:12]}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "FPO Representative",
            "email": email,
            "role": "fpo",
            "organization_name": "Sahyadri Farmer Collective",
        },
    )
    assert registration.status_code == 201
    user_id = uuid.UUID(registration.json()["data"]["user"]["id"])
    profile = db_session.query(FPOProfile).filter_by(user_id=user_id).one()
    assert profile.organization_name == "Sahyadri Farmer Collective"
    assert profile.organization_verification_status == "UNVERIFIED"
    org_evidence = (
        db_session.query(VerificationRecord)
        .filter_by(user_id=user_id, dimension="organization")
        .one()
    )
    assert org_evidence.status == "UNVERIFIED"


def test_privacy_requests_are_owner_scoped_and_gps_requires_explicit_consent(client, auth_headers, buyer_auth_headers):
    created = client.post(
        "/api/v1/privacy/requests", headers=auth_headers, json={"request_type": "access"}
    )
    assert created.status_code == 201
    own = client.get("/api/v1/privacy/requests", headers=auth_headers)
    other = client.get("/api/v1/privacy/requests", headers=buyer_auth_headers)
    assert created.json()["data"]["id"] in {item["id"] for item in own.json()["data"]["items"]}
    assert other.json()["data"]["items"] == []

    denied = client.put(
        "/api/v1/users/me/location",
        headers=auth_headers,
        json={"latitude": 19.0, "longitude": 73.0, "consent": False},
    )
    assert denied.status_code == 422
    assert "input" not in denied.json()["details"][0]
    saved = client.put(
        "/api/v1/users/me/location",
        headers=auth_headers,
        json={"latitude": 19.0, "longitude": 73.0, "accuracy_m": 25, "consent": True},
    )
    assert saved.status_code == 200
    active_location_consents = [
        item
        for item in client.get("/api/v1/privacy/consents", headers=auth_headers).json()["data"]["items"]
        if item["policy_type"] == "location_gps" and item["withdrawn_at"] is None
    ]
    assert len(active_location_consents) == 1
    profile = client.get("/api/v1/users/me", headers=auth_headers).json()["data"]
    assert "latitude" not in profile and "longitude" not in profile
    assert client.delete("/api/v1/users/me/location", headers=auth_headers).status_code == 200
    location_history = [
        item
        for item in client.get("/api/v1/privacy/consents", headers=auth_headers).json()["data"]["items"]
        if item["policy_type"] == "location_gps"
    ]
    assert location_history and all(item["withdrawn_at"] for item in location_history)


def test_admin_verification_requires_a_dimension_and_evidence_reference(
    client, admin_auth_headers, auth_headers, db_session
):
    buyer = db_session.query(User).filter_by(email="buyer@demo.com").one()
    profile = BuyerProfile(user_id=buyer.id, business_name="Demo Produce Buyer")
    db_session.add(profile)
    db_session.commit()
    legacy_state = buyer.is_verified
    buyer_listing = client.get("/api/v1/users/buyers").json()["data"]
    assert legacy_state is True
    assert not any(item["business_name"] == "Demo Produce Buyer" for item in buyer_listing)

    generic = client.post(
        f"/api/v1/admin/users/{buyer.id}/verify", headers=admin_auth_headers
    )
    assert generic.status_code == 409
    db_session.refresh(buyer)
    assert buyer.is_verified is legacy_state

    missing_reference = client.post(
        f"/api/v1/admin/users/{buyer.id}/verifications/business",
        headers=admin_auth_headers,
        json={"status": "VERIFIED", "method": "manual_document_review"},
    )
    assert missing_reference.status_code == 422
    assert "input" not in missing_reference.json()["details"][0]

    reviewed = client.post(
        f"/api/v1/admin/users/{buyer.id}/verifications/business",
        headers=admin_auth_headers,
        json={
            "status": "VERIFIED",
            "method": "manual_document_review",
            "provider_reference": "review-case-2026-001",
        },
    )
    assert reviewed.status_code == 200
    db_session.refresh(profile)
    assert profile.business_verification_status == "VERIFIED"
    db_session.refresh(buyer)
    assert buyer.is_verified is legacy_state
    buyer_listing = client.get("/api/v1/users/buyers").json()["data"]
    reviewed_buyer = next(item for item in buyer_listing if item["business_name"] == "Demo Produce Buyer")
    assert reviewed_buyer["business_verification"] == "verified"
    assert "id" not in reviewed_buyer

    denied = client.post(
        f"/api/v1/admin/users/{buyer.id}/verifications/business",
        headers=auth_headers,
        json={
            "status": "VERIFIED",
            "method": "manual_document_review",
            "provider_reference": "review-case-2026-002",
        },
    )
    assert denied.status_code == 403
