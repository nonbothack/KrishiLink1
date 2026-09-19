import hashlib
import uuid
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.domain_contracts import GRIEVANCE_TRANSITIONS, TRADE_TRANSITIONS, transition_allowed
from app.core.evidence_files import read_validated_evidence
from app.core.rate_limit import rate_limit
from app.core.s3 import delete_file, generate_presigned_url, get_s3_client, upload_file
from app.models import AuditLog, Dispute, Evidence, OutboxEvent, TradeEvent, Transaction, User
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/disputes", tags=["disputes"])


def _can_access_dispute(db: Session, dispute: Dispute, user: User) -> bool:
    if user.role.lower() in ("admin", "operator") or dispute.raised_by == user.id:
        return True
    if not dispute.transaction_id:
        return False
    transaction = db.get(Transaction, dispute.transaction_id)
    return bool(transaction and user.id in (transaction.buyer_id, transaction.seller_id))


class CreateDisputeRequest(BaseModel):
    transaction_id: str | None = None
    reason: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    category: str | None = "General Inquiry"
    priority: str | None = "MEDIUM"


class UpdateDisputeStatusRequest(BaseModel):
    status: str
    resolution: str | None = None


class EvidenceRequest(BaseModel):
    s3_key: str
    file_hash: str
    mime_type: str | None = None


@router.post("", response_model=dict, status_code=201)
@rate_limit(max_requests=15, window_seconds=60, key_prefix="rl_dispute")
def create_dispute(
    data: CreateDisputeRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    txn_id = None
    if data.transaction_id:
        try:
            txn_id = uuid.UUID(data.transaction_id)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="Invalid trade reference") from exc
        txn = db.query(Transaction).filter(Transaction.id == txn_id).with_for_update().first()
        if not txn:
            raise HTTPException(status_code=404, detail="Trade not found")
        if user.role.lower() not in ("admin", "operator") and user.id not in (txn.buyer_id, txn.seller_id):
            raise HTTPException(status_code=403, detail="Only a trade participant can raise a trade grievance")

    d = Dispute(
        id=uuid.uuid4(),
        transaction_id=txn_id,
        raised_by=user.id,
        reason=f"[{data.category or 'General'}] {data.reason}",
        description=data.description,
        status="OPEN",
    )
    db.add(d)

    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="dispute.create",
            entity="disputes",
            entity_id=str(d.id),
            after={"reason": d.reason, "status": d.status},
            request_id=rid,
        )
    )

    if txn_id:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).with_for_update().first()
        if txn:
            old_trade_status = txn.status
            if transition_allowed(txn.status, "DISPUTED", TRADE_TRANSITIONS):
                txn.status = "DISPUTED"
                txn.updated_at = datetime.now(timezone.utc)
            db.add(
                TradeEvent(
                    transaction_id=txn.id,
                    actor_id=user.id,
                    actor_role=user.role,
                    event_type="DISPUTE_OPENED",
                    from_status=old_trade_status,
                    to_status=txn.status,
                    title="Trade grievance opened",
                    description="A participant opened a grievance linked to this trade.",
                    source_kind="PLATFORM_RECORDED",
                    metadata_json={"dispute_id": str(d.id), "status": d.status},
                )
            )
            db.add(
                OutboxEvent(
                    aggregate="trades",
                    aggregate_id=str(txn.id),
                    event_type="trade.dispute_opened",
                    payload={"trade_id": str(txn.id), "dispute_id": str(d.id), "from_status": old_trade_status, "to_status": txn.status},
                )
            )
            counterparty = txn.seller_id if user.id == txn.buyer_id else txn.buyer_id
            if counterparty != user.id:
                NotificationService.create_notification(
                    db=db,
                    user_id=counterparty,
                    type_="dispute_update",
                    title="A trade grievance was opened",
                    message=f"A participant opened a grievance for trade {txn.public_id or 'record'}.",
                    related_id=d.id,
                    outbox=True,
                )

    db.commit()
    db.refresh(d)
    return {
        "success": True,
        "data": {
            "id": str(d.id),
            "reason": d.reason,
            "description": d.description,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        },
        "message": "Support ticket created successfully",
        "request_id": rid,
    }


@router.get("", response_model=dict)
def list_disputes(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Dispute)
    if user.role.lower() not in ("admin", "operator"):
        participant_trade_ids = select(Transaction.id).where(
            or_(Transaction.buyer_id == user.id, Transaction.seller_id == user.id)
        )
        q = q.filter(or_(Dispute.raised_by == user.id, Dispute.transaction_id.in_(participant_trade_ids)))
    items = q.order_by(Dispute.created_at.desc()).all()
    data = [
        {
            "id": str(d.id),
            "ticket_number": f"KL-TKT-{str(d.id)[:8].upper()}",
            "reason": d.reason,
            "description": d.description,
            "status": d.status,
            "resolution": d.resolution,
            "transaction_id": str(d.transaction_id) if d.transaction_id else None,
            "raised_by": str(d.raised_by),
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in items
    ]
    return {
        "success": True,
        "data": data,
        "message": f"{len(data)} support tickets",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{dispute_id}", response_model=dict)
def get_dispute(
    dispute_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    d = None
    try:
        u = uuid.UUID(dispute_id)
        d = db.query(Dispute).filter(Dispute.id == u).first()
    except (ValueError, TypeError):
        pass

    if not d:
        raise HTTPException(status_code=404, detail="Dispute or support ticket not found")

    if not _can_access_dispute(db, d, user):
        raise HTTPException(status_code=403, detail="Forbidden: You cannot access this grievance")

    ev_items = db.query(Evidence).filter(Evidence.dispute_id == d.id).all()
    evidence_list = []
    for ev in ev_items:
        url = None
        if get_s3_client():
            try:
                url = generate_presigned_url(ev.s3_key)
            except Exception:
                url = None
        evidence_list.append(
            {
                "id": str(ev.id),
                "filename": ev.original_filename or "Evidence file",
                "classification": ev.classification,
                "provenance_status": ev.provenance_status,
                "mime_type": ev.mime_type,
                "file_size_bytes": ev.file_size_bytes,
                "url": url,
            }
        )

    return {
        "success": True,
        "data": {
            "id": str(d.id),
            "ticket_number": f"KL-TKT-{str(d.id)[:8].upper()}",
            "reason": d.reason,
            "description": d.description,
            "status": d.status,
            "resolution": d.resolution,
            "transaction_id": str(d.transaction_id) if d.transaction_id else None,
            "evidence": evidence_list,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        },
        "message": "Ticket details",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{dispute_id}/status", response_model=dict)
def update_dispute_status(
    dispute_id: str,
    data: UpdateDisputeStatusRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Restrict status changes to admin or operator
    if user.role.lower() not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Forbidden: Only administrators can update dispute status")

    try:
        u = uuid.UUID(dispute_id)
        d = db.query(Dispute).filter(Dispute.id == u).first()
    except (ValueError, TypeError):
        d = None

    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found")

    new_status = data.status.upper()
    if new_status in ("RESOLVED", "REJECTED") and not (data.resolution or "").strip():
        raise HTTPException(status_code=422, detail="A resolution reason is required for this grievance status")
    if not transition_allowed(d.status, new_status, GRIEVANCE_TRANSITIONS):
        raise HTTPException(status_code=409, detail=f"Invalid grievance transition: {d.status} -> {new_status}")
    previous_status = d.status
    d.status = new_status
    if data.resolution:
        d.resolution = data.resolution
    d.operator_id = user.id
    d.updated_at = datetime.now(timezone.utc)

    if d.transaction_id:
        txn = db.query(Transaction).filter(Transaction.id == d.transaction_id).with_for_update().first()
        if txn:
            db.add(
                TradeEvent(
                    transaction_id=txn.id,
                    actor_id=user.id,
                    actor_role=user.role,
                    event_type="DISPUTE_STATUS_CHANGED",
                    from_status=txn.status,
                    to_status=txn.status,
                    title=f"Grievance status changed to {new_status.replace('_', ' ').title()}",
                    description=(data.resolution or "").strip() or None,
                    source_kind="OPERATOR_RECORDED",
                    metadata_json={
                        "dispute_id": str(d.id),
                        "from_dispute_status": previous_status,
                        "to_dispute_status": new_status,
                    },
                )
            )
            db.add(
                OutboxEvent(
                    aggregate="trades",
                    aggregate_id=str(txn.id),
                    event_type="trade.dispute_status_changed",
                    payload={"trade_id": str(txn.id), "dispute_id": str(d.id), "status": new_status},
                )
            )

    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="dispute.update_status",
            entity="disputes",
            entity_id=str(d.id),
            after={"status": d.status, "resolution": d.resolution},
            request_id=rid,
        )
    )

    # Send persistent notification to ticket creator
    NotificationService.create_notification(
        db=db,
        user_id=d.raised_by,
        type_="support_update",
        title="Support Ticket Updated",
        message=f"Your ticket '{d.reason}' is now {new_status}. {data.resolution or ''}".strip(),
        related_id=d.id,
        outbox=True,
    )

    db.commit()
    return {
        "success": True,
        "data": {"id": str(d.id), "status": d.status, "resolution": d.resolution},
        "message": f"Ticket status updated to {d.status}",
        "request_id": rid,
    }


@router.post("/{dispute_id}/evidence", response_model=dict)
def add_evidence(
    dispute_id: str,
    data: EvidenceRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # A client-provided key/hash is not evidence provenance. Require upload through
    # the server, which validates the bytes and records the computed hash/uploader.
    try:
        dispute_uuid = uuid.UUID(dispute_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=404, detail="Dispute not found") from exc
    dispute = db.query(Dispute).filter(Dispute.id == dispute_uuid).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if not _can_access_dispute(db, dispute, user):
        raise HTTPException(status_code=403, detail="Forbidden: You cannot upload evidence to this grievance")
    raise HTTPException(status_code=410, detail="Upload the file through the evidence upload endpoint")


@router.post("/{dispute_id}/evidence/upload", response_model=dict)
async def upload_evidence(
    dispute_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        u = uuid.UUID(dispute_id)
        d = db.query(Dispute).filter(Dispute.id == u).first()
    except (ValueError, TypeError):
        d = None

    if not d:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if not _can_access_dispute(db, d, user):
        raise HTTPException(status_code=403, detail="Forbidden: You cannot upload evidence to this grievance")
    content, content_type, safe_filename = await read_validated_evidence(file)

    client = get_s3_client()
    if not client:
        raise HTTPException(status_code=503, detail="Storage service unavailable")

    evidence_id = uuid.uuid4()
    key = f"disputes/{d.id}/evidence/{evidence_id}/{safe_filename}"
    try:
        upload_file(BytesIO(content), key, content_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Evidence storage could not accept the file") from exc

    ev = Evidence(
        id=evidence_id,
        dispute_id=d.id,
        transaction_id=d.transaction_id,
        uploader_id=user.id,
        s3_key=key,
        file_hash=hashlib.sha256(content).hexdigest(),
        mime_type=content_type,
        classification="DISPUTE_EVIDENCE",
        provenance_status="PARTICIPANT_SUBMITTED",
        file_size_bytes=len(content),
        original_filename=safe_filename,
        metadata_json={"source_kind": "PARTICIPANT_REPORTED", "provider_verified": False},
    )
    db.add(ev)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    if d.transaction_id:
        db.add(
            TradeEvent(
                transaction_id=d.transaction_id,
                actor_id=user.id,
                actor_role=user.role,
                event_type="EVIDENCE_SUBMITTED",
                from_status=None,
                to_status=None,
                title="Participant submitted grievance evidence",
                description="The uploaded file is participant-submitted and has not been independently verified.",
                source_kind="PARTICIPANT_REPORTED",
                metadata_json={"dispute_id": str(d.id), "evidence_id": str(ev.id), "sha256": ev.file_hash},
            )
        )
        db.add(
            OutboxEvent(
                aggregate="trades",
                aggregate_id=str(d.transaction_id),
                event_type="trade.evidence_submitted",
                payload={"trade_id": str(d.transaction_id), "dispute_id": str(d.id), "evidence_id": str(ev.id)},
            )
        )
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="dispute.evidence_uploaded",
            entity="evidence",
            entity_id=str(ev.id),
            after={"dispute_id": str(d.id), "classification": ev.classification, "file_hash": ev.file_hash},
            request_id=rid,
        )
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        try:
            delete_file(key)
        except Exception:
            pass
        raise

    try:
        url = generate_presigned_url(key)
    except Exception:
        url = None
    return {
        "success": True,
        "data": {"id": str(ev.id), "classification": ev.classification, "provenance_status": ev.provenance_status, "url": url},
        "message": "Evidence uploaded",
        "request_id": rid,
    }
