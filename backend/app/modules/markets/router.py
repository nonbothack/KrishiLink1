import re
import unicodedata
from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from geoalchemy2 import Geography
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_current_user, require_role
from app.models import (
    AuditLog,
    BuyerProfile,
    DataSourceRegistry,
    District,
    FPOProfile,
    Market,
    State,
    StorageFacility,
    User,
)
from app.modules.crops.service import normalize_crop_name

router = APIRouter(prefix="/markets", tags=["markets"])


def public_source_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return None
    return value


@router.get("", response_model=dict)
def list_markets(
    request: Request,
    db: Session = Depends(get_db),
    state: str | None = None,
    district: str | None = None,
    search: str | None = None,
    near_lat: float | None = None,
    near_lng: float | None = None,
    radius_km: float | None = 100,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    """
    List APMC / wholesale markets with optional PostGIS spatial proximity and search filters.
    """
    q = db.query(Market).filter(
        Market.is_active.is_(True),
        Market.verification_status == "verified",
        Market.coordinate_confidence >= 0.85,
        Market.source_confidence >= 0.85,
        Market.latitude.is_not(None),
        Market.longitude.is_not(None),
    )

    if state and state.lower() != "all":
        q = q.filter(Market.state.ilike(f"%{state}%"))
    if district and district.lower() != "all":
        q = q.filter(Market.district.ilike(f"%{district}%"))
    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.filter((Market.name.ilike(term)) | (Market.district.ilike(term)) | (Market.state.ilike(term)))

    # PostGIS Spatial Radius Query (Dialect aware for PostgreSQL & SQLite test runner)
    if (near_lat is None) != (near_lng is None):
        raise HTTPException(422, "near_lat and near_lng must be supplied together")
    if near_lat is not None and near_lng is not None:
        if not (6 <= near_lat <= 38 and 68 <= near_lng <= 98):
            raise HTTPException(422, "Coordinates must be within the supported India bounds")
        if radius_km is None or not (0 < radius_km <= 500):
            raise HTTPException(422, "radius_km must be greater than 0 and no more than 500")
        dialect_name = getattr(getattr(db.bind, "dialect", None), "name", "")
        if dialect_name == "postgresql":
            point = cast(
                func.ST_SetSRID(func.ST_MakePoint(near_lng, near_lat), 4326),
                Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            )
            q = q.filter(Market.location_geog.is_not(None), func.ST_DWithin(Market.location_geog, point, radius_km * 1000))
        else:
            # SQLite is a test-only fallback; exact Haversine filtering is applied below.
            deg_delta = radius_km / 111.0
            q = q.filter(
                Market.latitude.between(near_lat - deg_delta, near_lat + deg_delta),
                Market.longitude.between(near_lng - deg_delta, near_lng + deg_delta),
            )

    dialect_name = getattr(getattr(db.bind, "dialect", None), "name", "")
    distance_m = None
    if near_lat is not None and near_lng is not None and dialect_name == "postgresql":
        point = cast(
            func.ST_SetSRID(func.ST_MakePoint(near_lng, near_lat), 4326),
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        )
        distance_m = func.ST_Distance(Market.location_geog, point).label("distance_m")
        rows = q.with_entities(Market, distance_m).order_by(distance_m).all()
        total = len(rows)
        page_rows = rows[(page - 1) * limit : page * limit]
        items = [(row[0], float(row[1]) / 1000 if row[1] is not None else None) for row in page_rows]
    elif near_lat is not None and near_lng is not None:
        candidates = q.all()
        ranked = []
        for market in candidates:
            if market.latitude is None or market.longitude is None:
                continue
            dlat = radians(float(market.latitude) - near_lat)
            dlng = radians(float(market.longitude) - near_lng)
            a = sin(dlat / 2) ** 2 + cos(radians(near_lat)) * cos(radians(float(market.latitude))) * sin(dlng / 2) ** 2
            distance = 6371 * (2 * atan2(sqrt(a), sqrt(1 - a)))
            if distance <= radius_km:
                ranked.append((market, distance))
        ranked.sort(key=lambda item: item[1])
        total = len(ranked)
        items = ranked[(page - 1) * limit : page * limit]
    else:
        total = q.count()
        items = [(market, None) for market in q.order_by(Market.name).offset((page - 1) * limit).limit(limit).all()]

    data: list[dict[str, Any]] = []
    source_ids = {market.source_registry_id for market, _distance in items if market.source_registry_id}
    sources = {
        source.id: source
        for source in db.query(DataSourceRegistry).filter(DataSourceRegistry.id.in_(source_ids)).all()
    } if source_ids else {}
    for m, dist_km in items:
        source = sources.get(m.source_registry_id)
        data.append(
            {
                "id": str(m.id),
                "slug": public_market_slug(m),
                "name": m.name,
                "district": m.district,
                "state": m.state,
                "latitude": float(m.latitude) if m.latitude is not None else None,
                "longitude": float(m.longitude) if m.longitude is not None else None,
                "market_type": m.market_type,
                "outlet_type": m.outlet_type,
                "verification_status": m.verification_status,
                "coordinate_source": m.coordinate_source,
                "coordinate_confidence": float(m.coordinate_confidence) if m.coordinate_confidence is not None else None,
                "source_confidence": float(m.source_confidence) if m.source_confidence is not None else None,
                "source_name": source.name if source else None,
                "source_url": public_source_url(source.url) if source else None,
                "source_license_status": source.license_status if source else None,
                "last_reviewed_at": m.last_reviewed_at.isoformat() if m.last_reviewed_at else None,
                "distance_km": round(dist_km, 1) if dist_km is not None else None,
            }
        )

    if near_lat is not None and near_lng is not None:
        data.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"] or 0))

    return {
        "success": True,
        "data": {
            "items": data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total > 0 else 0,
        },
        "message": f"{len(data)} markets",
        "request_id": getattr(request.state, "request_id", None),
    }


def public_market_slug(market: Market) -> str:
    """Stable, human-readable slug backed by an outlet ID suffix."""
    label = " ".join(part for part in (market.name, market.district, market.state) if part)
    normalized = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "outlet"
    identity = str(market.id).replace("-", "")[:12]
    return f"{base}-{identity}"


@router.get("/slug/{slug}", response_model=dict)
def get_public_market_by_slug(slug: str, request: Request, db: Session = Depends(get_db)):
    """Return a public, reviewed outlet projection without operational/private fields."""
    identity = slug.rsplit("-", 1)[-1]
    if not re.fullmatch(r"[0-9a-fA-F]{12}", identity):
        raise HTTPException(404, "Outlet not found")
    market = (
        db.query(Market)
        .filter(
            func.substr(func.replace(cast(Market.id, String), "-", ""), 1, 12) == identity.lower(),
            Market.is_active.is_(True),
            Market.verification_status == "verified",
            Market.coordinate_confidence >= 0.85,
            Market.source_confidence >= 0.85,
            Market.latitude.is_not(None),
            Market.longitude.is_not(None),
        )
        .first()
    )
    if not market or public_market_slug(market) != slug:
        raise HTTPException(404, "Outlet not found")
    source = db.get(DataSourceRegistry, market.source_registry_id) if market.source_registry_id else None
    data = {
        "id": str(market.id),
        "slug": public_market_slug(market),
        "name": market.name,
        "district": market.district,
        "state": market.state,
        "outlet_type": market.outlet_type,
        "market_type": market.market_type,
        "latitude": float(market.latitude),
        "longitude": float(market.longitude),
        "verification_status": market.verification_status,
        "coordinate_source": market.coordinate_source,
        "coordinate_confidence": float(market.coordinate_confidence),
        "source_confidence": float(market.source_confidence),
        "source_name": source.name if source else None,
        "source_url": public_source_url(source.url) if source else None,
        "source_license_status": source.license_status if source else None,
        "last_reviewed_at": market.last_reviewed_at.isoformat() if market.last_reviewed_at else None,
    }
    return {
        "success": True,
        "data": data,
        "message": "Reviewed outlet details",
        "request_id": getattr(request.state, "request_id", None),
    }


class OutletReviewRequest(BaseModel):
    status: Literal["needs_review", "verified", "rejected"]
    verification_method: str = Field(min_length=5, max_length=500)
    coordinate_source: str | None = Field(default=None, max_length=100)
    coordinate_confidence: float | None = Field(default=None, ge=0, le=1)
    source_confidence: float | None = Field(default=None, ge=0, le=1)
    outlet_type: Literal[
        "apmc_principal", "apmc_sub", "enam_market", "private_mandi", "fpo_centre",
        "processor_point", "government_procurement", "warehouse", "cold_storage",
        "collection_centre", "verified_trader", "haat", "market_candidate", "haat_candidate",
    ] | None = None


class DataSourceCreateRequest(BaseModel):
    source_key: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9][a-z0-9._-]+$")
    name: str = Field(min_length=2, max_length=200)
    owner: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=1000)
    license_name: str | None = Field(default=None, max_length=200)
    license_url: str | None = Field(default=None, max_length=1000)
    license_status: Literal["approved", "restricted", "unknown", "not_applicable"] = "unknown"
    retrieval_method: str | None = Field(default=None, max_length=200)
    schema_version: str | None = Field(default=None, max_length=100)
    expected_cadence: str | None = Field(default=None, max_length=100)
    geographic_coverage: str | None = Field(default=None, max_length=300)
    dedupe_key: str | None = Field(default=None, max_length=300)
    parser_version: str | None = Field(default=None, max_length=100)


class DataSourceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    owner: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=1000)
    license_name: str | None = Field(default=None, max_length=200)
    license_url: str | None = Field(default=None, max_length=1000)
    license_status: Literal["approved", "restricted", "unknown", "not_applicable"] | None = None
    retrieval_method: str | None = Field(default=None, max_length=200)
    schema_version: str | None = Field(default=None, max_length=100)
    expected_cadence: str | None = Field(default=None, max_length=100)
    geographic_coverage: str | None = Field(default=None, max_length=300)
    dedupe_key: str | None = Field(default=None, max_length=300)
    parser_version: str | None = Field(default=None, max_length=100)
    unit_conventions: dict[str, Literal["INR/quintal", "INR/number"]] | None = None
    is_active: bool | None = None

    @field_validator("unit_conventions")
    @classmethod
    def normalize_unit_convention_keys(cls, values):
        if values is None:
            return None
        normalized = {}
        for key, unit in values.items():
            if "::" in key:
                crop_name, variety_name = key.split("::", 1)
                normalized[f"{normalize_crop_name(crop_name)}::{normalize_crop_name(variety_name)}"] = unit
            else:
                normalized[normalize_crop_name(key)] = unit
        return normalized


def source_projection(source: DataSourceRegistry) -> dict[str, Any]:
    return {
        "id": str(source.id), "source_key": source.source_key, "name": source.name,
        "owner": source.owner, "url": source.url, "license_name": source.license_name,
        "license_url": source.license_url, "license_status": source.license_status,
        "retrieval_method": source.retrieval_method, "schema_version": source.schema_version,
        "expected_cadence": source.expected_cadence, "geographic_coverage": source.geographic_coverage,
        "dedupe_key": source.dedupe_key, "parser_version": source.parser_version,
        "last_success_at": source.last_success_at.isoformat() if source.last_success_at else None,
        "last_attempt_at": source.last_attempt_at.isoformat() if source.last_attempt_at else None,
        "last_failure_at": source.last_failure_at.isoformat() if source.last_failure_at else None,
        "freshness_sla_seconds": source.freshness_sla_seconds,
        "unit_conventions": source.unit_conventions or {},
        "last_run_status": source.last_run_status,
        "last_run_counts": source.last_run_counts,
        "known_gaps": source.known_gaps or [],
        "quality_score": float(source.quality_score) if source.quality_score is not None else None,
        "is_active": bool(source.is_active),
    }


@router.get("/sources", response_model=dict)
def list_data_sources(
    request: Request, db: Session = Depends(get_db), _user: User = Depends(require_role("admin", "operator"))
):
    sources = db.query(DataSourceRegistry).order_by(DataSourceRegistry.name).all()
    return {"success": True, "data": {"items": [source_projection(source) for source in sources], "total": len(sources)}, "message": "Data source registry", "request_id": getattr(request.state, "request_id", None)}


@router.post("/sources", response_model=dict, status_code=201)
def create_data_source(
    payload: DataSourceCreateRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
):
    if payload.license_status == "approved" and not (payload.license_name or payload.license_url):
        raise HTTPException(422, "Approved source requires license name or license URL evidence")
    if db.query(DataSourceRegistry).filter_by(source_key=payload.source_key).first():
        raise HTTPException(409, "source_key already exists")
    source = DataSourceRegistry(**payload.model_dump())
    db.add(source)
    db.flush()
    db.add(AuditLog(actor_id=str(user.id), action="data_source.created", entity="data_source_registry", entity_id=str(source.id), after={"source_key": source.source_key, "license_status": source.license_status}, request_id=getattr(request.state, "request_id", None)))
    db.commit()
    return {"success": True, "data": source_projection(source), "message": "Data source registered", "request_id": getattr(request.state, "request_id", None)}


@router.patch("/sources/{source_id}", response_model=dict)
def update_data_source(
    source_id: str, payload: DataSourceUpdateRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("admin"))
):
    source = db.query(DataSourceRegistry).filter(DataSourceRegistry.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")
    changes = payload.model_dump(exclude_unset=True)
    final_status = changes.get("license_status", source.license_status)
    final_license = changes.get("license_name", source.license_name)
    final_license_url = changes.get("license_url", source.license_url)
    if final_status == "approved" and not (final_license or final_license_url):
        raise HTTPException(422, "Approved source requires license name or license URL evidence")
    before = {key: getattr(source, key) for key in changes}
    for key, value in changes.items():
        setattr(source, key, value)
    db.add(AuditLog(actor_id=str(user.id), action="data_source.updated", entity="data_source_registry", entity_id=str(source.id), before=before, after=changes, request_id=getattr(request.state, "request_id", None)))
    db.commit()
    return {"success": True, "data": source_projection(source), "message": "Data source updated", "request_id": getattr(request.state, "request_id", None)}


@router.get("/review", response_model=dict)
def outlet_review_queue(
    request: Request,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "operator")),
    limit: int = Query(100, ge=1, le=500),
):
    rows = (
        db.query(Market)
        .filter(Market.verification_status.in_(["needs_review", "unverified"]))
        .order_by(Market.created_at, Market.name)
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": str(row.id),
            "name": row.name,
            "district": row.district,
            "state": row.state,
            "outlet_type": row.outlet_type,
            "source_ref": row.source_ref,
            "coordinate_source": row.coordinate_source,
            "coordinate_confidence": float(row.coordinate_confidence) if row.coordinate_confidence is not None else None,
            "source_confidence": float(row.source_confidence) if row.source_confidence is not None else None,
            "latitude": float(row.latitude) if row.latitude is not None else None,
            "longitude": float(row.longitude) if row.longitude is not None else None,
            "metadata": row.metadata_json or {},
        }
        for row in rows
    ]
    return {"success": True, "data": {"items": items, "total": len(items)}, "message": "Outlet review queue", "request_id": getattr(request.state, "request_id", None)}


@router.get("/quality", response_model=dict)
def outlet_quality_report(
    request: Request,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "operator")),
):
    total = db.query(Market).count()
    verified = db.query(Market).filter(Market.verification_status == "verified", Market.is_active.is_(True)).count()
    review = db.query(Market).filter(Market.verification_status.in_(["needs_review", "unverified"])).count()
    missing_source = db.query(Market).filter(Market.source_registry_id.is_(None)).count()
    missing_type = db.query(Market).filter(Market.outlet_type.is_(None)).count()
    low_confidence = db.query(Market).filter(
        Market.latitude.is_not(None),
        (Market.coordinate_confidence.is_(None) | (Market.coordinate_confidence < 0.85)),
    ).count()
    low_source_confidence = db.query(Market).filter(
        Market.is_active.is_(True),
        (Market.source_confidence.is_(None) | (Market.source_confidence < 0.85)),
    ).count()
    outside_bounds = db.query(Market).filter(or_(
        (Market.latitude.is_not(None)) & ((Market.latitude < 6) | (Market.latitude > 38)),
        (Market.longitude.is_not(None)) & ((Market.longitude < 68) | (Market.longitude > 98)),
    )).count()
    stale_before = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1)
    stale_verified = db.query(Market).filter(
        Market.verification_status == "verified",
        or_(Market.last_reviewed_at.is_(None), Market.last_reviewed_at < stale_before),
    ).count()
    coordinate_clusters = (
        db.query(func.round(Market.latitude, 2), func.round(Market.longitude, 2))
        .filter(Market.latitude.is_not(None), Market.longitude.is_not(None))
        .group_by(func.round(Market.latitude, 2), func.round(Market.longitude, 2))
        .having(func.count() >= 5)
        .count()
    )
    data = {
        "total_records": total,
        "verified_active_outlets": verified,
        "review_queue": review,
        "missing_source": missing_source,
        "missing_outlet_type": missing_type,
        "low_confidence_coordinates": low_confidence,
        "low_confidence_sources": low_source_confidence,
        "coordinates_outside_india_bounds": outside_bounds,
        "stale_verifications_over_365_days": stale_verified,
        "suspicious_coordinate_clusters_rounded_0_01deg": coordinate_clusters,
        "verified_coordinate_coverage_pct": round(
            100 * db.query(Market).filter(
                Market.verification_status == "verified", Market.is_active.is_(True),
                Market.latitude.is_not(None), Market.longitude.is_not(None), Market.coordinate_confidence >= 0.85,
                Market.source_confidence >= 0.85,
            ).count() / verified, 1
        ) if verified else None,
    }
    return {"success": True, "data": data, "message": "Outlet quality report", "request_id": getattr(request.state, "request_id", None)}


@router.post("/{market_id}/review", response_model=dict)
def review_outlet(
    market_id: str,
    payload: OutletReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "operator")),
):
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(404, "Outlet candidate not found")
    if payload.status == "verified":
        source = db.get(DataSourceRegistry, market.source_registry_id) if market.source_registry_id else None
        if not source or source.license_status not in {"approved", "not_applicable"}:
            raise HTTPException(409, "An approved source record is required before verification")
        if market.latitude is None or market.longitude is None or market.location_geog is None:
            raise HTTPException(409, "A coordinate with recorded provenance is required before publishing this outlet")
        if not payload.coordinate_source or payload.coordinate_confidence is None or payload.coordinate_confidence < 0.85:
            raise HTTPException(422, "Verified outlets require coordinate provenance and confidence of at least 0.85")
        if payload.source_confidence is None or payload.source_confidence < 0.85:
            raise HTTPException(422, "Verified outlets require recorded source confidence of at least 0.85")
        if not (6 <= float(market.latitude) <= 38 and 68 <= float(market.longitude) <= 98):
            raise HTTPException(422, "Outlet coordinates must be within India bounds")
        state = db.get(State, market.state_id) if market.state_id else None
        district = db.get(District, market.district_id) if market.district_id else None
        if not state or not district or not state.lgd_code or not district.lgd_code or district.state_id != state.id:
            raise HTTPException(409, "A consistent LGD state and district mapping is required before publication")
        resolved_type = payload.outlet_type or market.outlet_type
        if resolved_type in ("market_candidate", "haat_candidate") or not resolved_type:
            raise HTTPException(422, "A candidate type cannot be published as a verified selling outlet")
    before = {"verification_status": market.verification_status, "is_active": market.is_active}
    market.verification_status = payload.status
    market.verification_method = payload.verification_method.strip()
    market.last_reviewed_at = datetime.now(timezone.utc)
    market.verified_by = user.id
    if payload.outlet_type:
        market.outlet_type = payload.outlet_type
        market.market_type = payload.outlet_type
    if payload.status == "verified":
        market.verified_at = market.last_reviewed_at
        market.coordinate_source = payload.coordinate_source
        market.coordinate_confidence = payload.coordinate_confidence
        market.source_confidence = payload.source_confidence
        market.is_active = True
    else:
        market.verified_at = None
        market.is_active = False
    db.add(AuditLog(
        actor_id=str(user.id), action="market.outlet_review", entity="markets", entity_id=str(market.id),
        before=before, after={"verification_status": market.verification_status, "is_active": market.is_active, "method": market.verification_method},
        request_id=getattr(request.state, "request_id", None),
    ))
    db.commit()
    return {"success": True, "data": {"id": str(market.id), "verification_status": market.verification_status, "is_active": market.is_active}, "message": "Outlet review saved", "request_id": getattr(request.state, "request_id", None)}


@router.get("/locations", response_model=dict)
def get_map_locations(
    request: Request,
    db: Session = Depends(get_db),
    category: str = Query("all", description="all, mandi, buyer, storage, fpo"),
    state: str | None = None,
    district: str | None = None,
    near_lat: float | None = None,
    near_lng: float | None = None,
    radius_km: float | None = 150,
    search: str | None = None,
    user: User | None = Depends(get_optional_current_user),
):
    """
    Get all map locations (Mandis, Buyers, Storage Facilities, FPOs) for interactive map rendering.
    """
    from math import atan2, cos, radians, sin, sqrt

    has_sensitive_map_access = bool(user and user.role.lower() in {"admin", "operator"})
    if category in {"buyer", "buyers", "storage", "warehouses", "fpo", "fpos"} and not has_sensitive_map_access:
        raise HTTPException(403, "This map layer is not public")
    if category == "all" and not has_sensitive_map_access:
        # Public discovery is limited to the substantiated outlet registry.
        category = "mandi"

    def calc_dist(lat1: float, lng1: float, lat2: float | None, lng2: float | None) -> float | None:
        if lat2 is None or lng2 is None:
            return None
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(6371 * c, 1)

    locations: list[dict[str, Any]] = []

    # 1. Mandis / APMCs
    if category in ("all", "mandi", "mandis"):
        mq = db.query(Market).filter(
            Market.is_active.is_(True),
            Market.verification_status == "verified",
            Market.coordinate_confidence >= 0.85,
            Market.source_confidence >= 0.85,
        )
        if state and state.lower() != "all":
            mq = mq.filter(Market.state.ilike(f"%{state}%"))
        if district and district.lower() != "all":
            mq = mq.filter(Market.district.ilike(f"%{district}%"))
        if search and search.strip():
            mq = mq.filter(Market.name.ilike(f"%{search.strip()}%"))

        for m in mq.limit(200).all():
            if m.latitude and m.longitude:
                lat = float(m.latitude)
                lng = float(m.longitude)
                dist = calc_dist(near_lat, near_lng, lat, lng) if near_lat and near_lng else None
                if radius_km and dist is not None and dist > radius_km:
                    continue
                locations.append(
                    {
                        "id": f"mandi-{m.id}",
                        "raw_id": str(m.id),
                        "type": "mandi",
                        "name": m.name,
                        "district": m.district,
                        "state": m.state,
                        "lat": lat,
                        "lng": lng,
                        "distance_km": dist,
                        "info": f"APMC Wholesale Mandi · {m.district}, {m.state}",
                        "details": {
                            "market_type": m.market_type or "APMC",
                            "district": m.district,
                            "state": m.state,
                        },
                    }
                )

    # 2. Buyers / Traders
    if category in ("all", "buyer", "buyers"):
        bq = db.query(BuyerProfile, User).join(User, BuyerProfile.user_id == User.id).filter(User.is_active == True)  # noqa: E712
        if state and state.lower() != "all":
            bq = bq.filter(User.state.ilike(f"%{state}%"))
        if district and district.lower() != "all":
            bq = bq.filter(User.district.ilike(f"%{district}%"))

        for bp, u in bq.limit(100).all():
            coords = bp.location_geog or u.location_geog
            if not coords:
                continue
            try:
                from shapely import wkb

                point = wkb.loads(bytes(coords.data))
                lng, lat = point.x, point.y
            except (AttributeError, TypeError, ValueError):
                continue
            dist = calc_dist(near_lat, near_lng, lat, lng) if near_lat and near_lng else None
            if radius_km and dist is not None and dist > radius_km:
                continue

            crops_str = ", ".join(bp.crops_interested) if bp.crops_interested else "not specified"
            locations.append(
                {
                    "id": f"buyer-{bp.id}",
                    "raw_id": str(bp.id),
                    "type": "buyer",
                    "name": bp.business_name or u.full_name,
                    "district": u.district,
                    "state": u.state,
                    "lat": lat,
                    "lng": lng,
                    "distance_km": dist,
                    "info": f"Buyer ({bp.business_type or 'type unavailable'}) · Buying {crops_str}",
                    "details": {
                        "business_type": bp.business_type,
                        "rating": float(bp.rating) if bp.total_transactions and bp.rating is not None else None,
                        "crops": bp.crops_interested or [],
                        "business_verification_status": bp.business_verification_status,
                        "verified": bp.business_verification_status == "VERIFIED",
                    },
                }
            )

    # 3. Storage Facilities
    if category in ("all", "storage", "warehouses"):
        sq = db.query(StorageFacility).filter(
            StorageFacility.status == "ACTIVE",
            StorageFacility.verification_status == "VERIFIED",
            StorageFacility.source_kind != "UNKNOWN_LEGACY",
        )
        for s in sq.limit(50).all():
            if not s.location_geog:
                continue
            try:
                from shapely import wkb

                point = wkb.loads(bytes(s.location_geog.data))
                lng, lat = point.x, point.y
            except (AttributeError, TypeError, ValueError):
                continue
            dist = calc_dist(near_lat, near_lng, lat, lng) if near_lat and near_lng else None
            if radius_km and dist is not None and dist > radius_km:
                continue

            locations.append(
                {
                    "id": f"storage-{s.id}",
                    "raw_id": str(s.id),
                    "type": "storage",
                    "name": s.name,
                    "district": s.location_text,
                    "state": None,
                    "lat": lat,
                    "lng": lng,
                    "distance_km": dist,
                    "info": f"{s.type or 'Storage facility'} · availability not confirmed",
                    "details": {
                        "type": s.type,
                        "verification_status": s.verification_status,
                        "source_kind": s.source_kind,
                        "is_demo": s.source_kind == "DEMO_SYNTHETIC",
                        "availability": "NOT_CURRENTLY_CONFIRMED",
                        "rate": "NOT_CURRENTLY_CONFIRMED",
                    },
                }
            )

    # 4. FPOs
    if category in ("all", "fpo", "fpos"):
        fq = db.query(FPOProfile, User).join(User, FPOProfile.user_id == User.id).filter(User.is_active == True)  # noqa: E712
        for fpo, u in fq.limit(50).all():
            coords = u.location_geog
            if not coords:
                continue
            try:
                from shapely import wkb

                point = wkb.loads(bytes(coords.data))
                lng, lat = point.x, point.y
            except (AttributeError, TypeError, ValueError):
                continue
            dist = calc_dist(near_lat, near_lng, lat, lng) if near_lat and near_lng else None
            if radius_km and dist is not None and dist > radius_km:
                continue

            locations.append(
                {
                    "id": f"fpo-{fpo.id}",
                    "raw_id": str(fpo.id),
                    "type": "fpo",
                    "name": fpo.organization_name or u.full_name,
                    "district": u.district,
                    "state": u.state,
                    "lat": lat,
                    "lng": lng,
                    "distance_km": dist,
                    "info": "Farmer Producer Organization",
                    "details": {
                        "members": fpo.member_count,
                        "crops": fpo.primary_crops or [],
                    },
                }
            )

    if near_lat is not None and near_lng is not None:
        locations.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"] or 0))

    counts = {
        "all": len(locations),
        "mandi": len([loc for loc in locations if loc["type"] == "mandi"]),
        "buyer": len([loc for loc in locations if loc["type"] == "buyer"]),
        "storage": len([loc for loc in locations if loc["type"] == "storage"]),
        "fpo": len([loc for loc in locations if loc["type"] == "fpo"]),
    }

    return {
        "success": True,
        "data": {
            "locations": locations,
            "counts": counts,
            "total": len(locations),
        },
        "message": f"Retrieved {len(locations)} map location markers",
        "request_id": getattr(request.state, "request_id", None),
    }
