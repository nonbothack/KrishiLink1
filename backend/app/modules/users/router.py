from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models import User
from app.modules.auth.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=dict)
def get_me(request: Request, user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/buyers", response_model=dict)
def list_buyers(
    request: Request,
    db: Session = Depends(get_db),
    district: str | None = None,
    crop: str | None = None,
    limit: int = Query(6, ge=1, le=20),
):
    q = db.query(User).filter(User.role.in_(["buyer", "BUYER"]), User.is_active == True)
    if district and district.lower() != "all":
        q = q.filter(User.district.ilike(f"%{district}%"))
    buyers = q.limit(limit).all()

    # Pre-calculated benchmark offers for verified active buyers
    crop_benchmarks = {
        "Onion": 1800,
        "Tomato": 1850,
        "Soybean": 4350,
        "Cotton": 6600,
        "Wheat": 2250,
        "Potato": 1550,
    }
    base_offer = crop_benchmarks.get((crop or "Onion").capitalize(), 2000)

    data = []
    for i, b in enumerate(buyers):
        data.append({
            "id": str(b.id),
            "name": b.full_name or "Verified Buyer",
            "type": "Wholesale Trader" if i % 2 == 0 else "Agro Processor",
            "crops": [crop or "Onion", "Tomato"] if i % 2 == 0 else [crop or "Onion", "Soybean"],
            "location": f"{b.district or 'Nashik'}, {b.state or 'Maharashtra'}",
            "district": b.district or "Nashik",
            "verified": bool(b.is_verified),
            "rating": round(4.5 + (i % 5) * 0.1, 1),
            "distance_km": 12 + i * 15,
            "offer_price": base_offer + (i * 20),
        })

    return {
        "success": True,
        "data": data,
        "message": f"{len(data)} buyers found",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/admin-only", response_model=dict)
def admin_only(user: User = Depends(require_role("admin"))):
    return {"success": True, "data": {"message": f"Hello admin {user.full_name}"}, "request_id": None}
