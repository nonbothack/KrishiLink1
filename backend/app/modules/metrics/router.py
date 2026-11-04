from fastapi import APIRouter, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.core.config import settings

router = APIRouter(tags=["observability"])

REQUEST_COUNT = Counter("krishilink_requests_total", "Total requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("krishilink_request_duration_seconds", "Request latency")


@router.get("/metrics", include_in_schema=False)
def metrics(request: Request):
    if settings.env == "production":
        token = request.headers.get("X-Metrics-Token") or request.query_params.get("token")
        if not settings.metrics_token or token != settings.metrics_token:
            raise HTTPException(status_code=403, detail="Forbidden")
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
