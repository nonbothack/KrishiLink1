from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models import Crop, Market, PriceObservation, User
from app.modules.prices.sync_service import PARSER_VERSION, sync_daily_prices

router = APIRouter(prefix="/prices", tags=["prices"])


def observations(db, crop=None, market=None, district=None, state=None):
    q = db.query(PriceObservation, Crop, Market).join(Crop, PriceObservation.crop_id == Crop.id).join(Market, PriceObservation.market_id == Market.id)
    # Older versions generated synthetic history. Retain it for audit, never publish it as market data.
    q = q.filter(PriceObservation.parser_version == PARSER_VERSION)
    for value, column in ((crop, Crop.name), (market, Market.name), (district, Market.district), (state, Market.state)):
        if value and value.lower() != "all":
            q = q.filter(column.ilike(f"%{value}%"))
    return q


def serialize(row):
    o, c, m = row
    return {"id": str(o.id), "crop": c.name, "market": m.name, "district": m.district, "state": m.state,
            "price_date": o.price_date.isoformat(), "min_price": float(o.min_price), "modal_price": float(o.modal_price),
            "max_price": float(o.max_price), "unit": "quintal", "trend": "UNKNOWN", "change_pct": None,
            "source": "Agmarknet reported observations", "source_url": o.source_url, "source_record_id": o.source_record_id}


@router.get("")
def list_prices(request: Request, db: Session = Depends(get_db), crop: str | None = None, market: str | None = None,
                district: str | None = None, state: str | None = None, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    q = observations(db, crop, market, district, state).order_by(PriceObservation.price_date.desc(), PriceObservation.id)
    total = q.count()
    data = [serialize(row) for row in q.offset((page - 1) * limit).limit(limit).all()]
    return {"success": True, "data": {"items": data, "total": total, "page": page, "pages": (total + limit - 1) // limit},
            "message": "Reported observations; check the date", "request_id": getattr(request.state, "request_id", None)}


@router.get("/live")
def live_prices(request: Request, db: Session = Depends(get_db), crop: str | None = None, market: str | None = None,
                district: str | None = None, state: str | None = None, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    q = observations(db, crop, market, district, state).order_by(PriceObservation.price_date.desc())
    return {"success": True, "data": {"items": [serialize(row) for row in q.offset(offset).limit(limit).all()],
            "total": q.count(), "is_live": False}, "source": "Agmarknet reported observations"}


@router.get("/trends/{crop_name}")
def trend(crop_name: str, db: Session = Depends(get_db), market: str | None = None):
    # A trend is meaningful only for the same market. Do not compare unrelated markets.
    rows = observations(db, crop_name, market).order_by(PriceObservation.price_date.desc()).limit(7).all() if market else []
    values = [float(row[0].modal_price) for row in rows]
    if len(values) < 2 or len({str(row[2].id) for row in rows}) != 1:
        return {"success": True, "data": {"trend": "UNKNOWN", "current_price": None, "percentage_change": None, "explanation": "Not enough comparable observations"}}
    average = sum(values) / len(values)
    pct = round((values[0] - average) / average * 100, 2)
    return {"success": True, "data": {"trend": "RISING" if pct > 1.5 else "FALLING" if pct < -1.5 else "STABLE",
            "current_price": values[0], "moving_average": average, "percentage_change": pct}}


@router.get("/{crop_name}/history")
def history(crop_name: str, db: Session = Depends(get_db), market: str | None = None, days: int = Query(15, ge=1, le=90)):
    rows = observations(db, crop_name, market).order_by(PriceObservation.price_date.desc()).limit(days).all()
    return {"success": True, "data": {"history": [{**serialize(row), "date": row[0].price_date.isoformat(), "price": float(row[0].modal_price)} for row in reversed(rows)]}}


@router.get("/{obs_id}/provenance")
def provenance(obs_id: str, db: Session = Depends(get_db)):
    import uuid

    from fastapi import HTTPException
    try:
        obs = db.get(PriceObservation, uuid.UUID(obs_id))
    except ValueError:
        obs = None
    if not obs:
        raise HTTPException(404, "Observation not found")
    return {"success": True, "data": {"id": str(obs.id), "source_url": obs.source_url, "source_record_id": obs.source_record_id,
            "parser_version": obs.parser_version, "retrieved_at": obs.retrieved_at.isoformat() if obs.retrieved_at else None}}


@router.post("/sync")
def sync(db: Session = Depends(get_db), force: bool = False, user: User = Depends(require_role("admin", "operator"))):
    return {"success": True, "data": sync_daily_prices(db, force)}

