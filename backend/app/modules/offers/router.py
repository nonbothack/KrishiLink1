import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.rate_limit import rate_limit
from app.models import AuditLog, Lot, Offer, OutboxEvent, Reservation, Transaction, User
from app.modules.notifications.service import NotificationService
from app.modules.notifications.sms_service import SMSService

router = APIRouter(prefix="/offers", tags=["offers"])


class CreateOfferRequest(BaseModel):
    lot_id: str
    quantity: float = Field(gt=0)
    price_per_unit: float = Field(gt=0)
    message: str | None = None
    expires_at: datetime | None = None


class CounterRequest(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    price_per_unit: float | None = Field(default=None, gt=0)
    message: str | None = None


def _ensure_buyer(user: User):
    if user.role.lower() not in ("buyer", "admin"):
        raise HTTPException(status_code=403, detail="Only buyers can create offers")


@router.post("", response_model=dict, status_code=201)
@rate_limit(max_requests=30, window_seconds=60, key_prefix="rl_offer")
def create_offer(
    data: CreateOfferRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_buyer(user)
    cached = check_idempotency(request, db)
    if cached:
        return cached.response_body

    lot = db.get(Lot, data.lot_id) or db.query(Lot).filter(Lot.public_id == data.lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    if float(data.quantity) > float(lot.quantity):
        raise HTTPException(status_code=409, detail="Offer quantity exceeds lot quantity")

    # Lock lot row to prevent race conditions
    lot_locked = db.query(Lot).filter(Lot.id == lot.id).with_for_update().first()
    if float(data.quantity) > float(lot_locked.quantity):
        raise HTTPException(status_code=409, detail="Offer quantity exceeds lot quantity")

    offer = Offer(
        id=uuid.uuid4(),
        lot_id=lot_locked.id,
        buyer_id=user.id,
        owner_id=lot_locked.owner_id,
        quantity=data.quantity,
        price_per_unit=data.price_per_unit,
        total_value=float(data.quantity) * float(data.price_per_unit),
        message=data.message,
        expires_at=data.expires_at or (datetime.now(timezone.utc) + timedelta(days=3)),
        status="PENDING",
    )
    db.add(offer)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="offer.create",
            entity="offers",
            entity_id=str(offer.id),
            after={"lot_id": str(lot.id), "quantity": data.quantity, "price": data.price_per_unit},
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
        message=f"Received offer of ₹{data.price_per_unit:,.0f}/qtl for {data.quantity} qtl of {lot.crop_name}.",
        related_id=offer.id,
        outbox=True,
    )

    farmer = db.get(User, lot_locked.owner_id)
    if farmer:
        db.add(
            OutboxEvent(
                aggregate="offers",
                aggregate_id=str(offer.id),
                event_type="offer.received.sms",
                payload={
                    "offer_id": str(offer.id),
                    "farmer_phone": farmer.phone,
                    "farmer_name": farmer.full_name,
                    "crop_name": lot.crop_name,
                    "quantity": float(data.quantity),
                    "price_per_unit": float(data.price_per_unit),
                },
            )
        )

    db.commit()
    db.refresh(offer)

    # Asynchronous background SMS dispatch to farmer via native FastAPI BackgroundTasks
    if farmer and farmer.phone:
        background_tasks.add_task(
            SMSService.send_offer_received_sms,
            farmer_phone=farmer.phone,
            farmer_name=farmer.full_name or "Farmer",
            crop_name=lot.crop_name,
            quantity=float(data.quantity),
            price_per_unit=float(data.price_per_unit),
        )
    body = {
        "success": True,
        "data": {
            "id": str(offer.id),
            "lot_id": str(offer.lot_id),
            "quantity": float(offer.quantity),
            "price_per_unit": float(offer.price_per_unit),
            "status": offer.status,
        },
        "message": "Offer created",
        "request_id": rid,
    }
    save_idempotency(request, db, 201, body)
    return body


@router.get("", response_model=dict)
def list_offers(
    request: Request,
    db: Session = Depends(get_db),
    lot_id: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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

    if user.role.lower() == "farmer":
        q = q.filter(Offer.owner_id == user.id)
    elif user.role.lower() == "buyer":
        q = q.filter(Offer.buyer_id == user.id)

    total = q.count()
    items = q.order_by(Offer.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(o.id),
            "lot_id": str(o.lot_id),
            "buyer_id": str(o.buyer_id),
            "quantity": float(o.quantity),
            "price_per_unit": float(o.price_per_unit),
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in items
    ]
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
            "owner_id": str(o.owner_id),
            "quantity": float(o.quantity),
            "price_per_unit": float(o.price_per_unit),
            "total_value": float(o.total_value) if o.total_value else None,
            "status": o.status,
            "message": o.message,
            "expires_at": o.expires_at.isoformat() if o.expires_at else None,
            "parent_offer_id": str(o.parent_offer_id) if o.parent_offer_id else None,
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
    orig = db.get(Offer, offer_id)
    if not orig:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.id != orig.owner_id and user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only lot owner can counter")
    if orig.status.upper() not in ("PENDING", "COUNTERED"):
        raise HTTPException(status_code=409, detail="Offer not in negotiable state")

    orig.status = "COUNTERED"
    new_offer = Offer(
        id=uuid.uuid4(),
        lot_id=orig.lot_id,
        buyer_id=orig.buyer_id,
        owner_id=orig.owner_id,
        quantity=data.quantity or float(orig.quantity),
        price_per_unit=data.price_per_unit or float(orig.price_per_unit),
        total_value=(data.quantity or float(orig.quantity)) * (data.price_per_unit or float(orig.price_per_unit)),
        message=data.message or orig.message,
        status="PENDING",
        parent_offer_id=orig.id,
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

    # Notify buyer of counter offer
    NotificationService.create_notification(
        db=db,
        user_id=orig.buyer_id,
        type_="counter_offer",
        title="Counter-Offer Received",
        message=f"Farmer countered with ₹{new_offer.price_per_unit:,.0f}/qtl for {new_offer.quantity} qtl.",
        related_id=new_offer.id,
        outbox=True,
    )

    db.commit()
    return {
        "success": True,
        "data": {"id": str(new_offer.id), "status": new_offer.status, "parent_offer_id": str(orig.id)},
        "message": "Counter offer created",
        "request_id": rid,
    }


@router.post("/{offer_id}/accept", response_model=dict)
def accept_offer(
    offer_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cached = check_idempotency(request, db)
    if cached:
        return cached.response_body
    o = db.get(Offer, offer_id)
    if not o:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.id not in (o.owner_id, o.buyer_id) and user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not participant")
    if o.status.upper() != "PENDING":
        raise HTTPException(status_code=409, detail="Offer not pending")

    lot = db.query(Lot).filter(Lot.id == o.lot_id).with_for_update().first()
    if float(o.quantity) > float(lot.quantity):
        raise HTTPException(status_code=409, detail="Insufficient lot quantity")
    allocated = (
        db.query(Reservation)
        .filter(Reservation.lot_id == lot.id, Reservation.status == "ACTIVE")
        .with_for_update()
        .all()
    )
    total_alloc = sum(float(r.quantity) for r in allocated)
    if total_alloc + float(o.quantity) > float(lot.quantity):
        raise HTTPException(status_code=409, detail="Insufficient remaining quantity")

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

    # Automatically initialize Transaction so deal is active on both sides immediately
    gross_val = round(float(o.quantity) * float(o.price_per_unit), 2)
    txn = Transaction(
        id=uuid.uuid4(),
        lot_id=lot.id,
        buyer_id=o.buyer_id,
        seller_id=lot.owner_id,
        allocation_id=None,
        offer_id=o.id,
        status="CREATED",
        gross_value=gross_val,
    )
    db.add(txn)

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
        message=f"Your offer for {lot.crop_name} ({o.quantity} qtl at ₹{o.price_per_unit:,.0f}/qtl) was accepted. Order #{str(txn.id)[:8]} created.",
        related_id=o.id,
        outbox=True,
    )

    seller = db.get(User, lot.owner_id)
    if seller:
        db.add(
            OutboxEvent(
                aggregate="deals",
                aggregate_id=str(txn.id),
                event_type="deal.confirmed.sms",
                payload={
                    "transaction_id": str(txn.id),
                    "order_id": str(txn.id)[:8],
                    "farmer_phone": seller.phone,
                    "farmer_name": seller.full_name,
                    "crop_name": lot.crop_name,
                    "quantity": float(o.quantity),
                    "price_per_unit": float(o.price_per_unit),
                },
            )
        )

    db.commit()

    # Asynchronous background SMS dispatch via FastAPI BackgroundTasks
    if seller and seller.phone:
        background_tasks.add_task(
            SMSService.send_deal_confirmation,
            farmer_phone=seller.phone,
            farmer_name=seller.full_name or "Farmer",
            crop_name=lot.crop_name,
            quantity=float(o.quantity),
            price_per_unit=float(o.price_per_unit),
            order_id=str(txn.id)[:8],
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
    save_idempotency(request, db, 200, body)
    return body


@router.post("/{offer_id}/reject", response_model=dict)
def reject_offer(
    offer_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    o = db.get(Offer, offer_id)
    if not o:
        raise HTTPException(status_code=404, detail="Offer not found")
    if user.id not in (o.owner_id, o.buyer_id) and user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if o.status.upper() != "PENDING":
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
    NotificationService.create_notification(
        db=db,
        user_id=o.buyer_id,
        type_="offer_rejected",
        title="Offer Declined",
        message=f"Your offer of ₹{o.price_per_unit:,.0f}/qtl for {o.quantity} qtl was declined.",
        related_id=o.id,
        outbox=True,
    )

    db.commit()
    return {
        "success": True,
        "data": {"id": str(o.id), "status": o.status},
        "message": "Offer rejected",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{offer_id}/history", response_model=dict)
def history(offer_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    o = db.get(Offer, offer_id)
    if not o:
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
            "quantity": float(x.quantity),
            "price_per_unit": float(x.price_per_unit),
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
