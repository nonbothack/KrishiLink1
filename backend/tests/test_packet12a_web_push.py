import base64
import uuid
from datetime import datetime, timedelta, timezone

from app.models import Notification, OutboxEvent, User, WebPushAttempt, WebPushDelivery, WebPushSubscription
from app.modules.notifications import web_push_provider, web_push_service
from app.modules.notifications.service import NotificationService
from app.workers import celery_app as worker_module


def _keys():
    p256dh = base64.urlsafe_b64encode(b"\x04" + b"p" * 64).decode().rstrip("=")
    auth = base64.urlsafe_b64encode(b"a" * 16).decode().rstrip("=")
    return p256dh, auth


def _endpoint(token="fixture"):
    return f"https://fcm.googleapis.com/fcm/send/{token}"


def _new_test_user(db_session):
    user = User(id=uuid.uuid4(), full_name="Push Test Farmer", role="farmer", is_active=True)
    db_session.add(user)
    db_session.commit()
    return user


def test_push_capability_requires_auth_and_never_exposes_private_key(client, auth_headers, monkeypatch):
    from pydantic import SecretStr

    monkeypatch.setattr(web_push_provider, "capability_status", lambda: ("AVAILABLE", "public-vapid-key"))
    from app.core.config import settings

    monkeypatch.setattr(settings, "web_push_vapid_private_key", SecretStr("not-returned-private-key"))
    unauthenticated = client.get("/api/v1/notifications/push/capability")
    assert unauthenticated.status_code == 401
    response = client.get("/api/v1/notifications/push/capability", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "AVAILABLE", "application_server_key": "public-vapid-key", "explicit_opt_in": True,
    }
    assert "not-returned-private-key" not in response.text


def test_push_subscription_is_authenticated_account_scoped_and_explicit(client, auth_headers, buyer_auth_headers, monkeypatch):
    monkeypatch.setattr(web_push_provider, "capability_status", lambda: ("AVAILABLE", "public-key"))
    p256dh, auth = _keys()
    payload = {"endpoint": _endpoint("shared-device"), "keys": {"p256dh": p256dh, "auth": auth}, "language": "mr"}
    first = client.post("/api/v1/notifications/push/subscriptions", json=payload, headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["data"]["status"] == "ACTIVE"
    assert "endpoint" not in first.text
    first_id = first.json()["data"]["id"]
    repeated = client.post(
        "/api/v1/notifications/push/subscriptions", json={**payload, "language": "hi"}, headers=auth_headers,
    )
    assert repeated.json()["data"]["id"] == first_id

    # Merely loading/reconciling as another account revokes the stale delivery
    # association; it does not silently transfer it to the new account.
    reconcile = client.post(
        "/api/v1/notifications/push/reconcile", json={"endpoint": payload["endpoint"]}, headers=buyer_auth_headers,
    )
    assert reconcile.json()["data"]["status"] == "REASSOCIATION_REQUIRED"

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        assert db.query(WebPushSubscription).filter(WebPushSubscription.endpoint_hash == web_push_service.endpoint_digest(payload["endpoint"])).one().is_active is False
    finally:
        db.close()

    second = client.post("/api/v1/notifications/push/subscriptions", json=payload, headers=buyer_auth_headers)
    assert second.status_code == 200
    assert second.json()["data"]["status"] == "ACTIVE"
    deleted_by_old_user = client.request(
        "DELETE", "/api/v1/notifications/push/subscriptions/current", json={"endpoint": payload["endpoint"]}, headers=auth_headers,
    )
    assert deleted_by_old_user.json()["data"]["status"] == "NOT_FOUND"


def test_push_endpoint_ssrf_key_validation_and_extra_fields_are_rejected(client, auth_headers, monkeypatch):
    monkeypatch.setattr(web_push_provider, "capability_status", lambda: ("AVAILABLE", "public-key"))
    p256dh, auth = _keys()
    invalid_host = client.post("/api/v1/notifications/push/subscriptions", json={
        "endpoint": "https://127.0.0.1/private", "keys": {"p256dh": p256dh, "auth": auth}, "language": "en",
    }, headers=auth_headers)
    assert invalid_host.status_code == 422
    invalid_key = client.post("/api/v1/notifications/push/subscriptions", json={
        "endpoint": _endpoint("bad-key"), "keys": {"p256dh": "x", "auth": "y"}, "language": "en",
    }, headers=auth_headers)
    assert invalid_key.status_code == 422
    client_user_id = uuid.uuid4()
    forged_owner = client.post("/api/v1/notifications/push/subscriptions", json={
        "endpoint": _endpoint("forged"), "keys": {"p256dh": p256dh, "auth": auth},
        "language": "en", "user_id": str(client_user_id),
    }, headers=auth_headers)
    assert forged_owner.status_code == 422


def test_push_payload_is_localized_and_excludes_private_notification_content(db_session, ensure_test_users):
    user = _new_test_user(db_session)
    notification = Notification(
        id=uuid.uuid4(), user_id=user.id, type="offer_received", title="Private price ₹999999",
        message="buyer phone 9999999999 and bank reference secret", related_id=uuid.uuid4(),
    )
    db_session.add(notification)
    db_session.commit()
    payload = web_push_service.safe_payload(notification, "hi")
    assert payload["category"] == "offer"
    assert payload["title"] == "ऑफ़र की सूचना"
    assert "999999" not in str(payload)
    assert "secret" not in str(payload)
    assert payload["path"].startswith("/offers?offer_id=")


def test_existing_notification_outbox_event_queues_push_then_delivery_is_deduplicated(
    db_session, ensure_test_users, monkeypatch,
):
    monkeypatch.setattr(web_push_provider, "configured", lambda: True)
    user = _new_test_user(db_session)
    p256dh, auth = _keys()
    subscription = WebPushSubscription(
        user_id=user.id, endpoint=_endpoint("delivery"), endpoint_hash=web_push_service.endpoint_digest(_endpoint("delivery")),
        p256dh=p256dh, auth=auth, language="en", is_active=True,
    )
    db_session.add(subscription)
    db_session.flush()
    notification = NotificationService.create_notification(
        db_session, user.id, "trade_update", "private", "private terms", related_id=uuid.uuid4(),
    )
    db_session.commit()
    event = db_session.query(OutboxEvent).filter_by(aggregate_id=str(notification.id)).one()
    queued = []
    monkeypatch.setattr(worker_module.dispatch_notification_web_push, "delay", lambda *args: queued.append(args))
    assert worker_module.dispatch_notification_outbox_event(event) is True
    assert queued == [(str(notification.id),)]
    assert worker_module.dispatch_notification_outbox_event(type("Other", (), {"aggregate": "trade", "aggregate_id": "x", "event_type": "TRADE_CREATED"})()) is False

    sent = []
    def sender(info, payload):
        sent.append(payload)
        return 201
    result = web_push_service.deliver_notification(db_session, str(notification.id), sender=sender)
    assert result == {"status": "COMPLETED", "delivered": 1, "retryable": 0}
    assert sent[0]["category"] == "trade"
    assert "private" not in str(sent[0])
    again = web_push_service.deliver_notification(db_session, str(notification.id), sender=sender)
    assert again["delivered"] == 0
    delivery = db_session.query(WebPushDelivery).filter_by(notification_id=notification.id).one()
    assert delivery.status == "DELIVERED"
    assert db_session.query(WebPushAttempt).filter_by(delivery_id=delivery.id).count() == 1


def test_web_push_transient_retry_and_gone_subscription_revoke(db_session, ensure_test_users, monkeypatch):
    monkeypatch.setattr(web_push_provider, "configured", lambda: True)
    user = _new_test_user(db_session)
    p256dh, auth = _keys()
    subscription = WebPushSubscription(
        user_id=user.id, endpoint=_endpoint("retry"), endpoint_hash=web_push_service.endpoint_digest(_endpoint("retry")),
        p256dh=p256dh, auth=auth, language="mr", is_active=True,
    )
    notification = Notification(id=uuid.uuid4(), user_id=user.id, type="price_alert", title="x", message="private", metadata_json={
        "crop": "Onion", "market": "Lasalgaon", "modal_price": "2500", "threshold": "1", "source": "AGMARKNET", "reported_date": "2026-09-17",
    })
    db_session.add_all([subscription, notification])
    db_session.commit()

    def fail_once(info, payload):
        raise web_push_provider.PushDeliveryError(503)

    first = web_push_service.deliver_notification(db_session, str(notification.id), sender=fail_once)
    assert first["retryable"] == 1
    delivery = db_session.query(WebPushDelivery).filter_by(notification_id=notification.id).one()
    assert delivery.status == "RETRY"
    assert db_session.query(WebPushAttempt).filter_by(delivery_id=delivery.id).one().outcome == "RETRYABLE_FAILURE"
    delivery.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    final = web_push_service.deliver_notification(db_session, str(notification.id), sender=lambda info, payload: 201)
    assert final["delivered"] == 1
    attempts = db_session.query(WebPushAttempt).filter_by(delivery_id=delivery.id).order_by(WebPushAttempt.attempt_number).all()
    assert [item.outcome for item in attempts] == ["RETRYABLE_FAILURE", "DELIVERED"]
    assert "2500" in str(web_push_service.safe_payload(notification, "mr"))
    assert "threshold" not in str(web_push_service.safe_payload(notification, "mr"))

    gone_notification = Notification(id=uuid.uuid4(), user_id=user.id, type="support_update", title="x", message="private")
    gone_subscription = WebPushSubscription(
        user_id=user.id, endpoint=_endpoint("gone"), endpoint_hash=web_push_service.endpoint_digest(_endpoint("gone")),
        p256dh=p256dh, auth=auth, language="en", is_active=True,
    )
    db_session.add_all([gone_notification, gone_subscription])
    db_session.commit()
    gone = web_push_service.deliver_notification(
        db_session, str(gone_notification.id), sender=lambda info, payload: (_ for _ in ()).throw(web_push_provider.PushDeliveryError(410)),
    )
    assert gone["retryable"] == 0
    assert gone_subscription.is_active is False
    assert db_session.query(WebPushDelivery).filter_by(
        notification_id=gone_notification.id, subscription_id=gone_subscription.id,
    ).one().status == "GONE"


def test_operator_health_is_aggregate_only(client, buyer_auth_headers, admin_auth_headers):
    denied = client.get("/api/v1/notifications/push/operator-health", headers=buyer_auth_headers)
    assert denied.status_code == 403
    allowed = client.get("/api/v1/notifications/push/operator-health", headers=admin_auth_headers)
    assert allowed.status_code == 200
    assert "endpoint" not in allowed.text
    assert "p256dh" not in allowed.text
