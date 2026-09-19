from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models import Notification, OutboxEvent, WebPushAttempt, WebPushDelivery, WebPushSubscription
from app.modules.notifications import web_push_provider, web_push_service
from app.modules.notifications.sms_service import SMSService
from app.modules.notifications.web_push_schemas import PushEndpointInput, PushSubscriptionInput

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/push/capability", response_model=dict)
def web_push_capability(request: Request, user=Depends(get_current_user)):
    status, public_key = web_push_provider.capability_status()
    return {
        "success": True,
        "data": {"status": status, "application_server_key": public_key, "explicit_opt_in": True},
        "message": "Web Push capability",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/push/subscriptions", response_model=dict)
def register_web_push_subscription(
    data: PushSubscriptionInput,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    status, _ = web_push_provider.capability_status()
    if status != "AVAILABLE":
        raise HTTPException(status_code=503, detail="Web Push is not configured")
    try:
        subscription = web_push_service.subscribe(
            db, user.id, data.endpoint, data.keys.p256dh, data.keys.auth, data.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "success": True,
        "data": {"id": str(subscription.id), "status": "ACTIVE", "language": subscription.language},
        "message": "This browser is subscribed",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/push/reconcile", response_model=dict)
def reconcile_web_push_subscription(
    data: PushEndpointInput,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        state = web_push_service.reconcile(db, user.id, data.endpoint)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "success": True,
        "data": {"status": state},
        "message": "Subscription state checked",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.delete("/push/subscriptions/current", response_model=dict)
def revoke_web_push_subscription(
    data: PushEndpointInput,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        revoked = web_push_service.unsubscribe(db, user.id, data.endpoint)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "success": True,
        "data": {"status": "REVOKED" if revoked else "NOT_FOUND"},
        "message": "Subscription state updated",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/push/operator-health", response_model=dict)
def web_push_operator_health(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "operator")),
):
    capability, _ = web_push_provider.capability_status()
    since = datetime.now(timezone.utc) - timedelta(days=1)
    data = {
        "configuration": capability,
        "active_subscriptions": db.query(WebPushSubscription).filter(WebPushSubscription.is_active.is_(True)).count(),
        "delivered_last_24h": db.query(WebPushDelivery).filter(
            WebPushDelivery.status == "DELIVERED", WebPushDelivery.delivered_at >= since,
        ).count(),
        "retry_or_failure_last_24h": db.query(WebPushDelivery).filter(
            WebPushDelivery.status.in_(["RETRY", "FAILED", "GONE"]), WebPushDelivery.last_attempt_at >= since,
        ).count(),
        "attempts_last_24h": db.query(WebPushAttempt).filter(WebPushAttempt.attempted_at >= since).count(),
    }
    return {"success": True, "data": data, "message": "Aggregate Web Push health", "request_id": getattr(request.state, "request_id", None)}


@router.get("/outbox/pending", response_model=dict)
def outbox_pending(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Restrict to admin or operator roles only — strictly enforced server-side
    if getattr(user, "role", None) not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Forbidden: Admin or operator privileges required")

    items = (
        db.query(OutboxEvent)
        .filter(OutboxEvent.status == "PENDING")
        .order_by(OutboxEvent.created_at.desc())
        .limit(20)
        .all()
    )
    data = [{"id": str(o.id), "aggregate": o.aggregate, "event_type": o.event_type, "status": o.status} for o in items]
    return {
        "success": True,
        "data": data,
        "message": f"{len(data)} pending outbox",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("", response_model=dict)
def list_notifications(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read == False)
    total = q.count()
    items = q.order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "metadata": n.metadata_json,
            "is_read": n.is_read,
            "related_id": str(n.related_id) if n.related_id else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} notifications",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{notif_id}/read", response_model=dict)
def mark_read(notif_id: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    n = db.get(Notification, notif_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {
        "success": True,
        "data": {"id": str(n.id), "is_read": True},
        "message": "Marked read",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/read-all", response_model=dict)
def mark_all_read(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).update(
        {"is_read": True}
    )
    db.commit()
    return {
        "success": True,
        "data": {"updated": True},
        "message": "All notifications marked as read",
        "request_id": getattr(request.state, "request_id", None),
    }


class TestSMSRequest(BaseModel):
    phone: str
    message: str | None = None


@router.post("/test-sms", response_model=dict)
def test_sms(
    data: TestSMSRequest,
    request: Request,
    user=Depends(get_current_user),
):
    """
    Test SMS delivery endpoint for SIH presentation and live sanity check.
    Allows testing Fast2SMS delivery to any 10-digit Indian phone number directly.
    """
    if user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Administrator role required")
    if settings.env != "development":
        raise HTTPException(status_code=404, detail="Not found")
    if data.message:
        result = SMSService.send_raw_sms(
            phone=data.phone,
            message=data.message,
        )
    else:
        result = SMSService.send_deal_confirmation(
            farmer_phone=data.phone,
            farmer_name=getattr(user, "full_name", None) or "KrishiLink User",
            crop_name="Organic Wheat",
            quantity=50.0,
            price_per_unit=2450.0,
            order_id="TEST01",
        )
    return {
        "success": result.get("success", False),
        "data": result,
        "message": f"SMS dispatch attempt completed: {result.get('status')}",
        "request_id": getattr(request.state, "request_id", None),
    }

