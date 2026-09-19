from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Crop
from app.modules.crops.service import crop_projection, resolve_crop

router = APIRouter(prefix="/crops", tags=["crops"])


@router.get("", response_model=dict)
def list_crops(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
):
    q = db.query(Crop).filter(Crop.is_active.is_(True), Crop.is_tradable.is_(True))
    if search and search.strip():
        # Resolve aliases as well as canonical names consistently across database dialects.
        matching = resolve_crop(db, search.strip(), include_inactive=False)
        if matching:
            q = q.filter(Crop.id == matching.id)
        else:
            q = q.filter(Crop.name.ilike(f"%{search.strip()}%"))
    total = q.count()
    items = q.order_by(Crop.name).offset((page - 1) * limit).limit(limit).all()
    data = [crop_projection(c) for c in items]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} crops",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{crop_id}", response_model=dict)
def get_crop(crop_id: str, request: Request, db: Session = Depends(get_db)):
    c = db.query(Crop).filter(Crop.id == crop_id, Crop.is_active.is_(True), Crop.is_tradable.is_(True)).first()
    if not c:
        raise HTTPException(status_code=404, detail="Crop not found")
    return {
        "success": True,
        "data": crop_projection(c),
        "message": "OK",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/resolve/{name}", response_model=dict)
def resolve_crop_name(name: str, request: Request, db: Session = Depends(get_db)):
    crop = resolve_crop(db, name, include_inactive=False)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    return {
        "success": True,
        "data": crop_projection(crop),
        "message": "Crop resolved",
        "request_id": getattr(request.state, "request_id", None),
    }
