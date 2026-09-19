import time
from datetime import datetime, timedelta, timezone

import redis as redis_lib
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import check_db, get_db
from app.models import DataSourceRegistry, PriceObservation, PriceSource

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "success": True,
        "data": {
            "status": "ok",
            "version": settings.app_version,
            "mode": "demo" if settings.demo_mode else "live",
            "env": settings.env,
        },
        "message": f"KrishiLink API v{settings.app_version} is running",
        "request_id": None,
    }


@router.get("/health/detailed")
def detailed_health(request: Request, db: Session = Depends(get_db)):
    checks: dict[str, str] = {}
    overall = "HEALTHY"

    db_ok = check_db()
    checks["database"] = "HEALTHY" if db_ok else "DOWN"
    if not db_ok:
        overall = "DEGRADED"

    try:
        r = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
        checks["redis"] = "HEALTHY"
    except Exception:
        checks["redis"] = "DOWN"
        overall = "DEGRADED"

    checks["api"] = "HEALTHY"
    checks["worker"] = "UNKNOWN"
    price_pipeline: dict[str, str | None] = {
        "status": "unavailable", "last_success_at": None, "last_failure_at": None,
        "latest_reported_date": None,
    }
    if db_ok:
        try:
            source = db.query(DataSourceRegistry).filter_by(source_key="agmarknet-daily-reported-prices").first()
            latest_date = db.query(func.max(PriceObservation.price_date)).join(
                PriceSource, PriceObservation.source_id == PriceSource.id
            ).filter(PriceSource.adapter == "agmarknet-data-gov-v1").scalar()
            configured = bool(settings.agmarknet_api_key or settings.mandi_api_key)
            last_success = source.last_success_at if source else None
            if last_success and last_success.tzinfo is None:
                last_success = last_success.replace(tzinfo=timezone.utc)
            sla = source.freshness_sla_seconds if source and source.freshness_sla_seconds else 86400
            stale = not last_success or datetime.now(timezone.utc) - last_success > timedelta(seconds=sla)
            price_pipeline = {
                "status": "not_configured" if not configured else (
                    "stale" if stale else (source.last_run_status if source else "pending")
                ),
                "last_success_at": source.last_success_at.isoformat() if source and source.last_success_at else None,
                "last_failure_at": source.last_failure_at.isoformat() if source and source.last_failure_at else None,
                "latest_reported_date": latest_date.isoformat() if latest_date else None,
            }
        except Exception:
            db.rollback()
            price_pipeline["status"] = "unavailable"

    return {
        "success": True,
        "data": {
            "status": overall,
            "version": settings.app_version,
            "checks": checks,
            "price_pipeline": price_pipeline,
            "timestamp": time.time(),
        },
        "message": f"System status: {overall}",
        "request_id": request.headers.get("X-Request-ID"),
    }


@router.get("/health/ready")
def readiness(request: Request):
    """Fail-closed readiness probe for load balancers and deploy smoke tests.

    Liveness is intentionally separate: an API process may be alive while its
    database or queue dependencies are unavailable, but it is not ready to
    receive authenticated or transactional traffic in that state.
    """
    checks: dict[str, str] = {"api": "HEALTHY"}
    database_ok = check_db()
    checks["database"] = "HEALTHY" if database_ok else "DOWN"
    redis_ok = False
    try:
        client = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        redis_ok = bool(client.ping())
    except Exception:
        redis_ok = False
    checks["redis"] = "HEALTHY" if redis_ok else "DOWN"
    ready = database_ok and redis_ok
    payload = {
        "success": ready,
        "data": {"ready": ready, "checks": checks, "version": settings.app_version, "env": settings.env},
        "message": "Ready" if ready else "Not ready",
        "request_id": request.headers.get("X-Request-ID"),
    }
    return JSONResponse(status_code=200 if ready else 503, content=payload)
