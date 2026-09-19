"""Account-scoped Web Push registration and idempotent outbox delivery."""

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuditLog, Notification, WebPushAttempt, WebPushDelivery, WebPushSubscription
from app.modules.notifications import web_push_provider

_COPY = {
    "en": {
        "price_title": "Reported price alert",
        "price_body": "A reported market price crossed your alert. Open Prices to review the market, date and source.",
        "offer_title": "Offer update",
        "offer_body": "You have a marketplace offer update. Open KrishiLink to review it.",
        "trade_title": "Trade update",
        "trade_body": "There is an update to a trade. Open KrishiLink to review its current status.",
        "support_title": "Support update",
        "support_body": "There is an update to your support request. Open KrishiLink to review it.",
        "general_title": "KrishiLink update",
        "general_body": "You have a new update. Open KrishiLink to review it.",
    },
    "hi": {
        "price_title": "रिपोर्ट किए गए भाव की सूचना",
        "price_body": "रिपोर्ट किया गया मंडी भाव आपके अलर्ट से मेल खाता है। मंडी, तारीख और स्रोत देखने के लिए भाव खोलें।",
        "offer_title": "ऑफ़र की सूचना",
        "offer_body": "आपके लिए बाज़ार में एक नया ऑफ़र अपडेट है। इसे देखने के लिए KrishiLink खोलें।",
        "trade_title": "व्यापार की सूचना",
        "trade_body": "आपके व्यापार में एक अपडेट है। वर्तमान स्थिति देखने के लिए KrishiLink खोलें।",
        "support_title": "सहायता की सूचना",
        "support_body": "आपकी सहायता अनुरोध में एक अपडेट है। इसे देखने के लिए KrishiLink खोलें।",
        "general_title": "KrishiLink अपडेट",
        "general_body": "आपके लिए एक नया अपडेट है। इसे देखने के लिए KrishiLink खोलें।",
    },
    "mr": {
        "price_title": "नोंदवलेल्या भावाची सूचना",
        "price_body": "नोंदवलेला बाजारभाव तुमच्या अलर्टशी जुळला आहे. बाजार, तारीख आणि स्रोत पाहण्यासाठी भाव उघडा.",
        "offer_title": "ऑफरची सूचना",
        "offer_body": "तुमच्या बाजारातील ऑफरबाबत नवीन अपडेट आहे. ते पाहण्यासाठी KrishiLink उघडा.",
        "trade_title": "व्यवहाराची सूचना",
        "trade_body": "तुमच्या व्यवहारात अपडेट आहे. सध्याची स्थिती पाहण्यासाठी KrishiLink उघडा.",
        "support_title": "मदतीची सूचना",
        "support_body": "तुमच्या मदत विनंतीत अपडेट आहे. ते पाहण्यासाठी KrishiLink उघडा.",
        "general_title": "KrishiLink अपडेट",
        "general_body": "तुमच्यासाठी नवीन अपडेट आहे. ते पाहण्यासाठी KrishiLink उघडा.",
    },
}
_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


def endpoint_digest(endpoint: str) -> str:
    return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def subscribe(db: Session, user_id: uuid.UUID, endpoint: str, p256dh: str, auth: str, language: str) -> WebPushSubscription:
    web_push_provider.validate_endpoint(endpoint)
    web_push_provider.validate_keys(p256dh, auth)
    digest = endpoint_digest(endpoint)
    now = datetime.now(timezone.utc)
    row = db.query(WebPushSubscription).filter(WebPushSubscription.endpoint_hash == digest).with_for_update().first()
    if row and row.user_id != user_id:
        previous_owner = str(row.user_id)
        row.is_active = False
        row.revoked_at = now
        row.updated_at = now
        db.add(AuditLog(
            actor_id=str(user_id), action="web_push.subscription_reassigned", entity="web_push_subscription",
            entity_id=digest, before={"previous_owner_id": previous_owner}, after={"new_owner_id": str(user_id)},
        ))
    if row:
        row.user_id = user_id
        row.endpoint = endpoint
        row.p256dh = p256dh
        row.auth = auth
        row.language = language
        row.is_active = True
        row.revoked_at = None
        row.updated_at = now
    else:
        row = WebPushSubscription(
            user_id=user_id, endpoint=endpoint, endpoint_hash=digest, p256dh=p256dh, auth=auth,
            language=language, is_active=True, created_at=now, updated_at=now,
        )
        db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Endpoint ownership changed concurrently. Fail closed; a retry can
        # perform a fresh explicit association after observing the conflict.
        raise ValueError("Subscription ownership changed; please retry") from None
    db.refresh(row)
    return row


def reconcile(db: Session, user_id: uuid.UUID, endpoint: str) -> str:
    web_push_provider.validate_endpoint(endpoint)
    digest = endpoint_digest(endpoint)
    row = db.query(WebPushSubscription).filter(WebPushSubscription.endpoint_hash == digest).with_for_update().first()
    if not row:
        return "NOT_REGISTERED"
    if row.user_id == user_id and row.is_active:
        return "ACTIVE"
    if not row.is_active:
        return "NOT_REGISTERED"
    if row.is_active:
        row.is_active = False
        row.revoked_at = datetime.now(timezone.utc)
        row.updated_at = datetime.now(timezone.utc)
        db.add(AuditLog(
            actor_id=str(user_id), action="web_push.subscription_reconciliation_revoked",
            entity="web_push_subscription", entity_id=digest,
            after={"reason": "authenticated account differs; explicit re-subscription required"},
        ))
        db.commit()
    return "REASSOCIATION_REQUIRED"


def unsubscribe(db: Session, user_id: uuid.UUID, endpoint: str) -> bool:
    web_push_provider.validate_endpoint(endpoint)
    digest = endpoint_digest(endpoint)
    row = db.query(WebPushSubscription).filter(
        WebPushSubscription.endpoint_hash == digest,
        WebPushSubscription.user_id == user_id,
        WebPushSubscription.is_active.is_(True),
    ).with_for_update().first()
    if not row:
        return False
    now = datetime.now(timezone.utc)
    row.is_active = False
    row.revoked_at = now
    row.updated_at = now
    db.add(AuditLog(
        actor_id=str(user_id), action="web_push.subscription_revoked", entity="web_push_subscription",
        entity_id=digest, after={"reason": "user requested unsubscribe"},
    ))
    db.commit()
    return True


def _route(notification: Notification) -> tuple[str, str]:
    kind = (notification.type or "").lower()
    related = str(notification.related_id or "")
    if kind == "price_alert":
        return "price", "/prices"
    if "offer" in kind and re.fullmatch(_UUID, related):
        return "offer", f"/offers?offer_id={related}"
    if ("trade" in kind or "order" in kind or "deal" in kind) and re.fullmatch(_UUID, related):
        return "trade", f"/trades/{related}"
    if "grievance" in kind or "dispute" in kind or "support" in kind:
        return "support", "/grievances"
    if "offer" in kind:
        return "offer", "/offers"
    if "trade" in kind or "order" in kind:
        return "trade", "/transactions"
    return "general", "/"


def safe_payload(notification: Notification, language: str) -> dict:
    language = language if language in _COPY else "en"
    category, path = _route(notification)
    strings = _COPY[language]
    copy_key = {"price": "price", "offer": "offer", "trade": "trade", "support": "support"}.get(category, "general")
    title = strings[f"{copy_key}_title"][:80]
    body = strings[f"{copy_key}_body"][:180]
    if category == "price" and isinstance(notification.metadata_json, dict):
        facts = notification.metadata_json
        # Only public reported-price facts are eligible. Never include the
        # user's threshold, location, notification message, or account details.
        def clean(value, limit):
            return "".join(char for char in str(value or "").strip() if ord(char) >= 32 and ord(char) != 127)[:limit]

        crop = clean(facts.get("crop"), 48)
        market = clean(facts.get("market"), 64)
        source = clean(facts.get("source"), 32)
        date = str(facts.get("reported_date") or "").strip()[:10]
        amount = str(facts.get("modal_price") or "").strip()[:16]
        if (
            crop and market and source and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
            and re.fullmatch(r"\d{1,9}(?:\.\d{1,2})?", amount)
        ):
            body = f"{crop} · {market}: ₹{amount}/qtl · {date} · {source}"[:180]
    return {
        "schema_version": 1,
        "notification_id": str(notification.id),
        "category": category,
        "title": title,
        "body": body,
        "path": path,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


def _result_category(status_code: int | None) -> str:
    if status_code in (404, 410):
        return "GONE"
    if status_code is None or status_code in (408, 425, 429) or status_code >= 500:
        return "RETRYABLE_FAILURE"
    return "PERMANENT_FAILURE"


def _create_delivery(db: Session, notification_id: uuid.UUID, subscription_id: uuid.UUID) -> WebPushDelivery | None:
    existing = db.query(WebPushDelivery).filter_by(
        notification_id=notification_id, subscription_id=subscription_id,
    ).with_for_update().first()
    if existing:
        return existing
    row = WebPushDelivery(notification_id=notification_id, subscription_id=subscription_id, status="PENDING")
    db.add(row)
    try:
        db.commit()
        return db.query(WebPushDelivery).filter_by(
            notification_id=notification_id, subscription_id=subscription_id,
        ).with_for_update().first()
    except IntegrityError:
        db.rollback()
        return db.query(WebPushDelivery).filter_by(
            notification_id=notification_id, subscription_id=subscription_id,
        ).with_for_update().first()


def deliver_notification(db: Session, notification_id: str, sender=None) -> dict:
    if not web_push_provider.configured():
        return {"status": "UNAVAILABLE", "delivered": 0, "retryable": 0}
    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        return {"status": "NOT_FOUND", "delivered": 0, "retryable": 0}
    notification = db.get(Notification, notif_uuid)
    if not notification:
        return {"status": "NOT_FOUND", "delivered": 0, "retryable": 0}
    subscriptions = db.query(WebPushSubscription).filter(
        WebPushSubscription.user_id == notification.user_id,
        WebPushSubscription.is_active.is_(True),
    ).all()
    delivered = retryable = 0
    now = datetime.now(timezone.utc)
    for subscription in subscriptions:
        delivery = _create_delivery(db, notif_uuid, subscription.id)
        if not delivery or delivery.status == "DELIVERED" or delivery.status == "FAILED" or delivery.status == "GONE":
            continue
        if delivery.status == "SENDING" and _as_utc(delivery.lease_until) and _as_utc(delivery.lease_until) > now:
            continue
        if delivery.status == "RETRY" and _as_utc(delivery.next_attempt_at) and _as_utc(delivery.next_attempt_at) > now:
            retryable += 1
            continue
        delivery.status = "SENDING"
        delivery.lease_until = now + timedelta(minutes=2)
        delivery.attempt_count += 1
        delivery.last_attempt_at = now
        attempt_number = delivery.attempt_count
        db.commit()
        attempt_started_at = datetime.now(timezone.utc)
        payload = safe_payload(notification, subscription.language)
        info = {"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}}
        try:
            try:
                web_push_provider.validate_endpoint(subscription.endpoint)
            except ValueError:
                raise web_push_provider.PushDeliveryError(400) from None
            status_code = (sender or web_push_provider.send)(info, payload)
            if not (200 <= int(status_code) < 300):
                raise web_push_provider.PushDeliveryError(int(status_code))
            delivery.status = "DELIVERED"
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.last_outcome = "DELIVERED"
            delivery.lease_until = None
            subscription.last_success_at = delivery.delivered_at
            db.add(WebPushAttempt(
                delivery_id=delivery.id, attempt_number=attempt_number, outcome="DELIVERED", status_code=int(status_code),
                attempted_at=attempt_started_at, completed_at=delivery.delivered_at,
            ))
            delivered += 1
        except web_push_provider.PushDeliveryError as exc:
            outcome = _result_category(exc.status_code)
            db.add(WebPushAttempt(
                delivery_id=delivery.id, attempt_number=attempt_number, outcome=outcome, status_code=exc.status_code,
                attempted_at=attempt_started_at, completed_at=datetime.now(timezone.utc),
            ))
            delivery.last_outcome = outcome
            delivery.lease_until = None
            if outcome == "GONE":
                delivery.status = "GONE"
                subscription.is_active = False
                subscription.revoked_at = datetime.now(timezone.utc)
                subscription.updated_at = subscription.revoked_at
            elif outcome == "RETRYABLE_FAILURE" and delivery.attempt_count < settings.web_push_max_attempts:
                delivery.status = "RETRY"
                delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=min(2 ** delivery.attempt_count, 30))
                retryable += 1
            else:
                delivery.status = "FAILED"
        except Exception:
            # Test-injected and unexpected adapter errors have no safe provider
            # detail; preserve a bounded retry only, with no sensitive logging.
            outcome = "RETRYABLE_FAILURE"
            db.add(WebPushAttempt(
                delivery_id=delivery.id, attempt_number=attempt_number, outcome=outcome,
                attempted_at=attempt_started_at, completed_at=datetime.now(timezone.utc),
            ))
            delivery.last_outcome = outcome
            delivery.lease_until = None
            if delivery.attempt_count < settings.web_push_max_attempts:
                delivery.status = "RETRY"
                delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=min(2 ** delivery.attempt_count, 30))
                retryable += 1
            else:
                delivery.status = "FAILED"
        db.commit()
    return {"status": "COMPLETED", "delivered": delivered, "retryable": retryable}


def retry_due_deliveries(db: Session) -> list[str]:
    now = datetime.now(timezone.utc)
    due = db.query(WebPushDelivery.notification_id).filter(
        ((WebPushDelivery.status == "RETRY") & (WebPushDelivery.next_attempt_at <= now))
        | ((WebPushDelivery.status == "SENDING") & (WebPushDelivery.lease_until <= now))
    ).distinct().limit(100).all()
    return sorted({str(item[0]) for item in due})
