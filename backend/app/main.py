import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import generic_exception_handler, validation_exception_handler
from app.core.otel import init_otel
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.crops.router import router as crops_router
from app.modules.disputes.router import router as disputes_router
from app.modules.fpo.router import router as fpo_router
from app.modules.health.router import router as health_router
from app.modules.lots.router import router as lots_router
from app.modules.markets.router import router as markets_router
from app.modules.matching.router import router as matching_router
from app.modules.metrics.router import REQUEST_COUNT, REQUEST_LATENCY
from app.modules.metrics.router import router as metrics_router
from app.modules.notifications.router import router as notifications_router
from app.modules.offers.router import router as offers_router
from app.modules.prices.router import router as prices_router
from app.modules.reservations.router import router as reservations_router
from app.modules.storage.router import router as storage_router
from app.modules.transactions.router import router as transactions_router
from app.modules.users.router import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.agmarknet_api_key or settings.mandi_api_key:
        from app.core.database import SessionLocal
        from app.modules.prices.sync_service import sync_daily_prices
        with SessionLocal() as db:
            try:
                sync_daily_prices(db)
            except Exception:
                logger.warning("Initial market sync failed; dated records remain available")
    yield


def create_app() -> FastAPI:
    settings.validate_prod()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    init_otel(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = rid
        start = time.time()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        elapsed = round((time.time() - start) * 1000, 2)
        response.headers["X-Process-Time-ms"] = str(elapsed)
        REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=response.status_code).inc()
        REQUEST_LATENCY.observe(time.time() - start)
        return response

    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]

    app.include_router(health_router, prefix=settings.api_v1_prefix)
    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(crops_router, prefix=settings.api_v1_prefix)
    app.include_router(markets_router, prefix=settings.api_v1_prefix)
    app.include_router(prices_router, prefix=settings.api_v1_prefix)
    app.include_router(lots_router, prefix=settings.api_v1_prefix)
    app.include_router(fpo_router, prefix=settings.api_v1_prefix)
    app.include_router(matching_router, prefix=settings.api_v1_prefix)
    app.include_router(offers_router, prefix=settings.api_v1_prefix)
    app.include_router(reservations_router, prefix=settings.api_v1_prefix)
    app.include_router(transactions_router, prefix=settings.api_v1_prefix)
    app.include_router(storage_router, prefix=settings.api_v1_prefix)
    app.include_router(disputes_router, prefix=settings.api_v1_prefix)
    app.include_router(notifications_router, prefix=settings.api_v1_prefix)
    app.include_router(admin_router, prefix=settings.api_v1_prefix)
    app.include_router(metrics_router)

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "success": True,
            "data": {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"},
            "message": "KrishiLink API 2.0 — see /docs",
            "request_id": None,
        }

    return app


app = create_app()
