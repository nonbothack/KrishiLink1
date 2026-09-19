import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.domain_contracts import TRADE_TRANSITIONS
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.rate_limit import rate_limit
from app.models import (
    AuditLog,
    BuyerProfile,
    Lot,
    Offer,
    OutboxEvent,
    Reservation,
    TradeEvent,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/transactions", tags=["transactions"])

ALLOWED_TRANSITIONS = TRADE_TRANSITIONS

ROLE_TRANSITIONS = {
    "PAYMENT_PENDING": ["buyer", "admin"],
    "PAYMENT_CONFIRMED": ["buyer", "admin"],
    "PROCESSING": ["farmer", "seller", "admin"],
    "READY_FOR_DISPATCH": ["farmer", "seller", "admin"],
    "IN_TRANSIT": ["farmer", "seller", "admin"],
    "DELIVERED": ["buyer", "farmer", "seller", "admin"],
    "COMPLETED": ["buyer", "admin"],
    "DISPUTED": ["buyer", "farmer", "seller", "admin"],
    "REFUNDED": ["admin", "operator"],
    "CANCELLED": ["buyer", "farmer", "seller", "admin"],
}


class CreateTxnRequest(BaseModel):
    reservation_id: str


class TransitionRequest(BaseModel):
    to_status: str
    reason: str | None = None


@router.post("", response_model=dict, status_code=201)
@rate_limit(max_requests=20, window_seconds=60, key_prefix="rl_txn")
def create_transaction(
    data: CreateTxnRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body

    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        existing = db.query(Transaction).filter(Transaction.idempotency_key == idempotency_key).first()
        if existing:
            return {
                "success": True,
                "data": {"id": str(existing.id), "status": existing.status, "lot_id": str(existing.lot_id)},
                "message": "Transaction already created (idempotent)",
                "request_id": getattr(request.state, "request_id", None),
            }

    res = db.get(Reservation, data.reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # Authorize: user must be the reservation's buyer or an admin
    if user.role.lower() not in ("admin", "operator") and str(res.buyer_id) != str(user.id):
        raise HTTPException(
            status_code=403, detail="Forbidden: You cannot create a transaction for another user's reservation"
        )

    # Check if transaction was already initialized when accepting the offer
    existing_txn = db.query(Transaction).filter(
        Transaction.offer_id == res.offer_id
    ).first()
    if existing_txn:
        if not existing_txn.public_id:
            existing_txn.public_id = f"KL-TRD-{uuid.uuid4().hex[:10].upper()}"
        res.status = "CONSUMED"
        db.commit()
        body = {
            "success": True,
            "data": {
                "id": str(existing_txn.id),
                "public_id": existing_txn.public_id,
                "status": existing_txn.status,
                "lot_id": str(existing_txn.lot_id),
                "gross_value": float(existing_txn.gross_value) if existing_txn.gross_value else 0.0,
            },
            "message": "Transaction created",
            "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        }
        save_idempotency(request, db, 201, body, user=user)
        return body

    if res.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Reservation not active or already consumed")

    lot = db.get(Lot, res.lot_id)
    offer = db.get(Offer, res.offer_id) if res.offer_id else None
    if lot is None:
        raise HTTPException(status_code=409, detail="Reserved lot is unavailable")

    # Derive contractual gross_value from accepted offer or lot price
    if offer and offer.price_per_unit is not None:
        agreed_price = Decimal(str(offer.price_per_unit))
        gross_val = (Decimal(str(res.quantity)) * agreed_price).quantize(Decimal("0.01"))
    elif lot and lot.asking_price is not None:
        agreed_price = Decimal(str(lot.asking_price))
        gross_val = (Decimal(str(res.quantity)) * agreed_price).quantize(Decimal("0.01"))
    else:
        raise HTTPException(status_code=409, detail="Accepted offer and lot do not contain an agreed price")

    txn = Transaction(
        id=uuid.uuid4(),
        public_id=f"KL-TRD-{uuid.uuid4().hex[:10].upper()}",
        lot_id=res.lot_id,
        buyer_id=res.buyer_id,
        seller_id=lot.owner_id if lot else user.id,
        allocation_id=None,
        offer_id=res.offer_id,
        status="CREATED",
        gross_value=gross_val,
        idempotency_key=idempotency_key,
    )
    db.add(txn)
    db.flush()
    price_unit = agreed_price
    db.add(
        TradeTermSnapshot(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            lot_id=res.lot_id,
            buyer_id=res.buyer_id,
            seller_id=lot.owner_id if lot else user.id,
            crop_name=lot.crop_name,
            grade=lot.grade,
            quantity=Decimal(str(res.quantity)),
            unit=lot.unit,
            price_per_unit=price_unit,
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
            title="Trade Agreement Formed",
            description=(
                f"Agreed {Decimal(str(res.quantity))} {lot.unit} of {lot.crop_name} (Grade {lot.grade}) "
                f"at Rs. {price_unit:,.2f}/{lot.unit}."
            ),
        )
    )
    res.status = "CONSUMED"
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="transaction.create",
            entity="transactions",
            entity_id=str(txn.id),
            request_id=rid,
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

    # Notify seller (farmer) of new transaction
    if lot:
        NotificationService.create_notification(
            db=db,
            user_id=lot.owner_id,
            type_="order_created",
            title="New Order Confirmed",
            message=(
                f"Trade record created for {lot.crop_name}. "
                "Confirm payment arrangements directly with the other party; this platform does not move money."
            ),
            related_id=txn.id,
            outbox=True,
        )


    db.commit()
    db.refresh(txn)

    body = {
        "success": True,
        "data": {
            "id": str(txn.id),
            "public_id": txn.public_id,
            "status": txn.status,
            "lot_id": str(txn.lot_id),
            "gross_value": float(txn.gross_value) if txn.gross_value else 0.0,
        },
        "message": "Transaction created",
        "request_id": rid,
    }
    save_idempotency(request, db, 201, body, user=user)
    return body


@router.get("", response_model=dict)
def list_txns(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Transaction)
    if user.role.lower() in ("farmer", "fpo"):
        q = q.filter(Transaction.seller_id == user.id)
    elif user.role.lower() == "buyer":
        q = q.filter(Transaction.buyer_id == user.id)
    total = q.count()
    items = q.order_by(Transaction.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    lot_ids = [t.lot_id for t in items if t.lot_id]
    buyer_ids = list({t.buyer_id for t in items if t.buyer_id})
    seller_ids = list({t.seller_id for t in items if t.seller_id})
    offer_ids = list({t.offer_id for t in items if t.offer_id})
    lots_map = {l.id: l for l in db.query(Lot).filter(Lot.id.in_(lot_ids)).all()} if lot_ids else {}
    offers_map = {o.id: o for o in db.query(Offer).filter(Offer.id.in_(offer_ids)).all()} if offer_ids else {}
    terms_map = {s.transaction_id: s for s in db.query(TradeTermSnapshot).filter(TradeTermSnapshot.transaction_id.in_([t.id for t in items])).all()} if items else {}
    buyer_profiles = {p.user_id: p for p in db.query(BuyerProfile).filter(BuyerProfile.user_id.in_(buyer_ids)).all()} if buyer_ids else {}
    sellers = {seller.id: seller for seller in db.query(User).filter(User.id.in_(seller_ids)).all()} if seller_ids else {}

    data = []
    for t in items:
        terms = terms_map.get(t.id)
        offer = offers_map.get(t.offer_id)
        data.append({
            "id": str(t.id),
            "public_id": t.public_id,
            "lot_id": str(t.lot_id),
            "crop_name": lots_map[t.lot_id].crop_name if t.lot_id in lots_map else "Produce",
            "status": t.status,
            "gross_value": float(t.gross_value) if t.gross_value else None,
            "quantity": str(terms.quantity if terms else offer.quantity if offer else ""),
            "unit": terms.unit if terms else "quintal",
            "price_per_unit": str(terms.price_per_unit if terms else offer.price_per_unit if offer else "") or None,
            "buyer_name": buyer_profiles[t.buyer_id].business_name if t.buyer_id in buyer_profiles else "Buyer account",
            "seller_label": sellers[t.seller_id].full_name if user.role.lower() == "buyer" and t.seller_id in sellers else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} transactions",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{txn_id}", response_model=dict)
def get_txn(txn_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Transaction, txn_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if user.role.lower() not in ("admin", "operator") and user.id not in (t.buyer_id, t.seller_id):
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to view this transaction")
    lot = db.get(Lot, t.lot_id) if t.lot_id else None
    return {
        "success": True,
        "data": {
            "id": str(t.id),
            "public_id": t.public_id,
            "lot_id": str(t.lot_id),
            "crop_name": lot.crop_name if lot else "Produce",
            "buyer_id": str(t.buyer_id),
            "seller_id": str(t.seller_id),
            "status": t.status,
            "gross_value": float(t.gross_value) if t.gross_value else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        },
        "message": "OK",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{txn_id}/transition", response_model=dict)
def transition(
    txn_id: str,
    data: TransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.modules.trades.schemas import TradeRoomResponse
    from app.modules.trades.service import execute_trade_transition

    room = execute_trade_transition(db, txn_id, data.to_status, user, request, data.reason)
    validated = TradeRoomResponse.model_validate(room).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": f"Trade status recorded as {data.to_status.upper()}",
        "request_id": getattr(request.state, "request_id", None),
    }
