import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.idempotency import check_idempotency, save_idempotency
from app.models import User
from app.modules.fpo.schemas import (
    FPOAggregateLotRequest,
    FPOIntakeCorrectionRequest,
    FPOIntakeRequest,
    FPOMemberCreateRequest,
    FPOMemberUpdateRequest,
    FPOPoolContributionAddRequest,
    FPOPoolCreateRequest,
    FPOPoolPublishRequest,
)
from app.modules.fpo.service import FPOService

router = APIRouter(prefix="/fpo", tags=["fpo"])


def _body(request: Request, data, message: str):
    return {"success": True, "data": data, "message": message, "request_id": getattr(request.state, "request_id", None)}


@router.get("/export")
def export_fpo_data(
    request: Request,
    format: str = Query("json", pattern="^(json|csv)$"),
    domain: str = Query("all", pattern="^(all|members|intakes|pools|contributions|lots|trades|allocations|audit)$"),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("fpo")),
):
    """Export only the authenticated FPO owner's operational data.

    JSON ``all`` exports carry a manifest and checksum. CSV is intentionally
    one bounded domain at a time so callers cannot accidentally receive an
    unbounded, opaque archive. Secrets, credentials, provider payloads and
    unrelated staff notes are never part of the projection.
    """
    data = FPOService.export_data(db, user, domain=domain)
    if format == "json":
        body = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return Response(content=body, media_type="application/json")

    if domain == "all":
        raise HTTPException(422, "CSV export requires one domain; use JSON for the manifest export")
    rows = data.get("rows", [])
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=sorted({key for row in rows for key in row} or {"empty"}))
    writer.writeheader()
    for row in rows:
        # Formula-like values are escaped before leaving the application.
        writer.writerow({key: _csv_safe(value) for key, value in row.items()})
    filename = f"krishilink-{domain}-export.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _csv_safe(value):
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.get_summary(db, user), "FPO summary loaded")


@router.get("/members")
def members(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.get_members(db, user), "FPO members loaded")


@router.post("/members", status_code=status.HTTP_201_CREATED)
def add_member(payload: FPOMemberCreateRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.add_member(db, user, payload), "Member registered")


@router.get("/members/{member_id}")
def member_detail(member_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.get_member(db, user, member_id), "Member loaded")


@router.patch("/members/{member_id}")
def update_member(member_id: str, payload: FPOMemberUpdateRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.update_member(db, user, member_id, payload), "Member updated")


def _read_member_csv(body: bytes) -> list[dict]:
    if len(body) > 1_048_576:
        raise HTTPException(413, "CSV file exceeds 1 MiB")
    try:
        text = body.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "CSV must use UTF-8 encoding") from exc
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        required = {"member_code", "farmer_name", "phone", "village", "district", "primary_crop", "grade", "land_acres"}
        headers = set(reader.fieldnames or [])
        if headers != required or len(reader.fieldnames or []) != len(required):
            raise HTTPException(422, "CSV must contain exactly the required member columns")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise HTTPException(422, "CSV row has an invalid number of columns")
            rows.append(row)
            if len(rows) > 1000:
                raise HTTPException(413, "CSV is limited to 1,000 member rows")
        return rows
    except csv.Error as exc:
        raise HTTPException(422, "Malformed CSV") from exc


@router.post("/members/import/preview")
async def preview_member_import(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    try:
        if int(request.headers.get("content-length", "0")) > 1_048_576:
            raise HTTPException(413, "CSV file exceeds 1 MiB")
    except ValueError:
        raise HTTPException(400, "Invalid Content-Length")
    body = await request.body()
    result = FPOService.import_members(db, user, _read_member_csv(body), preview=True)
    return _body(request, result, "Import preview ready")


@router.post("/members/import", status_code=status.HTTP_201_CREATED)
async def import_members(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    try:
        if int(request.headers.get("content-length", "0")) > 1_048_576:
            raise HTTPException(413, "CSV file exceeds 1 MiB")
    except ValueError:
        raise HTTPException(400, "Invalid Content-Length")
    body = await request.body()
    result = FPOService.import_members(db, user, _read_member_csv(body), preview=False)
    response = _body(request, result, "Member import completed")
    save_idempotency(request, db, 201, response, user=user, commit=False)
    db.commit()
    return response


@router.get("/intakes")
def intakes(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.list_intakes(db, user), "Intake ledger loaded")


@router.post("/intakes", status_code=status.HTTP_201_CREATED)
def create_intake(payload: FPOIntakeRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    data = FPOService.create_intake(db, user, payload)
    response = _body(request, data, "Intake receipt created")
    save_idempotency(request, db, 201, response, user=user, commit=False)
    db.commit()
    return response


@router.post("/intakes/{intake_id}/corrections", status_code=status.HTTP_201_CREATED)
def correct_intake(intake_id: str, payload: FPOIntakeCorrectionRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.correct_intake(db, user, intake_id, payload), "Corrected intake receipt created")


@router.get("/intakes/{intake_id}/receipt")
def receipt(intake_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    for intake in FPOService.list_intakes(db, user):
        if intake["id"] == intake_id:
            return _body(request, intake, "Intake receipt loaded")
    raise HTTPException(404, "Intake receipt not found")


@router.get("/pools")
def pools(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.list_pools(db, user), "Pools loaded")


@router.post("/pools/{pool_id}/contributions", status_code=status.HTTP_201_CREATED)
def add_pool_contribution(pool_id: str, payload: FPOPoolContributionAddRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    data = FPOService.add_pool_contribution(db, user, pool_id, payload.intake_id, payload.quantity)
    return _body(request, data, "Pool contribution added")


@router.delete("/pools/{pool_id}/contributions/{contribution_id}")
def remove_pool_contribution(pool_id: str, contribution_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    data = FPOService.remove_pool_contribution(db, user, pool_id, contribution_id)
    return _body(request, data, "Pool contribution removed")


@router.get("/lots")
def lots(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.get_fpo_lots(db, user), "FPO lots loaded")


@router.get("/trades")
def trades(request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.get_fpo_trades(db, user), "FPO trades loaded")


@router.post("/pools", status_code=status.HTTP_201_CREATED)
def create_pool(payload: FPOPoolCreateRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.create_pool(db, user, payload), "Pool created")


@router.post("/pools/{pool_id}/publish", status_code=status.HTTP_201_CREATED)
def publish_pool(pool_id: str, payload: FPOPoolPublishRequest, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.publish_pool(db, user, pool_id, payload), "Pool published")


@router.get("/trades/{transaction_id}/trace")
def trade_trace(transaction_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role("fpo", "admin"))):
    return _body(request, FPOService.trade_trace(db, user, transaction_id), "Trade trace loaded")


@router.post("/aggregate-lot", status_code=status.HTTP_409_CONFLICT)
def retired_aggregate_lot(payload: FPOAggregateLotRequest, request: Request, user: User = Depends(require_role("fpo", "admin"))):
    raise HTTPException(409, "Aggregate lots must be created from persisted intake pools")
