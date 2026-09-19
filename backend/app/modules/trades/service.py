import hashlib
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from io import BytesIO

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.domain_contracts import TRADE_TRANSITIONS, transition_allowed
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.s3 import delete_file, generate_presigned_url, get_s3_client, upload_file
from app.models import (
    AuditLog,
    BuyerProfile,
    Evidence,
    OutboxEvent,
    Payment,
    StorageFacility,
    TradeEvent,
    TradeStorageRequest,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.notifications.service import NotificationService


def gen_trade_public_id(db: Session) -> str:
    return f"KL-TRD-{uuid.uuid4().hex[:10].upper()}"


def _get_transaction(db: Session, identifier: str, *, for_update: bool = False) -> Transaction:
    query = db.query(Transaction)
    try:
        uid = uuid.UUID(identifier)
        query = query.filter(Transaction.id == uid)
    except ValueError:
        query = query.filter(Transaction.public_id == identifier)
    if for_update:
        query = query.with_for_update()
    txn = query.first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return txn


def _ensure_participant_or_admin(txn: Transaction, user: User):
    if user.role.lower() in ("admin", "operator"):
        return
    if str(user.id) not in (str(txn.buyer_id), str(txn.seller_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not a participant in this trade",
        )


def derive_next_action(
    txn: Transaction,
    user: User,
    *,
    has_payment_report: bool = False,
    payment_report_needs_ack: bool = False,
) -> dict:
    st = (txn.status or "").upper()
    uid_str = str(user.id)
    is_buyer = uid_str == str(txn.buyer_id)
    is_seller = uid_str == str(txn.seller_id)
    is_admin_or_op = user.role.lower() in ("admin", "operator")

    if st in ("CREATED", "PAYMENT_PENDING", "OFFER_ACCEPTED"):
        if has_payment_report and payment_report_needs_ack:
            return {
                "action_required": True,
                "responsible_role": "seller",
                "action_title": "Review buyer payment report",
                "action_description": "The buyer entered a payment reference. It has not been verified by a payment provider.",
                "action_type": "ACKNOWLEDGE_PAYMENT_REPORT",
                "is_current_user_action": is_seller or is_admin_or_op,
            }
        if has_payment_report:
            return {
                "action_required": False,
                "responsible_role": "none",
                "action_title": "Payment report acknowledged",
                "action_description": "The seller acknowledged the reported receipt. No payment provider has verified settlement.",
                "action_type": "NONE",
                "is_current_user_action": False,
            }
        return {
            "action_required": True,
            "responsible_role": "buyer",
            "action_title": "Report payment only if sent",
            "action_description": "No payment provider is connected. Entering a reference will not verify or move money.",
            "action_type": "REPORT_PAYMENT_SENT",
            "is_current_user_action": is_buyer or is_admin_or_op,
        }
    elif st == "PAYMENT_CONFIRMED":
        return {
            "action_required": True,
            "responsible_role": "seller",
            "action_title": "Prepare Produce for Dispatch",
            "action_description": "The trade record is ready for seller action. Payment status is shown separately.",
            "action_type": "PREPARE_DISPATCH",
            "is_current_user_action": is_seller or is_admin_or_op,
        }
    elif st == "READY_FOR_DISPATCH":
        return {
            "action_required": True,
            "responsible_role": "seller",
            "action_title": "Mark as Dispatched",
            "action_description": "Produce is packed and ready. Mark shipment as dispatched towards destination.",
            "action_type": "DISPATCH",
            "is_current_user_action": is_seller or is_admin_or_op,
        }
    elif st == "IN_TRANSIT":
        return {
            "action_required": True,
            "responsible_role": "buyer",
            "action_title": "Confirm Delivery Arrival",
            "action_description": "The seller reported dispatch. Buyer receipt has not been confirmed by a carrier.",
            "action_type": "CONFIRM_DELIVERY",
            "is_current_user_action": is_buyer or is_admin_or_op,
        }
    elif st == "DELIVERED":
        return {
            "action_required": True,
            "responsible_role": "buyer",
            "action_title": "Review reported delivery",
            "action_description": "A delivery state was recorded by a participant. Payment or settlement is not implied.",
            "action_type": "FINALIZE_ACCEPTANCE",
            "is_current_user_action": is_buyer or is_admin_or_op,
        }
    elif st == "COMPLETED":
        return {
            "action_required": False,
            "responsible_role": "none",
            "action_title": "Trade operations complete",
            "action_description": "Trade activity is marked complete. Payment status remains separate and may be unavailable.",
            "action_type": "NONE",
            "is_current_user_action": False,
        }
    elif st == "DISPUTED":
        return {
            "action_required": True,
            "responsible_role": "operator",
            "action_title": "Under Dispute Review",
            "action_description": "A grievance or dispute has been opened for this trade. Operator triage is in progress.",
            "action_type": "DISPUTE_REVIEW",
            "is_current_user_action": is_admin_or_op,
        }
    else:
        return {
            "action_required": False,
            "responsible_role": "none",
            "action_title": "Trade Closed",
            "action_description": f"Trade is currently in {st} status.",
            "action_type": "NONE",
            "is_current_user_action": False,
        }


def get_or_create_term_snapshot(db: Session, txn: Transaction) -> TradeTermSnapshot | None:
    """Compatibility name; reads only and never reconstructs accepted terms."""
    return db.query(TradeTermSnapshot).filter(TradeTermSnapshot.transaction_id == txn.id).first()


def get_trade_room(db: Session, identifier: str, user: User) -> dict:
    txn = _get_transaction(db, identifier)
    _ensure_participant_or_admin(txn, user)
    snap = get_or_create_term_snapshot(db, txn)

    # Fetch parties
    buyer = db.get(User, txn.buyer_id)
    seller = db.get(User, txn.seller_id)
    buyer_profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == txn.buyer_id).first()
    seller_view = str(user.id) == str(txn.seller_id)

    # The event stream is the only Trade Room timeline. GET never adds events.
    events = (
        db.query(TradeEvent)
        .filter(TradeEvent.transaction_id == txn.id)
        .order_by(TradeEvent.created_at.asc(), TradeEvent.id.asc())
        .all()
    )
    payment_rows = (
        db.query(Payment)
        .filter(Payment.transaction_id == txn.id)
        .order_by(Payment.created_at.asc(), Payment.id.asc())
        .limit(20)
        .all()
    )
    payments = [payment for payment in payment_rows if payment.source_kind == "PARTICIPANT_REPORTED"]
    legacy_unverified_payment_count = sum(payment.source_kind != "PARTICIPANT_REPORTED" for payment in payment_rows)
    acknowledged_ids = {
        str((event.metadata_json or {}).get("payment_id"))
        for event in events
        if event.event_type == "PAYMENT_RECEIPT_ACKNOWLEDGED"
    }
    payment_status = "LEGACY_RECORD_UNVERIFIED" if legacy_unverified_payment_count else "NO_PROVIDER_DATA"
    if payments:
        all_reports_acknowledged = all(str(payment.id) in acknowledged_ids for payment in payments)
        payment_status = "SELLER_ACKNOWLEDGED_REPORTED" if all_reports_acknowledged else "PARTICIPANT_REPORTED"

    storage_rows = (
        db.query(TradeStorageRequest, StorageFacility)
        .join(StorageFacility, StorageFacility.id == TradeStorageRequest.facility_id)
        .filter(TradeStorageRequest.transaction_id == txn.id)
        .order_by(TradeStorageRequest.created_at.asc())
        .all()
    )
    storage_requests = [
        {
            "id": str(request_row.id),
            "facility_name": facility.name,
            "quantity": request_row.quantity,
            "unit": request_row.unit,
            "status": "REQUESTED",
            "confirmation_status": "PENDING_FACILITY_CONFIRMATION",
            "requested_at": request_row.created_at,
        }
        for request_row, facility in storage_rows
    ]
    evidence_rows = (
        db.query(Evidence)
        .filter(Evidence.transaction_id == txn.id)
        .order_by(Evidence.created_at.asc(), Evidence.id.asc())
        .all()
    )
    evidence_items = []
    for evidence in evidence_rows:
        signed_url = None
        if get_s3_client():
            try:
                signed_url = generate_presigned_url(evidence.s3_key)
            except Exception:
                signed_url = None
        evidence_items.append(
            {
                "id": evidence.id,
                "classification": evidence.classification,
                "provenance_status": evidence.provenance_status,
                "mime_type": evidence.mime_type,
                "file_size_bytes": evidence.file_size_bytes,
                "original_filename": evidence.original_filename,
                "file_hash": evidence.file_hash,
                "uploaded_at": evidence.created_at,
                "url": signed_url,
            }
        )

    quality_events = [event for event in events if event.event_type.startswith("QUALITY_")]
    logistics_events = [event for event in events if event.event_type.startswith("LOGISTICS_")]
    next_action = derive_next_action(
        txn,
        user,
        has_payment_report=bool(payments),
        payment_report_needs_ack=any(str(payment.id) not in acknowledged_ids for payment in payments),
    )
    gross_val = snap.gross_value if snap else None

    return {
        "id": txn.id,
        "public_id": txn.public_id,
        "status": txn.status,
        "created_at": txn.created_at,
        "updated_at": txn.updated_at,
        "buyer": {
            "id": None if seller_view else (buyer.id if buyer else txn.buyer_id),
            "full_name": None if seller_view else (buyer.full_name if buyer else "Unavailable"),
            "business_name": buyer_profile.business_name if buyer_profile else None,
            "role": buyer.role if buyer else "buyer",
            "location": None if seller_view else (buyer.location if buyer else None),
            "district": None if seller_view else (buyer.district if buyer else None),
        },
        "seller": {
            "id": seller.id if seller else txn.seller_id,
            "full_name": seller.full_name if seller else "Unavailable",
            "role": seller.role if seller else "farmer",
            "location": seller.location if seller else None,
            "district": seller.district if seller else None,
        },
        "terms": {
            "crop_name": snap.crop_name,
            "grade": snap.grade,
            "quantity": snap.quantity,
            "unit": snap.unit,
            "price_per_unit": snap.price_per_unit,
            "gross_value": snap.gross_value,
            "estimated_net_realization": snap.estimated_net_realization,
            "delivery_window": snap.delivery_window,
            "pickup_location": snap.pickup_location,
            "delivery_location": snap.delivery_location,
            "created_at": snap.created_at,
        } if snap else None,
        "payment": {
            "status": payment_status,
            "gross_value": gross_val,
            "provider_connected": False,
            "provider_verified": False,
            "legacy_unverified_count": legacy_unverified_payment_count,
            "reports": [
                {
                    "id": payment.id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "reference": payment.provider_reference,
                    "status": payment.status,
                    "source_kind": payment.source_kind,
                    "reported_at": payment.created_at,
                    "reported_by_role": "buyer" if payment.reported_by_id == txn.buyer_id else None,
                    "seller_acknowledged": str(payment.id) in acknowledged_ids,
                }
                for payment in payments
            ],
            "note": "No payment provider is connected. Participant-entered references are not provider-verified and do not prove funds moved. Older payment records have unknown provenance.",
        },
        "logistics": {
            "status": "PARTICIPANT_REPORTED" if logistics_events else "NOT_PROVIDER_CONNECTED",
            "origin": snap.pickup_location if snap else None,
            "destination": snap.delivery_location if snap else None,
            "provider_connected": False,
            "note": "No carrier integration is connected. Timeline updates are participant statements." if logistics_events else "No carrier integration is connected.",
        },
        "quality": {
            "agreed_grade": snap.grade if snap else "UNAVAILABLE",
            "verification_status": "PARTICIPANT_REPORTED" if quality_events else "NOT_VERIFIED",
            "note": "Participant statements and uploads are not a verified assay." if quality_events else "No verified assay is available.",
        },
        "next_action": next_action,
        "storage_requests": storage_requests,
        "evidence": evidence_items,
        "viewer_party": "buyer" if str(user.id) == str(txn.buyer_id) else "seller" if str(user.id) == str(txn.seller_id) else "operator",
        "timeline": [
            {
                "id": ev.id,
                "transaction_id": ev.transaction_id,
                "actor_id": ev.actor_id,
                "actor_role": ev.actor_role,
                "event_type": ev.event_type,
                "from_status": ev.from_status,
                "to_status": ev.to_status,
                "title": ev.title,
                "description": ev.description,
                "source_kind": ev.source_kind,
                "metadata": ev.metadata_json,
                "created_at": ev.created_at,
            }
            for ev in events
        ],
    }


def execute_trade_transition(
    db: Session,
    identifier: str,
    to_status: str,
    user: User,
    request: Request,
    reason: str | None = None,
) -> dict:
    txn = _get_transaction(db, identifier, for_update=True)
    _ensure_participant_or_admin(txn, user)

    old_status = (txn.status or "").upper()
    target_status = to_status.strip().upper()
    is_buyer = str(user.id) == str(txn.buyer_id)
    is_seller = str(user.id) == str(txn.seller_id)
    is_admin_or_op = user.role.lower() in ("admin", "operator")

    if target_status == "PAYMENT_CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment cannot be marked provider-confirmed without a configured payment provider.",
        )

    # Allowed transitions and RBAC rules
    allowed_targets = TRADE_TRANSITIONS.get(old_status, frozenset())
    if not transition_allowed(old_status, target_status, TRADE_TRANSITIONS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state transition from {old_status} to {target_status}. Allowed transitions: {sorted(allowed_targets)}",
        )

    # Role enforcement
    if target_status == "PAYMENT_CONFIRMED" and not (is_buyer or is_admin_or_op):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer or admin can authorize payment.")
    if target_status in ("READY_FOR_DISPATCH", "IN_TRANSIT") and not (is_seller or is_admin_or_op):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the seller or operator can update dispatch status.")
    if target_status == "COMPLETED" and not (is_buyer or is_admin_or_op):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the buyer or admin can confirm completion/acceptance.")
    if target_status == "REFUNDED" and not is_admin_or_op:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an administrator or operator can record a refund.")

    txn.status = target_status
    txn.updated_at = datetime.now(timezone.utc)
    db.flush()

    # Create timeline domain event
    titles = {
        "PAYMENT_PENDING": "Buyer marked payment as pending",
        "READY_FOR_DISPATCH": "Seller marked produce ready for dispatch",
        "IN_TRANSIT": "Seller reported dispatch",
        "DELIVERED": "Buyer confirmed receipt",
        "COMPLETED": "Buyer marked trade operations complete",
    }
    ev = TradeEvent(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        actor_id=user.id,
        actor_role=user.role,
        event_type="DOMAIN_EVENT",
        from_status=old_status,
        to_status=target_status,
        title=titles.get(target_status, f"Trade status changed to {target_status}"),
        description=reason,
        source_kind="PARTICIPANT_REPORTED" if not is_admin_or_op else "OPERATOR_RECORDED",
        metadata_json={"statement": reason} if reason else None,
    )
    db.add(ev)

    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="trade.transition",
            entity="transactions",
            entity_id=str(txn.id),
            before={"status": old_status},
            after={"status": target_status, "reason": reason},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="trades",
            aggregate_id=str(txn.id),
            event_type="trade.status_changed",
            payload={"trade_id": str(txn.id), "from_status": old_status, "to_status": target_status},
        )
    )

    # Notify counterparty
    recipient_id = txn.seller_id if is_buyer else txn.buyer_id
    NotificationService.create_notification(
        db=db,
        user_id=recipient_id,
        type_="trade_update",
        title="Trade Status Updated",
        message=f"Trade {txn.public_id or 'record'} status changed from {old_status} to {target_status}.",
        related_id=txn.id,
        outbox=True,
    )

    db.commit()
    return get_trade_room(db, str(txn.id), user)


def add_trade_note(db: Session, identifier: str, user: User, note: str, request: Request) -> TradeEvent:
    txn = _get_transaction(db, identifier)
    _ensure_participant_or_admin(txn, user)

    ev = TradeEvent(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        actor_id=user.id,
        actor_role=user.role,
        event_type="USER_NOTE",
        from_status=txn.status,
        to_status=txn.status,
        title=f"Note from {user.full_name} ({user.role.title()})",
        description=note,
        source_kind="PARTICIPANT_REPORTED",
    )
    db.add(ev)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="trade.note_added",
            entity="transactions",
            entity_id=str(txn.id),
            after={"note_preview": note[:100]},
            request_id=rid,
        )
    )
    db.commit()
    db.refresh(ev)
    return ev


def _operation_key(request: Request, user: User) -> str:
    raw_key = (request.headers.get("Idempotency-Key") or "").strip()
    if not 8 <= len(raw_key) <= 200:
        raise HTTPException(status_code=428, detail="A valid Idempotency-Key is required for this action")
    identity = f"{user.id}:{request.method}:{request.url.path}:{raw_key}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _begin_operation(db: Session, identifier: str, user: User, request: Request):
    txn = _get_transaction(db, identifier, for_update=True)
    _ensure_participant_or_admin(txn, user)
    cached = check_idempotency(request, db, user=user)
    if cached and cached.response_body is not None:
        return txn, None, cached.response_body
    return txn, _operation_key(request, user), None


def _record_operation(
    db: Session,
    txn: Transaction,
    user: User,
    request: Request,
    *,
    operation_key: str,
    event_type: str,
    title: str,
    description: str | None,
    metadata: dict,
    status_code: int = 201,
) -> dict:
    event = TradeEvent(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        actor_id=user.id,
        actor_role=user.role,
        event_type=event_type,
        from_status=txn.status,
        to_status=txn.status,
        title=title,
        description=description,
        source_kind="PARTICIPANT_REPORTED",
        metadata_json=metadata,
        idempotency_key=operation_key,
    )
    db.add(event)
    db.flush()
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action=f"trade.{event_type.lower()}",
            entity="transactions",
            entity_id=str(txn.id),
            after={"event_id": str(event.id), "source_kind": "PARTICIPANT_REPORTED"},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="trades",
            aggregate_id=str(txn.id),
            event_type="trade.operations_event_recorded",
            payload={"trade_id": str(txn.id), "event_id": str(event.id), "event_type": event_type},
        )
    )
    body = {
        "success": True,
        "data": {
            "id": str(event.id),
            "event_type": event_type,
            "source_kind": "PARTICIPANT_REPORTED",
            "created_at": event.created_at.isoformat() if event.created_at else None,
        },
        "message": "Statement recorded in the trade timeline; this is not provider verification.",
        "request_id": rid,
    }
    save_idempotency(request, db, status_code, body, user=user, commit=False)
    db.commit()
    return body


def report_payment(db: Session, identifier: str, user: User, request: Request, amount: Decimal, reference: str) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    if str(user.id) != str(txn.buyer_id):
        raise HTTPException(status_code=403, detail="Only the buyer can report a payment they sent")
    snap = get_or_create_term_snapshot(db, txn)
    gross = Decimal(str(snap.gross_value)) if snap is not None else None
    if gross is None:
        raise HTTPException(status_code=409, detail="Accepted trade terms are unavailable; payment cannot be reported")
    if amount > gross:
        raise HTTPException(status_code=422, detail="Reported amount must not exceed the recorded trade gross")
    clean_reference = reference.strip()
    if not clean_reference or any(ord(char) < 32 for char in clean_reference):
        raise HTTPException(status_code=422, detail="Enter a valid payment reference")
    payment = Payment(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        provider="participant_reported",
        provider_reference=clean_reference,
        amount=amount,
        currency="INR",
        status="BUYER_REPORTED_SENT",
        source_kind="PARTICIPANT_REPORTED",
        reported_by_id=user.id,
        idempotency_key=operation_key,
    )
    db.add(payment)
    db.flush()
    return _record_operation(
        db,
        txn,
        user,
        request,
        operation_key=operation_key,
        event_type="PAYMENT_REPORTED_SENT",
        title="Buyer reported payment sent",
        description="A buyer-entered payment reference was submitted. No provider verification was performed.",
        metadata={"payment_id": str(payment.id), "amount": str(amount), "currency": "INR"},
    )


def acknowledge_payment_report(
    db: Session, identifier: str, payment_id: uuid.UUID, user: User, request: Request
) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    if str(user.id) != str(txn.seller_id):
        raise HTTPException(status_code=403, detail="Only the seller can acknowledge a reported receipt")
    payment = db.query(Payment).filter(Payment.id == payment_id, Payment.transaction_id == txn.id).first()
    if not payment or payment.source_kind != "PARTICIPANT_REPORTED":
        raise HTTPException(status_code=404, detail="Participant payment report not found")
    prior = (
        db.query(TradeEvent)
        .filter(TradeEvent.transaction_id == txn.id, TradeEvent.event_type == "PAYMENT_RECEIPT_ACKNOWLEDGED")
        .all()
    )
    if any(str((event.metadata_json or {}).get("payment_id")) == str(payment.id) for event in prior):
        raise HTTPException(status_code=409, detail="This payment report was already acknowledged")
    return _record_operation(
        db,
        txn,
        user,
        request,
        operation_key=operation_key,
        event_type="PAYMENT_RECEIPT_ACKNOWLEDGED",
        title="Seller acknowledged the reported receipt",
        description="This records the seller's statement only. It is not bank or payment-provider verification.",
        metadata={"payment_id": str(payment.id), "provider_verified": False},
    )


def record_quality_report(db: Session, identifier: str, user: User, request: Request, kind: str, details: str, attributes: dict[str, str]) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    cleaned: dict[str, str] = {}
    for key, value in attributes.items():
        safe_key, safe_value = key.strip(), value.strip()
        if not safe_key or len(safe_key) > 60 or len(safe_value) > 200 or any(ord(char) < 32 for char in safe_key + safe_value):
            raise HTTPException(status_code=422, detail="Quality attributes contain invalid text")
        cleaned[safe_key] = safe_value
    event_type = "QUALITY_CLAIM" if kind == "PARTICIPANT_CLAIM" else "QUALITY_OBSERVATION"
    return _record_operation(
        db,
        txn,
        user,
        request,
        operation_key=operation_key,
        event_type=event_type,
        title="Participant quality statement recorded",
        description=details.strip(),
        metadata={"claim_kind": kind, "attributes": cleaned, "assay_verified": False},
    )


def record_weighment(db: Session, identifier: str, user: User, request: Request, gross: Decimal, tare: Decimal, unit: str) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    snap = get_or_create_term_snapshot(db, txn)
    if snap is None:
        raise HTTPException(status_code=409, detail="Accepted trade quantity is unavailable")
    if unit.strip().casefold() != snap.unit.strip().casefold():
        raise HTTPException(status_code=422, detail="Weighment unit must match the agreed trade unit")
    if gross <= tare:
        raise HTTPException(status_code=422, detail="Gross quantity must be greater than tare quantity")
    net = gross - tare
    contracted = Decimal(str(snap.quantity))
    return _record_operation(
        db,
        txn,
        user,
        request,
        operation_key=operation_key,
        event_type="WEIGHMENT_REPORTED",
        title="Participant reported weighment",
        description="Net quantity was calculated by KrishiLink from the submitted gross and tare values. This is not a verified weighbridge record.",
        metadata={
            "gross_quantity": str(gross),
            "tare_quantity": str(tare),
            "net_quantity": str(net),
            "contracted_quantity": str(contracted),
            "difference_quantity": str(abs(net - contracted)),
            "unit": snap.unit,
            "calculation_source": "SERVER_DECIMAL",
        },
    )


def record_logistics_update(
    db: Session,
    identifier: str,
    user: User,
    request: Request,
    kind: str,
    details: str | None,
    evidence_id: uuid.UUID | None,
) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    role = user.role.lower()
    is_buyer = str(user.id) == str(txn.buyer_id)
    is_seller = str(user.id) == str(txn.seller_id)
    allowed = {
        "PICKUP_REPORTED": is_seller,
        "DISPATCH_REPORTED": is_seller,
        "DELIVERY_REPORTED": is_seller,
        "RECEIPT_CONFIRMED": is_buyer,
    }
    if not allowed.get(kind, False):
        raise HTTPException(status_code=403, detail="This logistics statement is not available to your trade role")
    if evidence_id:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.transaction_id == txn.id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Trade evidence not found")
    titles = {
        "PICKUP_REPORTED": "Seller reported pickup",
        "DISPATCH_REPORTED": "Seller reported dispatch",
        "DELIVERY_REPORTED": "Seller reported delivery",
        "RECEIPT_CONFIRMED": "Buyer confirmed receipt",
    }
    return _record_operation(
        db,
        txn,
        user,
        request,
        operation_key=operation_key,
        event_type=f"LOGISTICS_{kind}",
        title=titles[kind],
        description=details,
        metadata={"assertion_by": role, "evidence_id": str(evidence_id) if evidence_id else None, "provider_confirmed": False},
    )


def request_trade_storage(
    db: Session,
    identifier: str,
    user: User,
    request: Request,
    facility_id: uuid.UUID,
    quantity: Decimal,
    unit: str,
) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    snap = get_or_create_term_snapshot(db, txn)
    if snap is None or unit.strip().casefold() != snap.unit.strip().casefold():
        raise HTTPException(status_code=422, detail="Storage request unit must match the agreed trade unit")
    if quantity > Decimal(str(snap.quantity)):
        raise HTTPException(status_code=422, detail="Storage request exceeds the agreed trade quantity")
    facility = (
        db.query(StorageFacility)
        .filter(
            StorageFacility.id == facility_id,
            StorageFacility.status == "ACTIVE",
            StorageFacility.verification_status == "VERIFIED",
        )
        .first()
    )
    if not facility:
        raise HTTPException(status_code=404, detail="No currently verified active facility was found")
    if facility.source_kind == "DEMO_SYNTHETIC" and not settings.demo_mode:
        raise HTTPException(status_code=404, detail="No currently verified active facility was found")
    storage_request = TradeStorageRequest(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        facility_id=facility.id,
        requested_by_id=user.id,
        quantity=quantity,
        unit=snap.unit,
        status="REQUESTED",
        idempotency_key=operation_key,
    )
    db.add(storage_request)
    db.flush()
    return _record_operation(
        db,
        txn,
        user,
        request,
        operation_key=operation_key,
        event_type="STORAGE_REQUESTED",
        title="Storage request sent; facility confirmation pending",
        description="This request does not reserve capacity. The facility has not confirmed availability or price.",
        metadata={"storage_request_id": str(storage_request.id), "facility_id": str(facility.id), "is_demo": facility.source_kind == "DEMO_SYNTHETIC"},
    )


def upload_trade_evidence(
    db: Session,
    identifier: str,
    user: User,
    request: Request,
    classification: str,
    content: bytes,
    mime_type: str,
    filename: str,
) -> dict:
    txn, operation_key, cached = _begin_operation(db, identifier, user, request)
    if cached:
        return cached
    allowed = {"QUALITY_PHOTO", "WEIGHMENT_DOCUMENT", "DELIVERY_DOCUMENT", "OTHER_TRADE_EVIDENCE"}
    if classification not in allowed:
        raise HTTPException(status_code=422, detail="Unsupported trade evidence classification")
    if not get_s3_client():
        raise HTTPException(status_code=503, detail="Evidence storage is not configured")

    evidence_id = uuid.uuid4()
    key = f"trades/{txn.id}/evidence/{evidence_id}/{filename}"
    try:
        upload_file(BytesIO(content), key, mime_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Evidence storage could not accept the file") from exc

    evidence = Evidence(
        id=evidence_id,
        transaction_id=txn.id,
        uploader_id=user.id,
        s3_key=key,
        file_hash=hashlib.sha256(content).hexdigest(),
        mime_type=mime_type,
        classification=classification,
        provenance_status="PARTICIPANT_SUBMITTED",
        file_size_bytes=len(content),
        original_filename=filename,
        metadata_json={"source_kind": "PARTICIPANT_REPORTED", "provider_verified": False},
    )
    db.add(evidence)
    try:
        db.flush()
        result = _record_operation(
            db,
            txn,
            user,
            request,
            operation_key=operation_key,
            event_type="EVIDENCE_SUBMITTED",
            title="Participant submitted trade evidence",
            description="The file was uploaded by a trade participant. Its contents have not been independently verified.",
            metadata={
                "evidence_id": str(evidence.id),
                "classification": classification,
                "provenance_status": "PARTICIPANT_SUBMITTED",
                "mime_type": mime_type,
                "file_size_bytes": len(content),
                "sha256": evidence.file_hash,
            },
        )
    except Exception:
        db.rollback()
        try:
            delete_file(key)
        except Exception:
            pass
        raise
    result["data"]["evidence_id"] = str(evidence.id)
    # The event response is already cached transactionally. Keep its body aligned
    # with the returned response for idempotent retries.
    cached_idempotency = check_idempotency(request, db, user=user)
    if cached_idempotency:
        cached_idempotency.response_body = result
        db.commit()
    return result
