import uuid
from datetime import datetime, timezone
from typing import Literal

import redis as redis_lib
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import check_db, get_db
from app.core.deps import require_role
from app.core.security import hash_password, verify_password
from app.models import (
    AuditLog,
    BuyerProfile,
    Dispute,
    FPOProfile,
    FraudCase,
    IncidentRecord,
    Lot,
    OutboxEvent,
    PrivacyRequest,
    SupportCase,
    SupportNote,
    SystemConfiguration,
    Transaction,
    User,
    VerificationRecord,
)
from app.modules.admin.permissions import (
    audit,
    issue_grant,
    require_permission,
    require_step_up,
    require_step_up_for_verification,
    safe_user_projection,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class StepUpRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    action_family: Literal["verification", "feature_flag", "fraud_restriction", "outbox_retry", "session_revoke", "staff_manage"]


class CaseDecisionRequest(BaseModel):
    status: Literal["IN_REVIEW", "ACTION_REQUIRED", "RESOLVED", "DISMISSED"]
    decision: str | None = Field(default=None, max_length=120)
    reason: str = Field(min_length=3, max_length=500)


class RestrictionRequest(BaseModel):
    status: Literal["RESTRICTED", "SUSPENDED", "ACTIVE"]
    reason: str = Field(min_length=3, max_length=300)
    expires_at: datetime | None = None


class SupportCaseRequest(BaseModel):
    requester_id: uuid.UUID
    category: Literal["ACCOUNT_ACCESS", "PROFILE", "PRICE_DATA", "LOT", "OFFER", "TRADE", "NOTIFICATION", "VERIFICATION", "PRIVACY", "OTHER"]
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    linked_grievance_id: uuid.UUID | None = None


class SupportNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class FeatureFlagRequest(BaseModel):
    enabled: bool
    reason: str = Field(min_length=3, max_length=500)


class IncidentRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    affected_capability: str | None = Field(default=None, max_length=100)
    summary: str = Field(min_length=3, max_length=4000)
    runbook_ref: str | None = Field(default=None, max_length=120)


class StaffCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=72)
    role: Literal["admin", "operator", "support", "reviewer", "fraud_reviewer"]
    reason: str = Field(min_length=3, max_length=500)


class VerificationReviewRequest(BaseModel):
    status: Literal["VERIFIED", "REJECTED", "PENDING_REVIEW", "NEEDS_MORE_INFORMATION"]
    method: str = Field(min_length=3, max_length=100)
    provider: str | None = Field(default=None, max_length=100)
    provider_reference: str | None = Field(default=None, min_length=3, max_length=200)
    reason_code: str | None = Field(default=None, max_length=100)

    @field_validator("method", "provider", "provider_reference", "reason_code", mode="before")
    @classmethod
    def trim_review_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def verified_status_needs_evidence_reference(self):
        if self.status == "VERIFIED" and not self.provider_reference:
            raise ValueError("A verification evidence reference is required")
        return self


@router.get("/users", response_model=dict)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin")),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = None,
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role.lower())
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "legacy_is_verified": u.is_verified,
            "is_active": u.is_active,
        }
        for u in items
    ]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} users",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/audit", response_model=dict)
def audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_permission("audit.read")),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: str | None = Query(default=None, max_length=100),
    entity: str | None = Query(default=None, max_length=100),
    correlation_id: str | None = Query(default=None, max_length=100),
):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if correlation_id:
        q = q.filter(AuditLog.request_id == correlation_id)
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(a.id),
            "actor_id": a.actor_id,
            "action": a.action,
            "entity": a.entity,
            "entity_id": a.entity_id,
            "request_id": a.request_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in items
    ]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} logs",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/system-health", response_model=dict)
def system_health(request: Request, db: Session = Depends(get_db), user=Depends(require_permission("provider.inspect"))):
    checks = {}
    try:
        checks["database"] = "HEALTHY" if check_db() else "DOWN"
    except:
        checks["database"] = "DOWN"
    try:
        r = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
        checks["redis"] = "HEALTHY"
    except:
        checks["redis"] = "DOWN"
    checks["api"] = "HEALTHY"
    # counts
    stats = {
        "users": db.query(User).count(),
        "lots": db.query(Lot).count(),
        "transactions": db.query(Transaction).count(),
        "disputes": db.query(Dispute).count(),
    }
    overall = "HEALTHY" if all(v == "HEALTHY" for v in checks.values()) else "DEGRADED"
    return {
        "success": True,
        "data": {"status": overall, "checks": checks, "stats": stats},
        "message": f"System {overall}",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/users/{user_id}/verify", response_model=dict)
def verify_user(user_id: str, request: Request, db: Session = Depends(get_db), admin=Depends(require_role("admin"))):
    del user_id, request, db, admin
    raise HTTPException(
        status_code=409,
        detail="Generic verification is retired; submit a dimension-specific evidence review",
    )


@router.post("/users/{user_id}/verifications/{dimension}", response_model=dict)
def review_verification(
    user_id: str,
    dimension: str,
    data: VerificationReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_permission("verification.review")),
    _step_up=Depends(require_step_up_for_verification()),
):
    allowed_dimensions = {"identity", "business", "gst", "bank", "organization"}
    if dimension not in allowed_dimensions:
        raise HTTPException(422, "This verification dimension must use its dedicated verification flow")
    if admin.role.lower() == "reviewer" and dimension not in {"business", "gst", "organization"}:
        raise HTTPException(403, "Reviewer is not assigned to this verification dimension")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    buyer_profile = None
    fpo_profile = None
    if dimension in {"business", "gst"}:
        if user.role != "buyer":
            raise HTTPException(422, "Business and GST reviews require a buyer account")
        buyer_profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == user.id).first()
        if not buyer_profile:
            raise HTTPException(409, "Buyer onboarding must be completed before verification review")
    if dimension == "organization":
        if user.role != "fpo":
            raise HTTPException(422, "Organization review requires an FPO account")
        fpo_profile = db.query(FPOProfile).filter(FPOProfile.user_id == user.id).first()
        if not fpo_profile:
            raise HTTPException(409, "FPO onboarding must be completed before verification review")
    now = datetime.now(timezone.utc)
    record = VerificationRecord(
        user_id=user.id,
        dimension=dimension,
        status=data.status,
        method=data.method.strip(),
        provider=data.provider.strip() if data.provider else "manual_review",
        provider_reference=data.provider_reference.strip() if data.provider_reference else None,
        reason_code=data.reason_code.strip() if data.reason_code else None,
        evidence_metadata={"reviewed_by": str(admin.id)},
        submitted_at=now if data.status == "PENDING_REVIEW" else None,
        checked_at=now if data.status != "PENDING_REVIEW" else None,
    )
    db.add(record)
    if dimension == "business" and buyer_profile:
        buyer_profile.business_verification_status = data.status
    elif dimension == "organization" and fpo_profile:
        fpo_profile.organization_verification_status = data.status
    db.add(
        AuditLog(
            actor_id=str(admin.id),
            action="verification.reviewed",
            entity="verification_records",
            entity_id=str(record.id),
            after={"user_id": str(user.id), "dimension": dimension, "status": data.status},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    db.commit()
    return {
        "success": True,
        "data": {"id": str(record.id), "dimension": dimension, "status": data.status},
        "message": "Dimension-specific verification review recorded",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/step-up", response_model=dict)
def step_up(
    payload: StepUpRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_role("admin", "operator", "support", "reviewer", "fraud_reviewer")),
):
    if payload.action_family in {"staff_manage", "feature_flag"} and user.role.lower() != "admin":
        raise HTTPException(403, "Only administrators may step up for this action")
    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Reauthentication failed")
    token = issue_grant(db, user, getattr(request.state, "session_id", None), payload.action_family)
    audit(db, user, "staff.step_up.granted", "staff_action_grants", None, request, after={"action_family": payload.action_family})
    db.commit()
    return {"success": True, "data": {"grant": token, "expires_in_seconds": 600, "action_family": payload.action_family}, "message": "Step-up granted"}


@router.get("/verification/queue", response_model=dict)
def verification_queue(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_permission("verification.review")),
    dimension: str | None = Query(default=None, max_length=40),
):
    q = db.query(VerificationRecord).filter(VerificationRecord.status.in_(["PENDING_REVIEW", "NEEDS_MORE_INFORMATION"]))
    if dimension:
        q = q.filter(VerificationRecord.dimension == dimension)
    rows = q.order_by(VerificationRecord.created_at.asc()).limit(100).all()
    return {"success": True, "data": {"items": [{"id": str(row.id), "user_id": str(row.user_id), "dimension": row.dimension, "status": row.status, "method": row.method, "provider": row.provider, "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None} for row in rows]}, "message": f"{len(rows)} verification reviews", "request_id": getattr(request.state, "request_id", None)}


@router.get("/fraud/cases", response_model=dict)
def fraud_cases(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_permission("fraud.review")),
    status_filter: str | None = Query(default=None, alias="status", max_length=30),
):
    q = db.query(FraudCase).order_by(FraudCase.created_at.desc()).limit(100)
    if status_filter:
        q = db.query(FraudCase).filter(FraudCase.status == status_filter).order_by(FraudCase.created_at.desc()).limit(100)
    rows = q.all()
    data = [{"id": str(row.id), "subject_type": row.subject_type, "subject_id": row.subject_id, "signal_type": row.signal_type, "rule_id": row.rule_id, "rule_version": row.rule_version, "severity": row.severity, "status": row.status, "evidence_refs": row.evidence_refs, "decision": row.decision, "created_at": row.created_at.isoformat() if row.created_at else None} for row in rows]
    return {"success": True, "data": {"items": data}, "message": f"{len(data)} cases requiring review", "request_id": getattr(request.state, "request_id", None)}


@router.post("/fraud/cases/{case_id}/decision", response_model=dict)
def decide_fraud_case(
    case_id: uuid.UUID,
    payload: CaseDecisionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_permission("fraud.review")),
    _step_up=Depends(require_step_up("fraud_restriction")),
):
    # Serialize reviewer decisions so two concurrent staff actions cannot both
    # observe an open case and overwrite each other's terminal decision.
    row = db.query(FraudCase).filter(FraudCase.id == case_id).with_for_update().first()
    if not row:
        raise HTTPException(404, "Fraud review case not found")
    if row.status in {"RESOLVED", "DISMISSED"}:
        raise HTTPException(409, "Fraud review case is already closed")
    before = {"status": row.status, "decision": row.decision}
    row.status, row.decision, row.decision_reason = payload.status, payload.decision, payload.reason
    row.assigned_reviewer_id = user.id
    if payload.status in {"RESOLVED", "DISMISSED"}:
        row.resolved_at = datetime.now(timezone.utc)
    audit(db, user, "fraud.case.decided", "fraud_cases", str(row.id), request, before=before, after={"status": row.status, "decision": row.decision}, reason=payload.reason)
    db.commit()
    return {"success": True, "data": {"id": str(row.id), "status": row.status, "decision": row.decision}, "message": "Fraud review decision recorded"}


@router.post("/users/{user_id}/restriction", response_model=dict)
def restrict_user(
    user_id: uuid.UUID,
    payload: RestrictionRequest,
    request: Request,
    db: Session = Depends(get_db),
    actor=Depends(require_permission("user.security_review")),
    _step_up=Depends(require_step_up("fraud_restriction")),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    before = {"account_status": target.account_status, "restricted_until": target.restricted_until.isoformat() if target.restricted_until else None}
    target.account_status = payload.status
    target.restricted_until = payload.expires_at if payload.status != "ACTIVE" else None
    target.restriction_reason = payload.reason if payload.status != "ACTIVE" else None
    audit(db, actor, "user.restriction.changed", "users", str(target.id), request, before=before, after={"account_status": target.account_status, "restricted_until": target.restricted_until.isoformat() if target.restricted_until else None}, reason=payload.reason)
    db.commit()
    return {"success": True, "data": {"id": str(target.id), "account_status": target.account_status, "restricted_until": target.restricted_until.isoformat() if target.restricted_until else None}, "message": "Account review state updated"}


@router.get("/support/users/{user_id}/context", response_model=dict)
def support_user_context(user_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("user.read_support"))):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    audit(db, actor, "support.user.lookup", "users", str(target.id), request, after={"projection": "safe_support"})
    db.commit()
    cases = db.query(SupportCase).filter(SupportCase.requester_id == target.id).order_by(SupportCase.created_at.desc()).limit(20).all()
    return {"success": True, "data": {"user": safe_user_projection(target), "cases": [{"id": str(case.id), "public_reference": case.public_reference, "category": case.category, "status": case.status, "subject": case.subject, "created_at": case.created_at.isoformat() if case.created_at else None} for case in cases]}, "message": "Scoped support context"}


@router.post("/support/cases", response_model=dict, status_code=201)
def create_support_case(payload: SupportCaseRequest, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("support.case"))):
    if not db.get(User, payload.requester_id):
        raise HTTPException(404, "Requester not found")
    if payload.linked_grievance_id and not db.get(Dispute, payload.linked_grievance_id):
        raise HTTPException(404, "Linked grievance not found")
    row = SupportCase(id=uuid.uuid4(), public_reference=f"SUP-{uuid.uuid4().hex[:10].upper()}", requester_id=payload.requester_id, category=payload.category, subject=payload.subject.strip(), description=payload.description.strip(), linked_grievance_id=payload.linked_grievance_id)
    db.add(row)
    audit(db, actor, "support.case.created", "support_cases", str(row.id), request, after={"category": row.category, "public_reference": row.public_reference})
    db.commit()
    return {"success": True, "data": {"id": str(row.id), "public_reference": row.public_reference, "status": row.status}, "message": "Support case created"}


@router.post("/support/cases/{case_id}/notes", response_model=dict)
def add_support_note(case_id: uuid.UUID, payload: SupportNoteRequest, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("support.case"))):
    if not db.get(SupportCase, case_id):
        raise HTTPException(404, "Support case not found")
    row = SupportNote(case_id=case_id, author_id=actor.id, note=payload.note.strip())
    db.add(row)
    audit(db, actor, "support.note.added", "support_cases", str(case_id), request, after={"note_id": str(row.id)})
    db.commit()
    return {"success": True, "data": {"id": str(row.id)}, "message": "Internal note recorded"}


@router.post("/users/{user_id}/revoke-sessions", response_model=dict)
def revoke_sessions(user_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("session.revoke")), _step_up=Depends(require_step_up("session_revoke"))):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    target.auth_token_version = int(target.auth_token_version or 0) + 1
    audit(db, actor, "session.revoked_all", "users", str(target.id), request, after={"reason": "staff_security_action"})
    db.commit()
    return {"success": True, "data": {"user_id": str(target.id)}, "message": "Active sessions revoked"}


@router.get("/outbox", response_model=dict)
def outbox_queue(request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("outbox.inspect")), status_filter: str | None = Query(default=None, alias="status", max_length=20), limit: int = Query(50, ge=1, le=100)):
    q = db.query(OutboxEvent).order_by(OutboxEvent.created_at.desc())
    if status_filter:
        q = q.filter(OutboxEvent.status == status_filter)
    rows = q.limit(limit).all()
    return {"success": True, "data": {"items": [{"id": str(row.id), "aggregate": row.aggregate, "event_type": row.event_type, "status": row.status, "retry_count": row.retry_count, "correlation_id": row.correlation_id, "last_error_category": row.last_error_category, "created_at": row.created_at.isoformat() if row.created_at else None} for row in rows]}, "message": f"{len(rows)} outbox events"}


@router.post("/outbox/{event_id}/retry", response_model=dict)
def retry_outbox(event_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("outbox.retry")), _step_up=Depends(require_step_up("outbox_retry"))):
    row = db.get(OutboxEvent, event_id)
    if not row:
        raise HTTPException(404, "Outbox event not found")
    allowed = row.aggregate == "notification" and str(row.event_type).startswith("NOTIFICATION_")
    if not allowed or row.status not in {"FAILED", "PENDING"}:
        raise HTTPException(409, "This event is not eligible for safe delivery retry")
    if row.status == "COMPLETED":
        raise HTTPException(409, "Completed events cannot be replayed")
    before = {"status": row.status, "retry_count": row.retry_count}
    row.status, row.retry_count, row.last_error_category = "PENDING", 0, None
    audit(db, actor, "outbox.notification_retry_requested", "outbox_events", str(row.id), request, before=before, after={"status": row.status}, reason="manual safe delivery retry")
    db.commit()
    return {"success": True, "data": {"id": str(row.id), "status": row.status}, "message": "Notification delivery queued for retry"}


@router.get("/provider-health", response_model=dict)
def provider_health(request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("provider.inspect"))):
    from app.core.config import settings
    sms_configured = bool(settings.sms_provider and (settings.fast2sms_api_key or settings.twilio_account_sid or settings.smsgate_base_url))
    push_configured = bool(settings.web_push_enabled and settings.web_push_vapid_public_key and settings.web_push_vapid_private_key)
    return {"success": True, "data": {"sms": {"status": "AVAILABLE" if sms_configured else "UNCONFIGURED"}, "web_push": {"status": "AVAILABLE" if push_configured else "UNCONFIGURED"}, "database": {"status": "UNKNOWN"}}, "message": "Provider configuration status"}


@router.get("/privacy/queue", response_model=dict)
def privacy_queue(request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("privacy_request.review"))):
    rows = db.query(PrivacyRequest).filter(PrivacyRequest.status.in_(["RECEIVED", "IN_REVIEW", "ACTION_PENDING"])).order_by(PrivacyRequest.submitted_at.asc()).limit(100).all()
    return {"success": True, "data": {"items": [{"id": str(row.id), "request_type": row.request_type, "status": row.status, "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None} for row in rows]}, "message": f"{len(rows)} privacy requests awaiting review"}


@router.get("/feature-flags", response_model=dict)
def feature_flags(request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("feature_flag.manage"))):
    rows = db.query(SystemConfiguration).filter(SystemConfiguration.key.like("flag.%")).all()
    return {"success": True, "data": {row.key.removeprefix("flag."): {"enabled": bool((row.value or {}).get("enabled", False)), "updated_at": row.updated_at.isoformat() if row.updated_at else None} for row in rows}, "message": "Feature flag state"}


@router.put("/feature-flags/{flag_name}", response_model=dict)
def set_feature_flag(flag_name: str, payload: FeatureFlagRequest, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("feature_flag.manage")), _step_up=Depends(require_step_up("feature_flag"))):
    if not flag_name.replace("_", "").isalnum() or len(flag_name) > 60:
        raise HTTPException(422, "Invalid feature flag name")
    key = f"flag.{flag_name}"
    row = db.get(SystemConfiguration, key)
    before = dict(row.value) if row else None
    if row:
        row.value = {"enabled": payload.enabled}
        row.version = int(row.version or 0) + 1
        row.updated_by = str(actor.id)
    else:
        row = SystemConfiguration(key=key, value={"enabled": payload.enabled}, updated_by=str(actor.id))
        db.add(row)
    audit(db, actor, "feature_flag.changed", "system_configurations", key, request, before=before, after={"enabled": payload.enabled}, reason=payload.reason)
    db.commit()
    return {"success": True, "data": {"flag": flag_name, "enabled": payload.enabled}, "message": "Feature flag updated"}


@router.get("/incidents", response_model=dict)
def incidents(request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("incident.manage"))):
    rows = db.query(IncidentRecord).order_by(IncidentRecord.started_at.desc()).limit(100).all()
    return {"success": True, "data": {"items": [{"id": str(row.id), "title": row.title, "severity": row.severity, "status": row.status, "affected_capability": row.affected_capability, "summary": row.summary, "runbook_ref": row.runbook_ref, "started_at": row.started_at.isoformat() if row.started_at else None} for row in rows]}, "message": f"{len(rows)} incidents"}


@router.post("/incidents", response_model=dict, status_code=201)
def create_incident(payload: IncidentRequest, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("incident.manage"))):
    row = IncidentRecord(title=payload.title.strip(), severity=payload.severity, affected_capability=payload.affected_capability, summary=payload.summary.strip(), runbook_ref=payload.runbook_ref, created_by=actor.id)
    db.add(row)
    db.flush()
    audit(db, actor, "incident.opened", "incident_records", str(row.id), request, after={"severity": row.severity, "affected_capability": row.affected_capability})
    db.commit()
    return {"success": True, "data": {"id": str(row.id), "status": row.status}, "message": "Incident opened"}


@router.post("/incidents/{incident_id}/resolve", response_model=dict)
def resolve_incident(incident_id: uuid.UUID, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("incident.manage"))):
    row = db.get(IncidentRecord, incident_id)
    if not row:
        raise HTTPException(404, "Incident not found")
    if row.status == "RESOLVED":
        return {"success": True, "data": {"id": str(row.id), "status": row.status}, "message": "Incident already resolved"}
    row.status, row.resolved_at = "RESOLVED", datetime.now(timezone.utc)
    audit(db, actor, "incident.resolved", "incident_records", str(row.id), request, after={"status": row.status})
    db.commit()
    return {"success": True, "data": {"id": str(row.id), "status": row.status}, "message": "Incident resolved"}


@router.post("/staff", response_model=dict, status_code=201)
def create_staff(payload: StaffCreateRequest, request: Request, db: Session = Depends(get_db), actor=Depends(require_permission("staff.manage")), _step_up=Depends(require_step_up("staff_manage"))):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "A user with this email already exists")
    staff = User(id=uuid.uuid4(), email=email, full_name=payload.full_name.strip(), password_hash=hash_password(payload.password), role=payload.role, is_active=True, account_status="ACTIVE")
    db.add(staff)
    db.flush()
    audit(db, actor, "staff.created", "users", str(staff.id), request, after={"role": staff.role, "email_present": True}, reason=payload.reason)
    db.commit()
    return {"success": True, "data": {"id": str(staff.id), "role": staff.role, "email": staff.email}, "message": "Staff account created"}
