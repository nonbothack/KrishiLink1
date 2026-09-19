import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.models import AuditLog, ConsentRecord, PrivacyRequest, User
from app.modules.auth.identity import CURRENT_POLICIES

router = APIRouter(prefix="/privacy", tags=["privacy"])


class PrivacyRequestCreate(BaseModel):
    request_type: Literal["access", "correction", "erasure"]
    note: str | None = Field(default=None, max_length=1000)


@router.get("/policies/current", response_model=dict)
def current_policies(request: Request):
    return {
        "success": True,
        "data": {key: dict(value) for key, value in CURRENT_POLICIES.items()},
        "message": "Current policy versions",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/consents", response_model=dict)
def list_consents(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.accepted_at.desc())
        .all()
    )
    return {
        "success": True,
        "data": {
            "marketing_enabled": any(
                row.policy_type == "marketing" and row.withdrawn_at is None for row in records
            ),
            "items": [
                {
                    "id": str(row.id),
                    "policy_type": row.policy_type,
                    "policy_version": row.policy_version,
                    "accepted_at": row.accepted_at.isoformat(),
                    "withdrawn_at": row.withdrawn_at.isoformat() if row.withdrawn_at else None,
                    "source": row.source,
                }
                for row in records
            ],
        },
        "message": "Consent history",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/consents/marketing/withdraw", response_model=dict)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_consent", production_requires_redis=True)
def withdraw_marketing_consent(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user.id,
            ConsentRecord.policy_type == "marketing",
            ConsentRecord.withdrawn_at.is_(None),
        )
        .order_by(ConsentRecord.accepted_at.desc())
        .with_for_update()
        .first()
    )
    if not record:
        return {"success": True, "data": {"marketing_enabled": False}, "message": "Marketing is already off"}
    record.withdrawn_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="consent.withdrawn",
            entity="consent_records",
            entity_id=str(record.id),
            after={"policy_type": "marketing", "policy_version": record.policy_version},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    db.commit()
    return {"success": True, "data": {"marketing_enabled": False}, "message": "Marketing consent withdrawn"}


@router.get("/requests", response_model=dict)
def list_privacy_requests(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PrivacyRequest)
        .filter(PrivacyRequest.user_id == user.id)
        .order_by(PrivacyRequest.submitted_at.desc())
        .all()
    )
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(row.id),
                    "request_type": row.request_type,
                    "status": row.status,
                    "submitted_at": row.submitted_at.isoformat(),
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                }
                for row in rows
            ]
        },
        "message": "Privacy requests",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/requests", response_model=dict, status_code=201)
@rate_limit(max_requests=5, window_seconds=3600, key_prefix="rl_privacy_req", production_requires_redis=True)
def create_privacy_request(
    data: PrivacyRequestCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = PrivacyRequest(
        id=uuid.uuid4(),
        user_id=user.id,
        request_type=data.request_type,
        user_note=data.note.strip() if data.note and data.note.strip() else None,
    )
    db.add(row)
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="privacy.request_submitted",
            entity="privacy_requests",
            entity_id=str(row.id),
            after={"request_type": data.request_type},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    db.commit()
    return {
        "success": True,
        "data": {"id": str(row.id), "request_type": row.request_type, "status": row.status},
        "message": "Request received",
        "request_id": getattr(request.state, "request_id", None),
    }
