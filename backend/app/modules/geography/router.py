from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import District, State, Subdistrict

router = APIRouter(prefix="/geo", tags=["geography"])


def _place(place):
    return {
        "id": str(place.id),
        "lgd_code": place.lgd_code,
        "name": place.name,
        "name_hindi": place.name_hindi,
        "name_marathi": place.name_marathi,
        "source_ref": place.source_ref,
    }


@router.get("/states", response_model=dict)
def states(request: Request, db: Session = Depends(get_db)):
    items = db.query(State).filter(State.is_active.is_(True)).order_by(State.name).all()
    return {
        "success": True,
        "data": {"items": [_place(item) for item in items], "total": len(items)},
        "message": f"{len(items)} known states",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/districts", response_model=dict)
def districts(
    request: Request,
    state_id: str = Query(min_length=1, max_length=64),
    db: Session = Depends(get_db),
):
    items = (
        db.query(District)
        .filter(District.state_id == state_id, District.is_active.is_(True))
        .order_by(District.name)
        .all()
    )
    return {
        "success": True,
        "data": {"items": [_place(item) for item in items], "total": len(items)},
        "message": f"{len(items)} known districts",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/subdistricts", response_model=dict)
def subdistricts(
    request: Request,
    district_id: str = Query(min_length=1, max_length=64),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Subdistrict)
        .filter(Subdistrict.district_id == district_id, Subdistrict.is_active.is_(True))
        .order_by(Subdistrict.name)
        .all()
    )
    return {
        "success": True,
        "data": {"items": [_place(item) for item in items], "total": len(items)},
        "message": f"{len(items)} known subdistricts",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/resolve", response_model=dict)
def resolve_location(
    request: Request,
    state: str | None = Query(None, min_length=1, max_length=100),
    district: str | None = Query(None, min_length=1, max_length=100),
    subdistrict: str | None = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    """Resolve exact structured labels only; ambiguous/unknown text stays unresolved."""
    found_state = None
    found_district = None
    found_subdistrict = None
    if state:
        matches = db.query(State).filter(State.is_active.is_(True), State.name.ilike(state.strip())).limit(2).all()
        found_state = matches[0] if len(matches) == 1 else None
    if found_state and district:
        matches = (
            db.query(District)
            .filter(District.state_id == found_state.id, District.is_active.is_(True), District.name.ilike(district.strip()))
            .limit(2)
            .all()
        )
        found_district = matches[0] if len(matches) == 1 else None
    if found_district and subdistrict:
        matches = (
            db.query(Subdistrict)
            .filter(Subdistrict.district_id == found_district.id, Subdistrict.is_active.is_(True), Subdistrict.name.ilike(subdistrict.strip()))
            .limit(2)
            .all()
        )
        found_subdistrict = matches[0] if len(matches) == 1 else None
    resolved = bool(found_state and (not district or found_district) and (not subdistrict or found_subdistrict))
    selected = [item for item in (found_state, found_district, found_subdistrict) if item]
    authoritative = bool(selected) and all(item.lgd_code and item.source_ref for item in selected)
    data = {
        "resolved": resolved,
        "state": _place(found_state) if found_state else None,
        "district": _place(found_district) if found_district else None,
        "subdistrict": _place(found_subdistrict) if found_subdistrict else None,
        "confidence": 1.0 if resolved and authoritative else 0.0,
        "provenance": "lgd" if resolved and authoritative else "unresolved",
    }
    return {
        "success": True,
        "data": data,
        "message": "Location resolved" if resolved else "Location remains unknown",
        "request_id": getattr(request.state, "request_id", None),
    }
