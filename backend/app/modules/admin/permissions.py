"""Least-privilege staff authorization and step-up grants."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import AuditLog, StaffActionGrant, User

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "user.read_support", "user.security_review", "staff.manage", "session.revoke",
        "verification.review", "verification.override", "market_source.review", "market_source.manage",
        "price_pipeline.operate", "trade.read_support", "trade.admin_action", "grievance.review",
        "fraud.review", "privacy_request.review", "outbox.inspect", "outbox.retry", "provider.inspect",
        "feature_flag.manage", "incident.manage", "audit.read", "support.case",
    },
    "operator": {"market_source.review", "market_source.manage", "price_pipeline.operate", "outbox.inspect", "outbox.retry", "provider.inspect", "incident.manage", "audit.read"},
    "support": {"user.read_support", "session.revoke", "trade.read_support", "grievance.review", "support.case"},
    "reviewer": {"verification.review", "market_source.review"},
    "fraud_reviewer": {"fraud.review", "user.security_review", "trade.read_support", "audit.read"},
}

SENSITIVE_ACTIONS = {"verification", "feature_flag", "fraud_restriction", "outbox_retry", "session_revoke", "staff_manage"}


def has_permission(user: User, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get((user.role or "").lower(), set())


def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)):
        if not has_permission(user, permission):
            raise HTTPException(403, "Staff permission required")
        return user
    return checker


def issue_grant(db: Session, staff: User, session_id: str | None, action_family: str) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(StaffActionGrant(
        staff_user_id=staff.id,
        session_id=session_id,
        action_family=action_family,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    ))
    return raw


def require_step_up(action_family: str):
    def checker(
        request: Request,
        grant: str | None = Header(default=None, alias="X-Privileged-Grant"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        if action_family not in SENSITIVE_ACTIONS:
            raise HTTPException(500, "Invalid privileged action family")
        if not grant:
            raise HTTPException(428, "Step-up authentication required")
        token_hash = hashlib.sha256(grant.encode()).hexdigest()
        row = db.query(StaffActionGrant).filter(
            StaffActionGrant.staff_user_id == user.id,
            StaffActionGrant.action_family == action_family,
            StaffActionGrant.token_hash == token_hash,
            StaffActionGrant.used_at.is_(None),
            StaffActionGrant.expires_at > datetime.now(timezone.utc),
        ).first()
        if not row or (row.session_id and row.session_id != getattr(request.state, "session_id", None)):
            raise HTTPException(403, "Invalid or expired step-up grant")
        row.used_at = datetime.now(timezone.utc)
        return user
    return checker


def require_step_up_for_verification():
    """Keep the legacy development fixture usable; production verification requires step-up."""
    def checker(
        request: Request,
        grant: str | None = Header(default=None, alias="X-Privileged-Grant"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        if settings.env != "production" and user.role.lower() == "admin":
            return user
        if not grant:
            raise HTTPException(428, "Step-up authentication required")
        token_hash = hashlib.sha256(grant.encode()).hexdigest()
        row = db.query(StaffActionGrant).filter(
            StaffActionGrant.staff_user_id == user.id,
            StaffActionGrant.action_family == "verification",
            StaffActionGrant.token_hash == token_hash,
            StaffActionGrant.used_at.is_(None),
            StaffActionGrant.expires_at > datetime.now(timezone.utc),
        ).first()
        if not row or (row.session_id and row.session_id != getattr(request.state, "session_id", None)):
            raise HTTPException(403, "Invalid or expired step-up grant")
        row.used_at = datetime.now(timezone.utc)
        return user
    return checker


def safe_user_projection(user: User) -> dict:
    phone = user.phone_canonical or user.phone or ""
    masked_phone = ("*" * max(0, len(phone) - 4) + phone[-4:]) if phone else None
    return {
        "id": str(user.id), "public_reference": str(user.id), "full_name": user.full_name,
        "role": user.role, "account_status": user.account_status, "phone_masked": masked_phone,
        "email_present": bool(user.email), "language": None, "district": user.district,
        "is_active": user.is_active,
    }


def audit(db: Session, actor: User, action: str, entity: str, entity_id: str | None, request: Request, before=None, after=None, reason: str | None = None):
    payload = dict(after or {})
    if reason:
        payload["reason"] = reason
    db.add(AuditLog(
        actor_id=str(actor.id), action=action, entity=entity, entity_id=entity_id,
        before=before, after=payload, request_id=getattr(request.state, "request_id", None),
    ))
