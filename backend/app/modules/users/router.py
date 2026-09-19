from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models import AuditLog, BuyerProfile, ConsentRecord, User, VerificationRecord
from app.modules.auth.identity import CURRENT_POLICIES
from app.modules.auth.schemas import LocationUpdateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=dict)
def get_me(request: Request, user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/me/verifications", response_model=dict)
def list_my_verifications(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.user_id == user.id)
        .order_by(VerificationRecord.created_at.desc())
        .all()
    )
    latest = {}
    for record in records:
        latest.setdefault(
            record.dimension,
            {
                "dimension": record.dimension,
                "status": record.status,
                "method": record.method,
                "provider": record.provider,
                "checked_at": record.checked_at.isoformat() if record.checked_at else None,
                "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            },
        )
    for dimension, verified_at in (("phone", user.phone_verified_at), ("email", user.email_verified_at)):
        latest.setdefault(
            dimension,
            {"dimension": dimension, "status": "VERIFIED" if verified_at else "UNVERIFIED", "checked_at": verified_at.isoformat() if verified_at else None},
        )
    return {
        "success": True,
        "data": {"items": list(latest.values())},
        "message": "Verification states",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.put("/me/location", response_model=dict)
def update_my_location(
    data: LocationUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.location_geog = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
    user.coordinate_source = "explicit_gps"
    user.coordinate_accuracy_m = data.accuracy_m
    user.coordinate_confidence = None
    now = datetime.now(timezone.utc)
    db.query(ConsentRecord).filter(
        ConsentRecord.user_id == user.id,
        ConsentRecord.policy_type == "location_gps",
        ConsentRecord.withdrawn_at.is_(None),
    ).update({ConsentRecord.withdrawn_at: now}, synchronize_session=False)
    db.add(
        ConsentRecord(
            user_id=user.id,
            policy_type="location_gps",
            policy_version=CURRENT_POLICIES["privacy_notice"]["version"],
            source="profile_location_settings",
            user_agent=request.headers.get("user-agent", "")[:500] or None,
        )
    )
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.location_gps_set",
            entity="users",
            entity_id=str(user.id),
            after={"source": "explicit_gps", "accuracy_recorded": data.accuracy_m is not None},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    db.commit()
    return {
        "success": True,
        "data": {"saved": True, "source": "explicit_gps", "accuracy_m": data.accuracy_m},
        "message": "Location saved",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.delete("/me/location", response_model=dict)
def clear_my_location(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    user.location_geog = None
    user.coordinate_source = None
    user.coordinate_confidence = None
    user.coordinate_accuracy_m = None
    db.query(ConsentRecord).filter(
        ConsentRecord.user_id == user.id,
        ConsentRecord.policy_type == "location_gps",
        ConsentRecord.withdrawn_at.is_(None),
    ).update({ConsentRecord.withdrawn_at: now}, synchronize_session=False)
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.location_gps_cleared",
            entity="users",
            entity_id=str(user.id),
            after={"outcome": "cleared"},
            request_id=getattr(request.state, "request_id", None),
        )
    )
    db.commit()
    return {"success": True, "data": {"saved": False}, "message": "Location removed"}


@router.get("/buyers", response_model=dict)
def list_buyers(
    request: Request,
    db: Session = Depends(get_db),
    district: str | None = None,
    crop: str | None = None,
    limit: int = Query(6, ge=1, le=20),
):
    # This is a public business directory, not an account/person directory.
    # Business verification is required before public listing; account identity,
    # contact details, user IDs and precise coordinates are never projected.
    q = db.query(User, BuyerProfile).join(BuyerProfile, BuyerProfile.user_id == User.id).filter(
        User.role.in_(["buyer", "BUYER"]),
        User.is_active.is_(True),
        BuyerProfile.business_verification_status == "VERIFIED",
    ).order_by(BuyerProfile.business_name, BuyerProfile.id)
    if district and district.lower() != "all":
        q = q.filter(User.district.ilike(f"%{district}%"))
    buyers = q.limit(limit).all()

    data = []
    for b, profile in buyers:
        item = {
            "business_name": profile.business_name,
            "type": profile.business_type,
            "crops": profile.crops_interested or [],
            "district": b.district,
            "state": b.state,
            "business_verification": "verified",
        }
        if crop and crop.lower() not in {name.lower() for name in item["crops"]}:
            continue
        data.append(item)

    return {
        "success": True,
        "data": data,
        "message": f"{len(data)} buyers found",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/admin-only", response_model=dict)
def admin_only(user: User = Depends(require_role("admin"))):
    return {"success": True, "data": {"message": f"Hello admin {user.full_name}"}, "request_id": None}
