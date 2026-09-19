import uuid

from app.models import OutboxEvent, User
from app.modules.admin.fraud import record_signal
from app.modules.admin.permissions import ROLE_PERMISSIONS, safe_user_projection


def test_staff_permissions_are_explicit_and_support_is_not_admin():
    assert "staff.manage" in ROLE_PERMISSIONS["admin"]
    assert "feature_flag.manage" not in ROLE_PERMISSIONS["support"]
    assert "verification.review" not in ROLE_PERMISSIONS["support"]
    assert "trade.admin_action" not in ROLE_PERMISSIONS["fraud_reviewer"]


def test_fraud_signal_is_idempotent_and_is_not_a_conviction(db_session):
    subject = uuid.uuid4()
    first = record_signal(db_session, subject_type="user", subject_id=str(subject), signal_type="PAYMENT_REFERENCE_REUSED", rule_id="payment.ref.reuse", rule_version="1", severity="MEDIUM", evidence_refs=["payment:1"])
    second = record_signal(db_session, subject_type="user", subject_id=str(subject), signal_type="PAYMENT_REFERENCE_REUSED", rule_id="payment.ref.reuse", rule_version="1", severity="MEDIUM", evidence_refs=["payment:1"])
    assert first.id == second.id
    assert first.status == "OPEN"
    assert first.decision is None


def test_support_projection_masks_contact_and_omits_sensitive_fields(db_session):
    suffix = str(uuid.uuid4().int)[-10:]
    user = User(id=uuid.uuid4(), email=f"{suffix}@example.test", phone=suffix, phone_canonical=f"+91{suffix}", full_name="Private Farmer", role="farmer")
    db_session.add(user)
    db_session.flush()
    projection = safe_user_projection(user)
    assert projection["phone_masked"].endswith(suffix[-4:])
    assert "email" not in projection
    assert "password_hash" not in projection
    assert "location_geog" not in projection


def test_buyer_cannot_open_staff_operations(client, buyer_auth_headers):
    response = client.get("/api/v1/admin/fraud/cases", headers=buyer_auth_headers)
    assert response.status_code == 403


def test_privileged_grant_is_required_for_feature_flags(client, admin_auth_headers):
    response = client.put("/api/v1/admin/feature-flags/web_push", json={"enabled": False, "reason": "maintenance"}, headers=admin_auth_headers)
    assert response.status_code == 428


def test_notification_retry_does_not_replay_completed_or_domain_event(client, db_session, admin_auth_headers):
    completed = OutboxEvent(aggregate="notification", aggregate_id=str(uuid.uuid4()), event_type="NOTIFICATION_CREATED", payload={}, status="COMPLETED")
    domain = OutboxEvent(aggregate="trade", aggregate_id=str(uuid.uuid4()), event_type="TRADE_ACCEPTED", payload={}, status="FAILED")
    db_session.add_all([completed, domain])
    db_session.commit()
    for row in (completed, domain):
        response = client.post(f"/api/v1/admin/outbox/{row.id}/retry", headers=admin_auth_headers)
        assert response.status_code == 428
