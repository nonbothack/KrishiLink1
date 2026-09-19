import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.domain_contracts import OFFER_TRANSITIONS, transition_allowed
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.rate_limit import rate_limit
from app.models import (
    AuditLog,
    BuyerProfile,
    BuyerRequirement,
    Crop,
    Lot,
    Offer,
    OutboxEvent,
    Reservation,
    TradeEvent,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.fpo.service import FPOService
from app.modules.lots.units import UNIT_TO_QUINTAL
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/offers", tags=["offers"])


class CreateOfferRequest(BaseModel):
    lot_id: str
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    price_per_unit: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    unit: str = "quintal"
    message: str | None = None
    expires_at: datetime | None = None
    buyer_requirement_id: str | None = None


class CounterRequest(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    price_per_unit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    unit: str | None = None
    message: str | None = None


class RejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=80)


def _ensure_buyer(user: User):
    if user.role.lower() not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyers can create offers")


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _normalized_terms(crop: Crop | None, quantity: Decimal, price: Decimal, unit: str):
    unit = unit.strip().lower()
    supported = {str(value).strip().lower() for value in (crop.valid_units or [crop.unit or "quintal"])} if crop else {"quintal"}
    factor = UNIT_TO_QUINTAL.get(unit)
    if not factor or unit not in supported:
        raise HTTPException(status_code=422, detail="Offer unit is not supported for this crop")
    canonical_qty = quantity * factor
    if canonical_qty.quantize(Decimal("0.01")) != canonical_qty:
        raise HTTPException(status_code=422, detail="Offer quantity is too precise for quintals")
    canonical_price = (price / factor).quantize(Decimal("0.01"))
    if canonical_qty <= 0 or canonical_price <= 0 or canonical_qty > Decimal("1000000"):
        raise HTTPException(status_code=422, detail="Offer quantity or price is outside the supported range")
    if canonical_qty * canonical_price > Decimal("9999999999.99"):
        raise HTTPException(status_code=422, detail="Offer gross exceeds the supported currency precision")
    return canonical_qty, canonical_price


@router.post("", response_model=dict, status_code=201)
@rate_limit(max_requests=30, window_seconds=60, key_prefix="rl_offer")
def create_offer(
    data: CreateOfferRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_buyer(user)
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body

    lot = db.get(Lot, data.lot_id) or db.query(Lot).filter(Lot.public_id == data.lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    if lot.status.upper() != "PUBLISHED":
        raise HTTPException(status_code=409, detail="This listing is not accepting offers")
    crop = db.get(Crop, lot.crop_id) if lot.crop_id else None
    quantity, price_per_unit = _normalized_terms(crop, data.quantity, data.price_per_unit, data.unit)

    # Lock lot row to prevent race conditions
    lot_locked = db.query(Lot).filter(Lot.id == lot.id).with_for_update().first()
    if not lot_locked or lot_locked.status.upper() != "PUBLISHED":
        raise HTTPException(status_code=409, detail="This listing is no longer accepting offers")
    if quantity > Decimal(str(lot_locked.quantity)):
        raise HTTPException(status_code=409, detail="Offer quantity exceeds lot quantity")
    requirement = None
    if data.buyer_requirement_id:
        try:
            requirement_id = uuid.UUID(data.buyer_requirement_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid requirement")
        requirement = db.query(BuyerRequirement).filter(
            BuyerRequirement.id == requirement_id, BuyerRequirement.buyer_id == user.id
        ).with_for_update().first()
        if not requirement or requirement.status not in ("ACTIVE", "PARTIALLY_FILLED"):
            raise HTTPException(status_code=409, detail="Requirement is not active")
        if requirement.crop_id and requirement.crop_id != lot_locked.crop_id:
            raise HTTPException(status_code=422, detail="Requirement crop does not match this lot")
        remaining = Decimal(str(requirement.canonical_quantity or requirement.quantity_max or 0)) - Decimal(str(requirement.committed_quantity or 0))
        if quantity > remaining:
            raise HTTPException(status_code=409, detail="Offer quantity exceeds remaining requirement quantity")
    requested_expiry = _utc(data.expires_at)
    if requested_expiry and requested_expiry <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Offer expiry must be in the future")

    offer = Offer(
        id=uuid.uuid4(),
        lot_id=lot_locked.id,
        buyer_id=user.id,
        owner_id=lot_locked.owner_id,
        quantity=quantity,
        price_per_unit=price_per_unit,
        total_value=(quantity * price_per_unit).quantize(Decimal("0.01")),
        message=data.message,
        expires_at=requested_expiry or (datetime.now(timezone.utc) + timedelta(days=3)),
        status="PENDING",
        buyer_requirement_id=requirement.id if requirement else None,
    )
    db.add(offer)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="offer.create",
            entity="offers",
            entity_id=str(offer.id),
            after={"lot_id": str(lot.id), "quantity": str(quantity), "price": str(price_per_unit)},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="offers",
            aggregate_id=str(offer.id),
            event_type="offer.created",
            payload={"offer_id": str(offer.id), "lot_id": str(lot.id)},
        )
    )

    # Notify lot owner (farmer)
    NotificationService.create_notification(
        db=db,
        user_id=lot_locked.owner_id,
        type_="offer_received",
        title="New Offer Received",
        message=f"Received offer for {quantity} quintals of {lot.crop_name}.",
        related_id=offer.id,
        outbox=True,
    )

    db.flush()
    body = {
        "success": True,
        "data": {
            "id": str(offer.id),
            "lot_id": str(offer.lot_id),
            "quantity": str(offer.quantity),
            "price_per_unit": str(offer.price_per_unit),
            "total_value": str(offer.total_value),
            "unit": "quintal",
            "status": offer.status,
            "buyer_requirement_id": str(offer.buyer_requirement_id) if offer.buyer_requirement_id else None,
        },
        "message": "Offer created",
        "request_id": rid,
    }
    save_idempotency(request, db, 201, body, user=user, commit=False)
    db.commit()
    return body


@router.get("", response_model=dict)
def list_offers(
    request: Request,
    db: Session = Depends(get_db),
    lot_id: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    q = db.query(Offer)
    if lot_id:
        lot = db.get(Lot, lot_id) or db.query(Lot).filter(Lot.public_id == lot_id).first()
        if lot:
            q = q.filter(Offer.lot_id == lot.id)
        else:
            q = q.filter(Offer.lot_id == lot_id)
    if status:
        q = q.filter(Offer.status == status.upper())

    if user.role.lower() in ("farmer", "fpo"):
        q = q.filter(Offer.owner_id == user.id)
    elif user.role.lower() == "buyer":
        q = q.filter(Offer.buyer_id == user.id)

    total = q.count()
    items = q.order_by(Offer.created_at.desc(), Offer.id.desc()).offset((page - 1) * limit).limit(limit).all()

    lot_ids = [o.lot_id for o in items if o.lot_id]
    user_ids = list({o.buyer_id for o in items if o.buyer_id} | {o.owner_id for o in items if o.owner_id})
    lots_map = {l.id: l for l in db.query(Lot).filter(Lot.id.in_(lot_ids)).all()} if lot_ids else {}
    profiles_map = {p.user_id: p for p in db.query(BuyerProfile).filter(BuyerProfile.user_id.in_(user_ids)).all()} if user_ids else {}
    transactions_map = {
        transaction.offer_id: transaction
        for transaction in db.query(Transaction).filter(Transaction.offer_id.in_([offer.id for offer in items])).all()
    } if items else {}

    data = []
    for o in items:
        lot = lots_map.get(o.lot_id)
        buyer_profile = profiles_map.get(o.buyer_id)
        transaction = transactions_map.get(o.id)
        total_value = o.total_value if o.total_value is not None else (Decimal(str(o.quantity)) * Decimal(str(o.price_per_unit)))
        data.append(
            {
                "id": str(o.id),
                "lot_id": str(o.lot_id),
                "buyer_id": str(o.buyer_id) if user.role.lower() == "buyer" else None,
                "owner_id": None,
                "quantity": str(o.quantity),
                "unit": lot.unit if lot else "quintal",
                "price_per_unit": str(o.price_per_unit),
                "total_value": str(total_value),
                "status": o.status,
                "message": o.message,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "expires_at": o.expires_at.isoformat() if o.expires_at else None,
                "crop_name": lot.crop_name if lot else "Produce",
                "crop": lot.crop_name if lot else "Produce",
                "lot_public_id": lot.public_id if lot else None,
                "transaction_id": str(transaction.id) if transaction else None,
                "trade_public_id": transaction.public_id if transaction else None,
                "buyer_name": buyer_profile.business_name if buyer_profile else "Buyer account",
                "buyer_verification_status": buyer_profile.business_verification_status if buyer_profile else "UNVERIFIED",
                "seller_label": "Farmer listing",
                "seller_type": "farmer",
                "location": (lot.district or lot.location_text) if lot else None,
                "buyer_requirement_id": str(o.buyer_requirement_id) if o.buyer_requirement_id else None,
                "parent_offer_id": str(o.parent_offer_id) if o.parent_offer_id else None,
            }
        )
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} offers",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{offer_id}", response_model=dict)
def get_offer(offer_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.get(Offer, offer_id)
    if not o:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.role.lower() not in ("admin", "operator") and user.id not in (o.buyer_id, o.owner_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "success": True,
        "data": {
            "id": str(o.id),
            "lot_id": str(o.lot_id),
            "buyer_id": str(o.buyer_id),
            "owner_id": None if user.role.lower() == "buyer" else str(o.owner_id),
            "quantity": str(o.quantity),
            "unit": "quintal",
            "price_per_unit": str(o.price_per_unit),
            "total_value": str(o.total_value) if o.total_value is not None else str(Decimal(str(o.quantity)) * Decimal(str(o.price_per_unit))),
            "status": o.status,
            "message": o.message,
            "expires_at": o.expires_at.isoformat() if o.expires_at else None,
            "parent_offer_id": str(o.parent_offer_id) if o.parent_offer_id else None,
            "buyer_requirement_id": str(o.buyer_requirement_id) if o.buyer_requirement_id else None,
        },
        "message": "OK",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{offer_id}/counter", response_model=dict)
def counter_offer(
    offer_id: str,
    data: CounterRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    try:
        offer_uuid = uuid.UUID(offer_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Offer not found")
    initial = db.get(Offer, offer_uuid)
    if not initial:
        raise HTTPException(status_code=404, detail="Offer not found")
    lot = db.query(Lot).filter(Lot.id == initial.lot_id).with_for_update().first()
    orig = db.query(Offer).filter(Offer.id == offer_uuid).with_for_update().populate_existing().first()
    if not orig:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.id not in (orig.owner_id, orig.buyer_id) and user.role.lower() not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Only an offer participant can counter")
    if user.id == orig.buyer_id and orig.parent_offer_id is None:
        raise HTTPException(status_code=403, detail="Buyer can counter only a farmer counter-offer")
    if not lot or lot.status.upper() != "PUBLISHED":
        raise HTTPException(status_code=409, detail="This lot is no longer accepting counter offers")
    if not transition_allowed(orig.status, "COUNTERED", OFFER_TRANSITIONS):
        raise HTTPException(status_code=409, detail="Offer not in negotiable state")
    if _utc(orig.expires_at) and _utc(orig.expires_at) <= datetime.now(timezone.utc):
        orig.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=409, detail="Offer has expired")
    if data.unit not in (None, "quintal"):
        raise HTTPException(status_code=422, detail="Counter terms use the lot's canonical quintal unit")
    qty = data.quantity if data.quantity is not None else Decimal(str(orig.quantity))
    price = data.price_per_unit if data.price_per_unit is not None else Decimal(str(orig.price_per_unit))
    if not lot or qty > Decimal(str(lot.quantity)):
        raise HTTPException(status_code=409, detail="Counter quantity exceeds the available lot quantity")
    if qty * price > Decimal("9999999999.99"):
        raise HTTPException(status_code=422, detail="Counter gross exceeds the supported currency precision")

    orig.status = "COUNTERED"
    new_offer = Offer(
        id=uuid.uuid4(),
        lot_id=orig.lot_id,
        buyer_id=orig.buyer_id,
        owner_id=orig.owner_id,
        quantity=qty,
        price_per_unit=price,
        total_value=(qty * price).quantize(Decimal("0.01")),
        message=data.message or orig.message,
        status="PENDING",
        parent_offer_id=orig.id,
        buyer_requirement_id=orig.buyer_requirement_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
    )
    db.add(new_offer)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="offer.counter",
            entity="offers",
            entity_id=str(new_offer.id),
            after={"parent": str(orig.id)},
            request_id=rid,
        )
    )

    # Notify the other participant through the transactional outbox.
    NotificationService.create_notification(
        db=db,
        user_id=orig.buyer_id if user.id == orig.owner_id else orig.owner_id,
        type_="counter_offer",
        title="Counter-Offer Received",
        message="A farmer sent a counter offer. Open KrishiLink to review the terms.",
        related_id=new_offer.id,
        outbox=True,
    )

    body = {
        "success": True,
        "data": {"id": str(new_offer.id), "status": new_offer.status, "parent_offer_id": str(orig.id)},
        "message": "Counter offer created",
        "request_id": rid,
    }
    save_idempotency(request, db, 200, body, user=user, commit=False)
    db.commit()
    return body


@router.post("/{offer_id}/accept", response_model=dict)
def accept_offer(
    offer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    try:
        offer_uuid = uuid.UUID(offer_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Offer not found")
    initial = db.get(Offer, offer_uuid)
    if not initial:
        raise HTTPException(status_code=404, detail="Offer not found")
    lot = db.query(Lot).filter(Lot.id == initial.lot_id).with_for_update().first()
    # Reload after the lot lock. The initial existence check may already have
    # placed an Offer instance in SQLAlchemy's identity map; populate_existing
    # prevents a concurrent acceptance from reusing stale PENDING state.
    o = db.query(Offer).filter(Offer.id == offer_uuid).with_for_update().populate_existing().first()
    if not o:
        raise HTTPException(status_code=404, detail="Offer not found")
    buyer_accepting_counter = user.id == o.buyer_id and o.parent_offer_id is not None
    if user.role.lower() not in ("admin", "operator") and user.id != o.owner_id and not buyer_accepting_counter:
        raise HTTPException(status_code=403, detail="Only the lot owner or counter recipient can accept this offer")
    if _utc(o.expires_at) and _utc(o.expires_at) <= datetime.now(timezone.utc):
        if o.status.upper() == "PENDING":
            o.status = "EXPIRED"
            db.commit()
        raise HTTPException(status_code=409, detail="Offer has expired")
    if not transition_allowed(o.status, "ACCEPTED", OFFER_TRANSITIONS):
        raise HTTPException(status_code=409, detail="Offer not pending")

    if lot is None or lot.owner_id != o.owner_id or lot.status.upper() != "PUBLISHED":
        raise HTTPException(status_code=409, detail="This lot is no longer available")
    if Decimal(str(o.quantity)) > Decimal(str(lot.quantity)):
        raise HTTPException(status_code=409, detail="Insufficient lot quantity")
    allocated = (
        db.query(Reservation)
        .filter(Reservation.lot_id == lot.id, Reservation.status == "ACTIVE")
        .with_for_update()
        .all()
    )
    total_alloc = sum((Decimal(str(r.quantity)) for r in allocated), Decimal("0"))
    if total_alloc + Decimal(str(o.quantity)) > Decimal(str(lot.quantity)):
        raise HTTPException(status_code=409, detail="Insufficient remaining quantity")
    requirement = None
    if o.buyer_requirement_id:
        requirement = db.query(BuyerRequirement).filter(BuyerRequirement.id == o.buyer_requirement_id).with_for_update().first()
        if not requirement or requirement.buyer_id != o.buyer_id or requirement.status not in ("ACTIVE", "PARTIALLY_FILLED"):
            raise HTTPException(status_code=409, detail="Linked requirement is no longer active")
        requested = Decimal(str(requirement.canonical_quantity or requirement.quantity_max or 0))
        committed = Decimal(str(requirement.committed_quantity or 0))
        if committed + Decimal(str(o.quantity)) > requested:
            raise HTTPException(status_code=409, detail="Offer would exceed the remaining requirement quantity")

    o.status = "ACCEPTED"
    res = Reservation(
        id=uuid.uuid4(),
        lot_id=lot.id,
        buyer_id=o.buyer_id,
        offer_id=o.id,
        quantity=o.quantity,
        status="ACTIVE",
        reserved_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(res)
    if requirement:
        requirement.committed_quantity = Decimal(str(requirement.committed_quantity or 0)) + Decimal(str(o.quantity))
        requested = Decimal(str(requirement.canonical_quantity or requirement.quantity_max or 0))
        requirement.status = "FILLED" if Decimal(str(requirement.committed_quantity)) >= requested else "PARTIALLY_FILLED"
        requirement.is_active = requirement.status != "FILLED"

    # Automatically initialize Transaction so deal is active on both sides immediately
    gross_val = (Decimal(str(o.quantity)) * Decimal(str(o.price_per_unit))).quantize(Decimal("0.01"))
    txn = Transaction(
        id=uuid.uuid4(),
        public_id=f"KL-TRD-{uuid.uuid4().hex[:10].upper()}",
        lot_id=lot.id,
        buyer_id=o.buyer_id,
        seller_id=lot.owner_id,
        allocation_id=None,
        offer_id=o.id,
        status="CREATED",
        gross_value=gross_val,
    )
    db.add(txn)
    # FPO marketplace lots retain a member-to-receipt ledger.  Allocation is in
    # this same transaction as acceptance, after the lot/offer locks above.
    db.flush()
    # Snapshot the accepted offer and lot facts in the acceptance transaction.
    # Trade Room reads must never reconstruct contractual terms later from mutable rows.
    db.add(
        TradeTermSnapshot(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            lot_id=lot.id,
            buyer_id=o.buyer_id,
            seller_id=lot.owner_id,
            crop_name=lot.crop_name,
            grade=lot.grade,
            quantity=Decimal(str(o.quantity)),
            unit=lot.unit,
            price_per_unit=Decimal(str(o.price_per_unit)),
            gross_value=gross_val,
            estimated_net_realization=None,
            delivery_window=None,
            pickup_location=lot.location_text,
            delivery_location=None,
        )
    )
    db.add(
        TradeEvent(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            actor_id=user.id,
            actor_role=user.role,
            event_type="DOMAIN_EVENT",
            from_status=None,
            to_status="CREATED",
            title="Offer accepted; agreed terms recorded",
            description="The accepted offer and lot facts were snapshotted for this trade.",
            source_kind="PLATFORM_RECORDED",
        )
    )
    FPOService.allocate_trade(
        db,
        lot,
        txn,
        Decimal(str(o.quantity)),
        Decimal(str(o.price_per_unit)),
    )

    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="offer.accept",
            entity="offers",
            entity_id=str(o.id),
            after={"status": "ACCEPTED", "transaction_id": str(txn.id)},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="offers",
            aggregate_id=str(o.id),
            event_type="offer.accepted",
            payload={"offer_id": str(o.id), "lot_id": str(lot.id), "transaction_id": str(txn.id)},
        )
    )
    db.add(
        OutboxEvent(
            aggregate="transactions",
            aggregate_id=str(txn.id),
            event_type="transaction.created",
            payload={"transaction_id": str(txn.id)},
        )
    )

    # Notify buyer of acceptance
    NotificationService.create_notification(
        db=db,
        user_id=o.buyer_id,
        type_="offer_accepted",
        title="Offer Accepted! 🎉",
        message=f"Your offer for {lot.crop_name} was accepted. Trade {txn.public_id or 'record'} is ready to view.",
        related_id=o.id,
        outbox=True,
    )
    NotificationService.create_notification(
        db=db,
        user_id=lot.owner_id,
        type_="trade_created",
        title="Trade record created",
        message=f"Your accepted {lot.crop_name} offer is now recorded as trade {txn.public_id}.",
        related_id=txn.id,
        outbox=True,
    )

    body = {
        "success": True,
        "data": {
            "id": str(o.id),
            "status": o.status,
            "reservation_id": str(res.id),
            "transaction_id": str(txn.id),
        },
        "message": "Offer accepted and order created",
        "request_id": rid,
    }
    save_idempotency(request, db, 200, body, user=user, commit=False)
    db.commit()
    return body


@router.post("/{offer_id}/reject", response_model=dict)
def reject_offer(
    offer_id: str, request: Request, data: RejectRequest | None = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    try:
        offer_uuid = uuid.UUID(offer_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Offer not found")
    initial = db.get(Offer, offer_uuid)
    if not initial:
        raise HTTPException(status_code=404, detail="Offer not found")
    db.query(Lot).filter(Lot.id == initial.lot_id).with_for_update().first()
    o = db.query(Offer).filter(Offer.id == offer_uuid).with_for_update().first()
    if not o:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.role.lower() not in ("admin", "operator") and user.id != o.owner_id:
        raise HTTPException(status_code=403, detail="Only the lot owner can decline this offer")
    if _utc(o.expires_at) and _utc(o.expires_at) <= datetime.now(timezone.utc):
        if o.status.upper() == "PENDING":
            o.status = "EXPIRED"
            db.commit()
        raise HTTPException(status_code=409, detail="Offer has expired")
    if not transition_allowed(o.status, "REJECTED", OFFER_TRANSITIONS):
        raise HTTPException(status_code=409, detail="Offer not pending")

    o.status = "REJECTED"
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="offer.reject",
            entity="offers",
            entity_id=str(o.id),
            request_id=getattr(request.state, "request_id", None),
        )
    )

    # Notify buyer
    reason = (data.reason or "").strip() if data else ""
    reason_copy = f" Reason: {reason}." if reason else ""
    NotificationService.create_notification(
        db=db,
        user_id=o.buyer_id,
        type_="offer_rejected",
        title="Offer Declined",
        message=f"Your offer for this listing was declined.{reason_copy}",
        related_id=o.id,
        outbox=True,
    )
    body = {
        "success": True,
        "data": {"id": str(o.id), "status": o.status},
        "message": "Offer rejected",
        "request_id": getattr(request.state, "request_id", None),
    }
    save_idempotency(request, db, 200, body, user=user, commit=False)
    db.commit()
    return body


@router.post("/{offer_id}/withdraw", response_model=dict)
def withdraw_offer(offer_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    try:
        offer_uuid = uuid.UUID(offer_id)
    except ValueError:
        raise HTTPException(404, "Offer not found")
    offer = db.query(Offer).filter(Offer.id == offer_uuid).with_for_update().first()
    if not offer:
        raise HTTPException(404, "Offer not found")
    if user.role.lower() not in ("admin", "operator") and user.id != offer.buyer_id:
        raise HTTPException(403, "Only the buyer can withdraw this offer")
    if not transition_allowed(offer.status, "CANCELLED", OFFER_TRANSITIONS):
        raise HTTPException(409, "Offer cannot be withdrawn")
    offer.status = "CANCELLED"
    NotificationService.create_notification(db=db, user_id=offer.owner_id, type_="offer_withdrawn", title="Offer withdrawn", message="A buyer withdrew an offer.", related_id=offer.id, outbox=True)
    body = {"success": True, "data": {"id": str(offer.id), "status": offer.status}, "message": "Offer withdrawn", "request_id": getattr(request.state, "request_id", None)}
    save_idempotency(request, db, 200, body, user=user, commit=False)
    db.commit()
    return body


@router.get("/{offer_id}/history", response_model=dict)
def history(offer_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.get(Offer, offer_id)
    if not o:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.role.lower() not in ("admin", "operator") and user.id not in (o.owner_id, o.buyer_id):
        raise HTTPException(status_code=404, detail="Offer not found")
    chain = []
    cur = o
    while cur:
        chain.append(cur)
        cur = db.get(Offer, cur.parent_offer_id) if cur.parent_offer_id else None
        if len(chain) > 10:
            break
    chain = list(reversed(chain))
    data = [
        {
            "id": str(x.id),
            "status": x.status,
            "quantity": str(x.quantity),
            "unit": "quintal",
            "price_per_unit": str(x.price_per_unit),
            "total_value": str(x.total_value) if x.total_value is not None else str(Decimal(str(x.quantity)) * Decimal(str(x.price_per_unit))),
            "message": x.message,
            "created_at": x.created_at.isoformat() if x.created_at else None,
        }
        for x in chain
    ]
    return {
        "success": True,
        "data": data,
        "message": "History",
        "request_id": getattr(request.state, "request_id", None),
    }
