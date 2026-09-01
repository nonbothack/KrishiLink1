import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.rate_limit import rate_limit
from app.models import AuditLog, Lot, Offer, OutboxEvent, Reservation, Transaction, User
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/transactions", tags=["transactions"])

ALLOWED_TRANSITIONS = {
    "CREATED": ["PAYMENT_PENDING", "CANCELLED"],
    "PAYMENT_PENDING": ["PAYMENT_CONFIRMED", "CANCELLED"],
    "PAYMENT_CONFIRMED": ["PROCESSING", "DISPUTED"],
    "PROCESSING": ["READY_FOR_DISPATCH", "DISPUTED"],
    "READY_FOR_DISPATCH": ["IN_TRANSIT", "DISPUTED"],
    "IN_TRANSIT": ["DELIVERED", "DISPUTED"],
    "DELIVERED": ["COMPLETED", "DISPUTED"],
    "COMPLETED": [],
    "DISPUTED": ["RESOLVED", "CANCELLED"],
    "CANCELLED": [],
}

ROLE_TRANSITIONS = {
    "PAYMENT_PENDING": ["buyer", "admin"],
    "PAYMENT_CONFIRMED": ["buyer", "admin"],
    "PROCESSING": ["farmer", "seller", "admin"],
    "READY_FOR_DISPATCH": ["farmer", "seller", "admin"],
    "IN_TRANSIT": ["farmer", "seller", "admin"],
    "DELIVERED": ["buyer", "farmer", "seller", "admin"],
    "COMPLETED": ["buyer", "admin"],
    "DISPUTED": ["buyer", "farmer", "seller", "admin"],
    "RESOLVED": ["admin", "operator"],
    "CANCELLED": ["buyer", "farmer", "seller", "admin"],
}

class CreateTxnRequest(BaseModel):
    reservation_id: str

class TransitionRequest(BaseModel):
    to_status: str

@router.post("", response_model=dict, status_code=201)
@rate_limit(max_requests=20, window_seconds=60, key_prefix="rl_txn")
def create_transaction(data: CreateTxnRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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
                "request_id": getattr(request.state, "request_id", None)
            }

    res = db.get(Reservation, data.reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Reservation not active or already consumed")

    # Authorize: user must be the reservation's buyer or an admin
    if user.role.lower() not in ("admin", "operator") and str(res.buyer_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Forbidden: You cannot create a transaction for another user's reservation")

    lot = db.get(Lot, res.lot_id)
    offer = db.get(Offer, res.offer_id) if res.offer_id else None

    # Derive contractual gross_value from accepted offer or lot price
    if offer and offer.price_per_unit is not None:
        gross_val = round(float(res.quantity) * float(offer.price_per_unit), 2)
    elif lot and lot.asking_price is not None:
        gross_val = round(float(res.quantity) * float(lot.asking_price), 2)
    else:
        gross_val = 0.0

    txn = Transaction(
        id=uuid.uuid4(),
        lot_id=res.lot_id,
        buyer_id=res.buyer_id,
        seller_id=lot.owner_id if lot else user.id,
        allocation_id=None,
        offer_id=res.offer_id,
        status="CREATED",
        gross_value=gross_val,
        idempotency_key=idempotency_key
    )
    db.add(txn)
    res.status = "CONSUMED"
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(AuditLog(actor_id=str(user.id), action="transaction.create", entity="transactions", entity_id=str(txn.id), request_id=rid))
    db.add(OutboxEvent(aggregate="transactions", aggregate_id=str(txn.id), event_type="transaction.created", payload={"transaction_id": str(txn.id)}))

    # Notify seller (farmer) of new transaction
    if lot:
        NotificationService.create_notification(
            db=db,
            user_id=lot.owner_id,
            type_="order_created",
            title="New Order Confirmed",
            message=f"Order created for {lot.crop_name} (ID: #{str(txn.id)[:8]}). Value: Rs. {gross_val:,.2f}. Awaiting escrow payment.",
            related_id=txn.id,
            outbox=True
        )

    db.commit()
    db.refresh(txn)
    body = {"success": True, "data": {"id": str(txn.id), "status": txn.status, "lot_id": str(txn.lot_id), "gross_value": float(txn.gross_value) if txn.gross_value else 0.0}, "message": "Transaction created", "request_id": rid}
    save_idempotency(request, db, 201, body, user=user)
    return body

@router.get("", response_model=dict)
def list_txns(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    q = db.query(Transaction)
    if user.role.lower() == "farmer":
        q = q.filter(Transaction.seller_id == user.id)
    elif user.role.lower() == "buyer":
        q = q.filter(Transaction.buyer_id == user.id)
    total = q.count()
    items = q.order_by(Transaction.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [{"id": str(t.id), "lot_id": str(t.lot_id), "status": t.status, "gross_value": float(t.gross_value) if t.gross_value else None, "created_at": t.created_at.isoformat() if t.created_at else None} for t in items]
    return {"success": True, "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit}, "message": f"{len(data)} transactions", "request_id": getattr(request.state, "request_id", None)}

@router.get("/{txn_id}", response_model=dict)
def get_txn(txn_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Transaction, txn_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if user.role.lower() not in ("admin", "operator") and user.id not in (t.buyer_id, t.seller_id):
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to view this transaction")
    return {"success": True, "data": {"id": str(t.id), "lot_id": str(t.lot_id), "buyer_id": str(t.buyer_id), "seller_id": str(t.seller_id), "status": t.status, "gross_value": float(t.gross_value) if t.gross_value else None, "created_at": t.created_at.isoformat() if t.created_at else None}, "message": "OK", "request_id": getattr(request.state, "request_id", None)}

@router.post("/{txn_id}/transition", response_model=dict)
def transition(txn_id: str, data: TransitionRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.get(Transaction, txn_id)
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if user.role.lower() not in ("admin", "operator") and user.id not in (t.buyer_id, t.seller_id):
        raise HTTPException(status_code=403, detail="Forbidden: You are not authorized to update this transaction")

    cur = t.status
    nxt = data.to_status.upper()
    if nxt not in ALLOWED_TRANSITIONS.get(cur, []):
        raise HTTPException(status_code=409, detail=f"Invalid transaction transition: {cur} -> {nxt}")

    # Verify role permissions for this transition
    allowed_roles = ROLE_TRANSITIONS.get(nxt, ["admin"])
    user_role = user.role.lower()
    if user_role not in ("admin", "operator") and user_role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Forbidden: {user.role} is not permitted to transition to {nxt}")

    t.status = nxt
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(AuditLog(actor_id=str(user.id), action=f"transaction.{nxt.lower()}", entity="transactions", entity_id=str(t.id), before={"status": cur}, after={"status": nxt}, request_id=rid))

    # Notify counterpart of transaction status update
    counterpart_id = t.buyer_id if user.id == t.seller_id else t.seller_id
    NotificationService.create_notification(
        db=db,
        user_id=counterpart_id,
        type_="order_status",
        title="Order Status Updated",
        message=f"Transaction #{str(t.id)[:8]} status changed from {cur} to {nxt}.",
        related_id=t.id,
        outbox=True
    )

    db.commit()
    return {"success": True, "data": {"id": str(t.id), "status": t.status}, "message": f"Transitioned to {nxt}", "request_id": rid}
