import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import BuyerRequirement, Crop, FPOProfile, Lot, Reservation, User
from app.modules.lots.units import UNIT_TO_QUINTAL

router = APIRouter(prefix="/requirements", tags=["requirements"])


class RequirementWrite(BaseModel):
    crop_id: str
    variety_id: str | None = None
    grade: str | None = Field(default=None, pattern="^(A|B|C|UNSPECIFIED)$")
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = "quintal"
    target_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    location_text: str | None = Field(default=None, max_length=300)
    required_until: date | None = None
    allow_partial: bool = True
    notes: str | None = Field(default=None, max_length=1000)
    status: str = Field(default="ACTIVE", pattern="^(DRAFT|ACTIVE)$")


def _buyer(user: User) -> None:
    if user.role.lower() != "buyer":
        raise HTTPException(403, "Buyer account required")


def _canonical(crop: Crop, quantity: Decimal, unit: str) -> tuple[Decimal, str]:
    clean = unit.strip().lower()
    supported = {str(x).lower() for x in (crop.valid_units or [crop.unit or "quintal"])}
    if clean not in supported or clean not in UNIT_TO_QUINTAL:
        raise HTTPException(422, "Unit is not supported for this crop")
    result = quantity * UNIT_TO_QUINTAL[clean]
    if result.quantize(Decimal("0.01")) != result or result > Decimal("1000000"):
        raise HTTPException(422, "Quantity is outside the supported canonical range")
    return result.quantize(Decimal("0.01")), clean


def _projection(row: BuyerRequirement) -> dict:
    requested = Decimal(str(row.canonical_quantity or row.quantity_max or 0))
    committed = Decimal(str(row.committed_quantity or 0))
    return {
        "id": str(row.id), "crop_id": str(row.crop_id) if row.crop_id else None,
        "crop": row.crop_name, "variety_id": str(row.variety_id) if row.variety_id else None,
        "grade": row.grade, "requested_quantity": str(requested),
        "requested_unit": row.requested_unit or "quintal", "canonical_quantity": str(requested),
        "committed_quantity": str(committed), "remaining_quantity": str(max(Decimal("0"), requested - committed)),
        "target_price": str(row.target_price) if row.target_price is not None else None,
        "location": row.location_text, "required_until": row.required_until.isoformat() if row.required_until else None,
        "allow_partial": bool(row.allow_partial), "notes": row.notes,
        "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.post("", status_code=201)
def create_requirement(data: RequirementWrite, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _buyer(user)
    try:
        crop = db.get(Crop, uuid.UUID(data.crop_id))
    except ValueError:
        crop = None
    if not crop or not crop.is_active or not crop.is_tradable:
        raise HTTPException(422, "Select an active canonical crop")
    canonical, unit = _canonical(crop, data.quantity, data.unit)
    if data.required_until and data.required_until < date.today():
        raise HTTPException(422, "Required-by date cannot be in the past")
    row = BuyerRequirement(id=uuid.uuid4(), buyer_id=user.id, crop_id=crop.id, crop_name=crop.name,
        variety_id=uuid.UUID(data.variety_id) if data.variety_id else None, grade=data.grade,
        quantity_min=canonical, quantity_max=canonical, requested_quantity=data.quantity,
        requested_unit=unit, canonical_quantity=canonical, committed_quantity=Decimal("0"),
        target_price=data.target_price, location_text=(data.location_text or None), required_until=data.required_until,
        allow_partial=data.allow_partial, notes=data.notes, status=data.status, is_active=data.status == "ACTIVE")
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _projection(row), "message": "Requirement created", "request_id": getattr(request.state, "request_id", None)}


@router.get("")
def list_requirements(request: Request, status: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _buyer(user)
    query = db.query(BuyerRequirement).filter(BuyerRequirement.buyer_id == user.id)
    if status: query = query.filter(BuyerRequirement.status == status.upper())
    rows = query.order_by(BuyerRequirement.created_at.desc()).all()
    return {"success": True, "data": {"items": [_projection(row) for row in rows], "total": len(rows)}, "message": "Requirements", "request_id": getattr(request.state, "request_id", None)}


@router.get("/discover/lots")
def discover_lots(request: Request, requirement_id: str | None = None, crop: str | None = None, grade: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _buyer(user)
    requirement = None
    if requirement_id:
        try: requirement = db.query(BuyerRequirement).filter(BuyerRequirement.id == uuid.UUID(requirement_id), BuyerRequirement.buyer_id == user.id).first()
        except ValueError: requirement = None
        if not requirement: raise HTTPException(404, "Requirement not found")
        crop = requirement.crop_name
        grade = requirement.grade or grade
    query = db.query(Lot).filter(Lot.deleted_at.is_(None), Lot.status.in_(["PUBLISHED", "PARTIALLY_ALLOCATED"]))
    if crop: query = query.filter(Lot.crop_name.ilike(crop))
    if grade and grade != "UNSPECIFIED": query = query.filter(Lot.grade == grade)
    rows = query.order_by(Lot.created_at.desc()).limit(100).all()
    reservations = {lot.id: sum((Decimal(str(r.quantity)) for r in db.query(Reservation).filter(Reservation.lot_id == lot.id, Reservation.status == "ACTIVE").all()), Decimal("0")) for lot in rows}
    owner_roles = {row.id: row.role.lower() for row in db.query(User).filter(User.id.in_([lot.owner_id for lot in rows])).all()} if rows else {}
    fpo_profiles = {row.user_id: row.organization_name for row in db.query(FPOProfile).filter(FPOProfile.user_id.in_([lot.owner_id for lot in rows])).all()} if rows else {}
    data = []
    for lot in rows:
        available = Decimal(str(lot.quantity)) - reservations[lot.id]
        if available <= 0: continue
        data.append({"id": str(lot.id), "public_id": lot.public_id, "crop": lot.crop_name, "crop_id": str(lot.crop_id) if lot.crop_id else None,
            "quantity": str(available), "unit": lot.unit or "quintal", "grade": lot.grade,
            "asking_price": str(lot.asking_price) if lot.asking_price is not None else None,
            "seller_type": "FPO" if owner_roles.get(lot.owner_id) == "fpo" else "Farmer", "seller_label": "FPO listing" if owner_roles.get(lot.owner_id) == "fpo" else "Farmer listing",
            "seller_name": fpo_profiles.get(lot.owner_id) if owner_roles.get(lot.owner_id) == "fpo" else None,
            "location": lot.district or lot.location_text, "available_from": lot.available_from.isoformat() if lot.available_from else None,
            "match_reason": f"Matches your {lot.crop_name} requirement" if requirement else None})
    return {"success": True, "data": {"items": data, "total": len(data)}, "message": "Available supply", "request_id": getattr(request.state, "request_id", None)}


@router.post("/{requirement_id}/close")
def close_requirement(requirement_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _buyer(user)
    row = db.query(BuyerRequirement).filter(BuyerRequirement.id == requirement_id, BuyerRequirement.buyer_id == user.id).with_for_update().first()
    if not row: raise HTTPException(404, "Requirement not found")
    row.status = "CLOSED"; row.is_active = False; db.commit()
    return {"success": True, "data": _projection(row), "message": "Requirement closed", "request_id": getattr(request.state, "request_id", None)}
