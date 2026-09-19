from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_role
from app.core.rate_limit import get_redis
from app.models import (
    Crop,
    CropVariety,
    DataSourceRegistry,
    IngestionRun,
    Market,
    PriceObservation,
    PriceSource,
    User,
)
from app.modules.crops.service import resolve_crop
from app.modules.prices.provider import PARSER_VERSION
from app.modules.prices.sync_service import (
    freshness_state,
    get_cached_price_payload,
    price_cache_key,
    set_cached_price_payload,
)

router = APIRouter(prefix="/prices", tags=["prices"])
SOURCE_KEY = "agmarknet-daily-reported-prices"


def observations(db: Session, crop=None, market=None, district=None, state=None, *, variety=None, grade=None,
                 from_date: date | None = None, to_date: date | None = None):
    query = (
        db.query(PriceObservation, Crop, Market, PriceSource, DataSourceRegistry, CropVariety)
        .join(Crop, PriceObservation.crop_id == Crop.id)
        .join(Market, PriceObservation.market_id == Market.id)
        .join(PriceSource, PriceObservation.source_id == PriceSource.id)
        .join(DataSourceRegistry, PriceSource.registry_id == DataSourceRegistry.id)
        .outerjoin(CropVariety, PriceObservation.variety_id == CropVariety.id)
        .filter(
            PriceSource.adapter == PARSER_VERSION,
            PriceSource.is_active.is_(True),
            DataSourceRegistry.source_key == SOURCE_KEY,
            DataSourceRegistry.is_active.is_(True),
            PriceObservation.price_unit.is_not(None),
            Crop.is_active.is_(True),
            Crop.is_tradable.is_(True),
        )
    )
    if crop and crop.lower() != "all":
        resolved = resolve_crop(db, crop, include_inactive=False)
        if resolved is None:
            return query.filter(Crop.id == uuid.UUID(int=0))
        query = query.filter(Crop.id == resolved.id)
    for value, column in ((market, Market.name), (district, Market.district), (state, Market.state)):
        if value and value.lower() != "all":
            query = query.filter(column.ilike(f"%{value.strip()}%"))
    if variety and variety.lower() != "all":
        query = query.filter(CropVariety.name.ilike(f"%{variety.strip()}%"))
    if grade and grade.lower() != "all":
        query = query.filter(func.lower(PriceObservation.grade) == grade.strip().lower())
    if from_date:
        query = query.filter(PriceObservation.price_date >= from_date)
    if to_date:
        query = query.filter(PriceObservation.price_date <= to_date)
    return query


def serialize(row: tuple[Any, ...]) -> dict[str, Any]:
    observation, crop, market, price_source, registry, crop_variety = row
    reported_on = observation.price_date
    return {
        "id": str(observation.id),
        "crop": crop.name,
        "variety": crop_variety.name if crop_variety else None,
        "grade": observation.grade,
        "market": market.name,
        "district": market.district,
        "state": market.state,
        "outlet_verification": market.verification_status,
        "location_verified": bool(
            market.verification_status == "verified" and market.is_active
            and market.latitude is not None and market.longitude is not None
            and market.coordinate_confidence is not None and market.coordinate_confidence >= 0.85
        ),
        "price_date": reported_on.isoformat() if reported_on else None,
        "fetched_at": observation.fetched_at.isoformat() if observation.fetched_at else None,
        "freshness_state": freshness_state(reported_on),
        "min_price": str(observation.min_price),
        "modal_price": str(observation.modal_price),
        "max_price": str(observation.max_price),
        "unit": observation.price_unit,
        "trend": "UNKNOWN",
        "change_pct": None,
        "source": registry.name,
        "source_url": observation.source_url or price_source.url,
        "source_record_id": observation.source_record_id,
        "parser_version": observation.parser_version,
    }

def _project_rows(query, *, offset: int, limit: int) -> list[dict[str, Any]]:
    rows = query.order_by(PriceObservation.price_date.desc(), PriceObservation.id).offset(offset).limit(limit).all()
    return [serialize(row) for row in rows]


def _response(request: Request, data: dict[str, Any], message: str) -> dict[str, Any]:
    return {"success": True, "data": data, "message": message,
            "request_id": getattr(request.state, "request_id", None)}


@router.get("/ops/health")
def price_pipeline_health(
    request: Request, db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "operator")),
):
    source = db.query(DataSourceRegistry).filter_by(source_key=SOURCE_KEY).first()
    latest_run = db.query(IngestionRun).join(PriceSource, IngestionRun.source_id == PriceSource.id).filter(
        PriceSource.adapter == PARSER_VERSION
    ).order_by(IngestionRun.started_at.desc()).first()
    latest_reported = db.query(func.max(PriceObservation.price_date)).join(
        PriceSource, PriceObservation.source_id == PriceSource.id
    ).filter(PriceSource.adapter == PARSER_VERSION).scalar()
    now = datetime.now(timezone.utc)
    last_success = source.last_success_at if source else None
    stale = not last_success or now - (last_success.replace(tzinfo=timezone.utc) if last_success.tzinfo is None else last_success) > timedelta(hours=24)
    status = "not_configured" if not (settings.agmarknet_api_key or settings.mandi_api_key) else (
        "stale" if stale else (source.last_run_status or "healthy")
    )
    return _response(request, {
        "status": status,
        "provider_configured": bool(settings.agmarknet_api_key or settings.mandi_api_key),
        "source_key": SOURCE_KEY,
        "last_attempt_at": source.last_attempt_at.isoformat() if source and source.last_attempt_at else None,
        "last_success_at": last_success.isoformat() if last_success else None,
        "last_failure_at": source.last_failure_at.isoformat() if source and source.last_failure_at else None,
        "latest_reported_date": latest_reported.isoformat() if latest_reported else None,
        "last_run": ({"id": str(latest_run.id), "status": latest_run.status,
                      "scope": latest_run.scope_json,
                      "counts": {"fetched": latest_run.records_fetched, "accepted": latest_run.records_accepted,
                                 "updated": latest_run.records_updated, "unchanged": latest_run.records_unchanged,
                                 "rejected": latest_run.records_rejected, "quarantined": latest_run.records_quarantined,
                                 "unresolved_markets": latest_run.unresolved_markets,
                                 "unresolved_crops": latest_run.unresolved_crops},
                      "failure": latest_run.provider_failure, "duration_ms": latest_run.duration_ms}
                     if latest_run else None),
    }, "Official reported market price pipeline status")


@router.get("")
def list_prices(
    request: Request, db: Session = Depends(get_db), crop: str | None = None, market: str | None = None,
    district: str | None = None, state: str | None = None, variety: str | None = None,
    grade: str | None = None, from_date: date | None = None, to_date: date | None = None,
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "from_date must not be after to_date")
    dimensions = {"crop": crop, "market": market, "district": district, "state": state,
                  "variety": variety, "grade": grade, "from_date": from_date, "to_date": to_date,
                  "page": page, "limit": limit}
    redis_client = get_redis()
    cache_key = price_cache_key(db, endpoint="list", **dimensions)
    cached = get_cached_price_payload(redis_client, cache_key)
    if cached is not None:
        return _response(request, cached, "Official reported observations; see source date and unit")
    query = observations(db, crop, market, district, state, variety=variety, grade=grade,
                         from_date=from_date, to_date=to_date)
    total = query.count()
    data = {"items": _project_rows(query, offset=(page - 1) * limit, limit=limit), "total": total,
            "page": page, "limit": limit, "pages": (total + limit - 1) // limit if total else 0,
            "is_live": False}
    set_cached_price_payload(redis_client, cache_key, data)
    return _response(request, data, "Official reported observations; see source date and unit")


@router.get("/live")
def live_prices(
    request: Request, db: Session = Depends(get_db), crop: str | None = None, market: str | None = None,
    district: str | None = None, state: str | None = None, variety: str | None = None,
    grade: str | None = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=500),
):
    dimensions = {"crop": crop, "market": market, "district": district, "state": state,
                  "variety": variety, "grade": grade, "page": page, "limit": limit}
    redis_client = get_redis()
    cache_key = price_cache_key(db, endpoint="live", **dimensions)
    cached = get_cached_price_payload(redis_client, cache_key)
    if cached is not None:
        return _response(request, cached, "Daily reported observations; not live prices")
    query = observations(db, crop, market, district, state, variety=variety, grade=grade)
    total = query.count()
    data = {"items": _project_rows(query, offset=(page - 1) * limit, limit=limit), "total": total,
            "page": page, "limit": limit, "pages": (total + limit - 1) // limit if total else 0,
            "is_live": False}
    set_cached_price_payload(redis_client, cache_key, data)
    return _response(request, data, "Daily reported observations; not live prices")


@router.get("/trends/{crop_name}")
def trend(crop_name: str, request: Request, db: Session = Depends(get_db), market: str | None = None,
          variety: str | None = None, grade: str | None = None):
    query = observations(db, crop_name, market, variety=variety, grade=grade)
    query = query.filter(PriceObservation.quality_status.in_(("HIGH", "MEDIUM")))
    rows = query.order_by(PriceObservation.price_date.desc(), PriceObservation.fetched_at.desc()).limit(60).all() if market else []
    comparable_dimensions = {
        (row[0].variety_id, (row[0].grade or "").strip().casefold(), row[0].price_unit, row[3].adapter)
        for row in rows
    }
    if not rows or len({row[0].market_id for row in rows}) != 1 or len(comparable_dimensions) != 1:
        return _response(request, {"eligibility": "INSUFFICIENT_DATA", "trend": "UNKNOWN", "current_price": None,
                                   "percentage_change": None, "observation_count": 0,
                                   "abstention_reason": "PRODUCT_UNIT_SOURCE_OR_MARKET_DIMENSIONS_DIFFER",
                                   "explanation": "Not enough comparable observations from the same market"}, "Reported price movement; descriptive only")
    # Keep one latest source record per distinct reported date. The comparison
    # is between the oldest and newest of seven observations, not a forecast.
    by_date = {}
    for row in rows:
        by_date.setdefault(row[0].price_date, row)
    series = sorted(by_date.items())[-7:]
    latest_date = series[-1][0]
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if (today - latest_date).days > 7:
        return _response(request, {"eligibility": "INSUFFICIENT_DATA", "trend": "UNKNOWN", "current_price": None,
                                   "percentage_change": None, "observation_count": len(series),
                                   "latest_observation_date": latest_date.isoformat(),
                                   "abstention_reason": "LATEST_OBSERVATION_STALE"}, "Reported price movement; descriptive only")
    if len(series) < 7:
        return _response(request, {"eligibility": "INSUFFICIENT_DATA", "trend": "UNKNOWN", "current_price": None,
                                   "percentage_change": None, "observation_count": len(series),
                                   "latest_observation_date": latest_date.isoformat(),
                                   "abstention_reason": "FEWER_THAN_SEVEN_DISTINCT_REPORTED_DATES",
                                   "explanation": "Seven distinct reported dates are required for this descriptive movement"}, "Reported price movement; descriptive only")
    values = [Decimal(str(row[0].modal_price)) for _day, row in series]
    average = sum(values, Decimal("0")) / Decimal(len(values))
    pct = ((values[-1] - values[0]) / values[0] * Decimal("100")).quantize(Decimal("0.01"))
    signal_threshold = settings.intelligence_descriptive_move_threshold_pct
    signal = "RISING" if pct > signal_threshold else "FALLING" if pct < -signal_threshold else "STABLE"
    return _response(request, {"eligibility": "DESCRIPTIVE_ONLY", "trend": signal, "current_price": str(values[-1]),
                               "moving_average": str(average.quantize(Decimal("0.01"))),
                               "percentage_change": str(pct), "observation_count": len(series),
                               "first_observation_date": series[0][0].isoformat(),
                               "latest_observation_date": latest_date.isoformat(),
                               "classification_threshold_pct": str(signal_threshold),
                               "unit": series[-1][1][0].price_unit,
                               "source": series[-1][1][4].name,
                               "movement_kind": "CHANGE_ACROSS_SEVEN_MOST_RECENT_DISTINCT_REPORT_DATES",
                               "forecast": None, "recommendation": None}, "Reported price movement; descriptive only")


@router.get("/{crop_name}/history")
def history(crop_name: str, request: Request, db: Session = Depends(get_db), market: str | None = None,
            days: int = Query(15, ge=1, le=90), variety: str | None = None, grade: str | None = None):
    start_date = datetime.now(ZoneInfo("Asia/Kolkata")).date() - timedelta(days=days - 1)
    query = observations(db, crop_name, market, variety=variety, grade=grade, from_date=start_date)
    rows = query.order_by(PriceObservation.price_date.desc(), PriceObservation.id).limit(500).all()
    items = [serialize(row) for row in reversed(rows)]
    for item, row in zip(items, reversed(rows)):
        item["date"] = row[0].price_date.isoformat()
        item["price"] = str(row[0].modal_price)
    return _response(request, {"history": items}, "Official reported price history")


@router.get("/{obs_id}/provenance")
def provenance(obs_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        observation = db.get(PriceObservation, uuid.UUID(obs_id))
    except ValueError:
        observation = None
    if not observation:
        raise HTTPException(404, "Observation not found")
    source = db.get(PriceSource, observation.source_id) if observation.source_id else None
    registry = db.get(DataSourceRegistry, source.registry_id) if source and source.registry_id else None
    if not source or source.adapter != PARSER_VERSION or not registry or registry.source_key != SOURCE_KEY:
        raise HTTPException(404, "Official price observation not found")
    return _response(request, {"id": str(observation.id), "source": registry.name, "source_url": observation.source_url,
                               "source_record_id": observation.source_record_id,
                               "reported_date": observation.price_date.isoformat(),
                               "fetched_at": observation.fetched_at.isoformat() if observation.fetched_at else None,
                               "price_unit": observation.price_unit, "source_unit": observation.source_unit,
                               "unit_provenance": observation.unit_provenance,
                               "parser_version": observation.parser_version,
                               "normalization_version": observation.normalization_version,
                               "raw_payload_hash": observation.raw_payload_hash}, "Official reported price provenance")


@router.post("/sync", status_code=202)
def sync(request: Request, force: bool = False, crop: str | None = None, district: str | None = None,
         state: str | None = None, user: User = Depends(require_role("admin", "operator"))):
    from app.workers.celery_app import sync_official_prices

    if bool(crop) != bool(district):
        raise HTTPException(422, "On-demand refresh requires both crop and district")
    try:
        task = sync_official_prices.delay(crop=crop, district=district, state=state)
    except Exception:
        raise HTTPException(503, "Price sync queue is unavailable") from None
    return _response(request, {"task_id": task.id, "status": "queued", "force_requested": bool(force),
                               "scope": {"crop": crop, "district": district, "state": state} if crop else None},
                     "Official price sync queued; source and scope refresh floors still apply")
