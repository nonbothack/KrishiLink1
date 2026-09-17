from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Transaction, User
from app.modules.trades.schemas import (
    AddTradeNoteRequest,
    TradeEventResponse,
    TradeRoomResponse,
    TradeTransitionRequest,
)
from app.modules.trades.service import (
    add_trade_note,
    execute_trade_transition,
    get_or_create_term_snapshot,
    get_trade_room,
)

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=dict)
def list_trades(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: str | None = None,
    crop: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Transaction)
    if user.role.lower() not in ("admin", "operator"):
        q = q.filter((Transaction.buyer_id == user.id) | (Transaction.seller_id == user.id))

    if status:
        q = q.filter(Transaction.status == status.upper())

    q = q.order_by(Transaction.created_at.desc())
    total = q.count()
    txns = q.offset((page - 1) * limit).limit(limit).all()

    items = []
    for t in txns:
        snap = get_or_create_term_snapshot(db, t)
        items.append({
            "id": str(t.id),
            "public_id": t.public_id or f"KL-TRD-{str(t.id)[:8].upper()}",
            "status": t.status,
            "crop_name": snap.crop_name,
            "grade": snap.grade,
            "quantity": float(snap.quantity),
            "unit": snap.unit,
            "gross_value": float(t.gross_value or snap.gross_value or 0.0),
            "created_at": t.created_at,
            "buyer_id": str(t.buyer_id),
            "seller_id": str(t.seller_id),
        })

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
        },
        "message": "Trades retrieved successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{trade_id}/room", response_model=dict)
def get_trade_room_endpoint(
    trade_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = get_trade_room(db, trade_id, user)
    # Validate with Pydantic model for strict schema conformity
    validated = TradeRoomResponse.model_validate(room).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": "Trade room retrieved successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{trade_id}/transition", response_model=dict)
def transition_trade_endpoint(
    trade_id: str,
    data: TradeTransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = execute_trade_transition(db, trade_id, data.to_status, user, request, data.reason)
    validated = TradeRoomResponse.model_validate(room).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": f"Trade successfully transitioned to {data.to_status.upper()}",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{trade_id}/notes", response_model=dict, status_code=201)
def add_trade_note_endpoint(
    trade_id: str,
    data: AddTradeNoteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ev = add_trade_note(db, trade_id, user, data.note, request)
    validated = TradeEventResponse.model_validate(ev).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": "Note added to trade timeline",
        "request_id": getattr(request.state, "request_id", None),
    }
