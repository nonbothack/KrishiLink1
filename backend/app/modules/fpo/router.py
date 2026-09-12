from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.models import User
from app.modules.fpo.schemas import (
    FPOAggregateLotRequest,
    FPOMemberCreateRequest,
)
from app.modules.fpo.service import FPOService

router = APIRouter(prefix="/fpo", tags=["fpo"])


@router.get("/summary", response_model=dict)
def get_fpo_summary(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("fpo", "admin")),
):
    """
    Get aggregated dashboard summary for authenticated FPO.
    """
    summary = FPOService.get_summary(db, user)
    return {
        "success": True,
        "data": summary,
        "message": "FPO summary loaded successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/members", response_model=dict)
def get_fpo_members(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("fpo", "admin")),
):
    """
    Get member farmers roster belonging to the authenticated FPO.
    """
    members = FPOService.get_members(db, user)
    return {
        "success": True,
        "data": members,
        "message": f"{len(members)} members retrieved",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/members", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_fpo_member(
    payload: FPOMemberCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("fpo", "admin")),
):
    """
    Register a new member farmer under this FPO.
    """
    member = FPOService.add_member(db, user, payload)
    return {
        "success": True,
        "data": member,
        "message": "Member registered successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/lots", response_model=dict)
def get_fpo_lots(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("fpo", "admin")),
):
    """
    Get all published lots by this FPO including received buyer offers.
    """
    lots = FPOService.get_fpo_lots(db, user)
    return {
        "success": True,
        "data": lots,
        "message": f"{len(lots)} lots retrieved",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/aggregate-lot", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_aggregated_lot(
    payload: FPOAggregateLotRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("fpo", "admin")),
):
    """
    Aggregate member produce and publish a bulk collective lot to the marketplace.
    """
    lot = FPOService.aggregate_and_create_lot(db, user, payload)
    return {
        "success": True,
        "data": lot,
        "message": "Aggregated collective lot published successfully",
        "request_id": getattr(request.state, "request_id", None),
    }
