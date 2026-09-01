import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.idempotency import check_idempotency, save_idempotency
from app.models import Crop, Lot, User
from app.modules.lots.service import calculate_farmer_earnings

router = APIRouter(prefix="/lots", tags=["lots"])

class CreateLotRequest(BaseModel):
    crop: str = Field(min_length=2)
    variety_id: str | None = None
    grade: str = Field(pattern="^(A|B|C)$")
    quantity: float = Field(gt=0)
    unit: str = "quintal"
    asking_price: float | None = Field(default=None, ge=0)
    location_text: str = Field(min_length=2)
    district: str | None = None
    harvest_date: date | None = None
    available_from: date | None = None
    available_until: date | None = None
    market_reference_price: float | None = None

def gen_public_id(db: Session):
    return f"KL-LOT-{uuid.uuid4().hex[:10].upper()}"

@router.post("", response_model=dict, status_code=201)
def create_lot(data: CreateLotRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("farmer","fpo","admin"))):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    crop = db.query(Crop).filter(Crop.name.ilike(data.crop)).first()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    lot = Lot(
        id=uuid.uuid4(),
        public_id=gen_public_id(db),
        owner_id=user.id,
        crop_id=crop.id,
        crop_name=crop.name,
        grade=data.grade,
        quantity=data.quantity,
        unit=data.unit,
        asking_price=data.asking_price,
        market_reference_price=data.market_reference_price,
        location_text=data.location_text,
        district=data.district or user.district,
        harvest_date=data.harvest_date,
        available_from=data.available_from or date.today(),
        available_until=data.available_until or (date.today()+timedelta(days=14)),
        status="PUBLISHED",
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)
    body = {"success": True, "data": {"id": str(lot.id), "public_id": lot.public_id, "crop": lot.crop_name, "quantity": float(lot.quantity), "grade": lot.grade, "status": lot.status}, "message": "Lot created", "request_id": getattr(request.state, "request_id", None)}
    save_idempotency(request, db, 201, body, user=user)
    return body

@router.get("", response_model=dict)
def list_lots(request: Request, db: Session = Depends(get_db), status: str | None = None, crop: str | None = None, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    q = db.query(Lot).filter(Lot.deleted_at.is_(None))
    if status:
        q = q.filter(Lot.status == status)
    if crop:
        q = q.filter(Lot.crop_name.ilike(crop))
    q = q.order_by(Lot.created_at.desc())
    total = q.count()
    items = q.offset((page-1)*limit).limit(limit).all()
    data = [{"id": str(l.id), "public_id": l.public_id, "crop": l.crop_name, "quantity": float(l.quantity), "grade": l.grade, "status": l.status, "location": l.location_text, "district": l.district, "asking_price": float(l.asking_price) if l.asking_price else None} for l in items]
    return {"success": True, "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total+limit-1)//limit}, "message": f"{len(data)} lots", "request_id": getattr(request.state, "request_id", None)}

@router.get("/{lot_id}", response_model=dict)
def get_lot(lot_id: str, request: Request, db: Session = Depends(get_db)):
    lot = None
    try:
        u = uuid.UUID(lot_id)
        lot = db.query(Lot).filter(Lot.id == u).first()
    except (ValueError, AttributeError):
        pass

    if not lot:
        lot = db.query(Lot).filter(Lot.public_id == lot_id).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    return {
        "success": True,
        "data": {
            "id": str(lot.id),
            "public_id": lot.public_id,
            "crop": lot.crop_name,
            "quantity": float(lot.quantity),
            "grade": lot.grade,
            "status": lot.status,
            "location": lot.location_text,
            "district": lot.district,
            "asking_price": float(lot.asking_price) if lot.asking_price else None,
            "available_from": lot.available_from.isoformat() if lot.available_from else None,
            "available_until": lot.available_until.isoformat() if lot.available_until else None,
        },
        "message": "OK",
        "request_id": getattr(request.state, "request_id", None),
    }

@router.get("/public/{public_id}", response_model=dict)
def public_lot(public_id: str, request: Request, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.public_id == public_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return {"success": True, "data": {"public_id": lot.public_id, "crop": lot.crop_name, "grade": lot.grade, "quantity": float(lot.quantity), "unit": lot.unit, "status": lot.status, "district": lot.district, "created_at": lot.created_at.isoformat() if lot.created_at else None}, "message": "Public lot", "request_id": getattr(request.state, "request_id", None)}

@router.get("/{lot_id}/earnings", response_model=dict)
def get_lot_earnings(
    lot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo", "admin")),
):
    try:
        data = calculate_farmer_earnings(db, lot_id, str(user.id))
        return {
            "success": True,
            "data": data,
            "message": "Earnings calculated successfully",
            "request_id": getattr(request.state, "request_id", None),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
