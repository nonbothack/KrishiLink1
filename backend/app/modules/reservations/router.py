from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Lot, Reservation

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=dict)
def list_reservations(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Reservation)
    role = user.role.lower()
    if role in ("farmer", "fpo"):
        q = q.join(Lot, Reservation.lot_id == Lot.id).filter(Lot.owner_id == user.id)
    elif role == "buyer":
        q = q.filter(Reservation.buyer_id == user.id)
    elif role != "admin":
        raise HTTPException(status_code=403, detail="Reservations are not available for this role")
    total = q.count()
    items = q.order_by(Reservation.reserved_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(r.id),
            "lot_id": str(r.lot_id),
            "quantity": float(r.quantity),
            "status": r.status,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        }
        for r in items
    ]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} reservations",
        "request_id": getattr(request.state, "request_id", None),
    }
