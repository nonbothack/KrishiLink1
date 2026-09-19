import uuid

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.evidence_files import read_validated_evidence
from app.models import Transaction, User
from app.modules.trades.schemas import (
    AddTradeNoteRequest,
    LogisticsUpdateRequest,
    PaymentReportRequest,
    QualityReportRequest,
    StorageRequestBody,
    TradeEventResponse,
    TradeRoomResponse,
    TradeTransitionRequest,
    WeighmentRequest,
)
from app.modules.trades.service import (
    acknowledge_payment_report,
    add_trade_note,
    execute_trade_transition,
    get_or_create_term_snapshot,
    get_trade_room,
    record_logistics_update,
    record_quality_report,
    record_weighment,
    report_payment,
    request_trade_storage,
    upload_trade_evidence,
)

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=dict)
def list_trades(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status: str | None = None,
    crop: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Transaction)
    if user.role.lower() not in ("admin", "operator"):
        q = q.filter((Transaction.buyer_id == user.id) | (Transaction.seller_id == user.id))

    if status:
        q = q.filter(Transaction.status == status.upper())

    q = q.order_by(Transaction.created_at.desc())
    total = q.count()
    txns = q.offset((page - 1) * limit).limit(limit).all()

    items = []
    for t in txns:
        snap = get_or_create_term_snapshot(db, t)
        items.append({
            "id": str(t.id),
            "public_id": t.public_id,
            "status": t.status,
            "crop_name": snap.crop_name if snap else None,
            "grade": snap.grade if snap else None,
            "quantity": snap.quantity if snap else None,
            "unit": snap.unit if snap else None,
            "gross_value": t.gross_value if t.gross_value is not None else (snap.gross_value if snap else None),
            "created_at": t.created_at,
            "buyer_id": str(t.buyer_id),
            "seller_id": str(t.seller_id),
        })

    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
        },
        "message": "Trades retrieved successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{trade_id}/room", response_model=dict)
def get_trade_room_endpoint(
    trade_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = get_trade_room(db, trade_id, user)
    # Validate with Pydantic model for strict schema conformity
    validated = TradeRoomResponse.model_validate(room).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": "Trade room retrieved successfully",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{trade_id}/transition", response_model=dict)
def transition_trade_endpoint(
    trade_id: str,
    data: TradeTransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    room = execute_trade_transition(db, trade_id, data.to_status, user, request, data.reason)
    validated = TradeRoomResponse.model_validate(room).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": f"Trade successfully transitioned to {data.to_status.upper()}",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{trade_id}/notes", response_model=dict, status_code=201)
def add_trade_note_endpoint(
    trade_id: str,
    data: AddTradeNoteRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ev = add_trade_note(db, trade_id, user, data.note, request)
    validated = TradeEventResponse.model_validate(
        {
            "id": ev.id,
            "transaction_id": ev.transaction_id,
            "actor_id": ev.actor_id,
            "actor_role": ev.actor_role,
            "event_type": ev.event_type,
            "from_status": ev.from_status,
            "to_status": ev.to_status,
            "title": ev.title,
            "description": ev.description,
            "source_kind": ev.source_kind,
            "metadata": ev.metadata_json,
            "created_at": ev.created_at,
        }
    ).model_dump()
    return {
        "success": True,
        "data": validated,
        "message": "Note added to trade timeline",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.post("/{trade_id}/payment-reports", response_model=dict, status_code=201)
def submit_payment_report(
    trade_id: str,
    data: PaymentReportRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return report_payment(db, trade_id, user, request, data.amount, data.reference)


@router.post("/{trade_id}/payment-reports/{payment_id}/acknowledge", response_model=dict, status_code=201)
def acknowledge_payment_report_endpoint(
    trade_id: str,
    payment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return acknowledge_payment_report(db, trade_id, payment_id, user, request)


@router.post("/{trade_id}/quality-reports", response_model=dict, status_code=201)
def submit_quality_report(
    trade_id: str,
    data: QualityReportRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return record_quality_report(db, trade_id, user, request, data.kind, data.details, data.attributes)


@router.post("/{trade_id}/weighments", response_model=dict, status_code=201)
def submit_weighment(
    trade_id: str,
    data: WeighmentRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return record_weighment(db, trade_id, user, request, data.gross_quantity, data.tare_quantity, data.unit)


@router.post("/{trade_id}/logistics-updates", response_model=dict, status_code=201)
def submit_logistics_update(
    trade_id: str,
    data: LogisticsUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return record_logistics_update(db, trade_id, user, request, data.kind, data.details, data.evidence_id)


@router.post("/{trade_id}/storage-requests", response_model=dict, status_code=201)
def submit_storage_request(
    trade_id: str,
    data: StorageRequestBody,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return request_trade_storage(db, trade_id, user, request, data.facility_id, data.quantity, data.unit)


@router.post("/{trade_id}/evidence", response_model=dict, status_code=201)
async def upload_trade_evidence_endpoint(
    trade_id: str,
    request: Request,
    file: UploadFile = File(...),
    classification: str = Form("OTHER_TRADE_EVIDENCE"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content, mime_type, filename = await read_validated_evidence(file)
    return upload_trade_evidence(db, trade_id, user, request, classification, content, mime_type, filename)
