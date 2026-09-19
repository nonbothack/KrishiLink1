from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import StorageFacility

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("", response_model=dict)
def list_storage(
    request: Request, db: Session = Depends(get_db), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)
):
    # Only review-approved facility identities may be discovered. Capacity and
    # rates are intentionally omitted: this model has no freshness/provider
    # contract proving that those values are currently bookable.
    q = db.query(StorageFacility).filter(
        StorageFacility.status == "ACTIVE",
        StorageFacility.verification_status == "VERIFIED",
        StorageFacility.source_kind != "UNKNOWN_LEGACY",
    )
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(s.id),
            "name": s.name,
            "type": s.type,
            "location_text": s.location_text,
            "verification_status": s.verification_status,
            "source_kind": s.source_kind,
            "is_demo": s.source_kind == "DEMO_SYNTHETIC",
            "availability": "NOT_CURRENTLY_CONFIRMED",
            "rate": "NOT_CURRENTLY_CONFIRMED",
        }
        for s in items
    ]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} facilities",
        "request_id": getattr(request.state, "request_id", None),
    }
