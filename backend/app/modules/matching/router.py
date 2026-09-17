import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Lot, Match
from app.modules.matching.schemas import MatchRequest
from app.modules.matching.service import find_candidates, refresh_matches

router = APIRouter(prefix="/matches", tags=["matching"])

def owned_lot(db, lot_id, user):
    try:
        lot = db.get(Lot, uuid.UUID(lot_id))
    except ValueError:
        lot = None
    if not lot:
        raise HTTPException(404, "Lot not found")
    if user.role not in ("admin", "operator") and str(lot.owner_id) != str(user.id):
        raise HTTPException(403, "This lot belongs to another account")
    return lot



@router.post("/refresh", response_model=dict)
def refresh(data: MatchRequest, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    owned_lot(db, data.lot_id, user)
    candidates = refresh_matches(db, data.lot_id)
    if candidates is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    return {
        "success": True,
        "data": [
            {
                "buyer_id": str(c["buyer"].id),
                "buyer_name": c["buyer"].full_name,
                "score": c["score"],
                "component_scores": c["component_scores"],
                "explanation": c["explanation"],
                "ruleset_version": c["explanation"].get("ruleset_version") or c["ruleset"].version,
            }
            for c in candidates
        ],
        "message": f"{len(candidates)} matches",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("", response_model=dict)
def list_matches(
    request: Request, db: Session = Depends(get_db), lot_id: str = Query(...), user=Depends(get_current_user)
):
    owned_lot(db, lot_id, user)
    lot, candidates = find_candidates(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    # also return persisted matches if any
    persisted = db.query(Match).filter(Match.lot_id == lot.id).order_by(Match.final_score.desc()).all()
    if persisted:
        data = [
            {
                "id": str(m.id),
                "buyer_id": str(m.buyer_id),
                "final_score": m.final_score,
                "component_scores": m.component_scores,
                "explanation": m.explanation,
                "ruleset_version": m.ruleset_version,
            }
            for m in persisted
        ]
        return {
            "success": True,
            "data": data,
            "message": f"{len(data)} persisted matches",
            "request_id": getattr(request.state, "request_id", None),
        }
    return {
        "success": True,
        "data": [
            {
                "buyer_id": str(c["buyer"].id),
                "buyer_name": c["buyer"].full_name,
                "score": c["score"],
                "component_scores": c["component_scores"],
                "explanation": c["explanation"],
            }
            for c in candidates
        ],
        "message": f"{len(candidates)} matches (live)",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{match_id}/explanation", response_model=dict)
def explain(match_id: str, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.get(Match, match_id)
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    lot = owned_lot(db, str(m.lot_id), user)
    return {
        "success": True,
        "data": {
            "match_id": str(m.id),
            "lot_id": str(m.lot_id),
            "lot_public_id": lot.public_id if lot else None,
            "buyer_id": str(m.buyer_id),
            "ruleset_version": m.ruleset_version,
            "component_scores": m.component_scores,
            "final_score": m.final_score,
            "explanation": m.explanation,
        },
        "message": "Explanation",
        "request_id": getattr(request.state, "request_id", None),
    }
