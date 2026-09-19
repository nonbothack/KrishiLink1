import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_optional_current_user, require_role
from app.core.idempotency import check_idempotency, save_idempotency
from app.models import (
    AuditLog,
    Crop,
    CropVariety,
    DataSourceRegistry,
    FPOPool,
    Lot,
    Market,
    Offer,
    OutboxEvent,
    PriceObservation,
    PriceSource,
    Transaction,
    User,
)
from app.modules.crops.service import resolve_crop
from app.modules.lots.service import calculate_farmer_earnings
from app.modules.lots.units import UNIT_TO_QUINTAL
from app.modules.notifications.service import NotificationService
from app.modules.prices.provider import PARSER_VERSION
from app.modules.prices.sync_service import freshness_state

router = APIRouter(prefix="/lots", tags=["lots"])


class CreateLotRequest(BaseModel):
    crop: str = Field(min_length=2)
    variety_id: str | None = None
    grade: str = Field(default="UNSPECIFIED", pattern="^(A|B|C|UNSPECIFIED)$")
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = "quintal"
    asking_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    location_text: str | None = Field(default=None, min_length=2, max_length=300)
    district: str | None = None
    harvest_date: date | None = None
    available_from: date | None = None
    available_until: date | None = None


class LotQuoteRequest(BaseModel):
    crop: str = Field(min_length=2)
    variety_id: str | None = None
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = "quintal"
    asking_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    district: str | None = None


class UpdateLotRequest(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    unit: str | None = None
    asking_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    grade: str | None = Field(default=None, pattern="^(A|B|C|UNSPECIFIED)$")
    location_text: str | None = Field(default=None, min_length=2, max_length=300)
    district: str | None = None
    available_from: date | None = None
    available_until: date | None = None


QUANTITY_QUANTUM = Decimal("0.01")
MAX_GROSS_VALUE = Decimal("9999999999.99")


def _canonical_lot_values(crop, quantity: Decimal, unit: str, asking_price: Decimal | None):
    unit = unit.strip().lower()
    supported = {str(value).strip().lower() for value in (crop.valid_units or [crop.unit or "quintal"])}
    if unit not in supported or unit not in UNIT_TO_QUINTAL:
        raise HTTPException(422, "Unit is not supported for this crop")
    normalized = quantity * UNIT_TO_QUINTAL[unit]
    if normalized.quantize(QUANTITY_QUANTUM) != normalized:
        raise HTTPException(422, "Quantity is too precise for the canonical quintal unit")
    if normalized < Decimal("0.01") or normalized > Decimal("1000000.00"):
        raise HTTPException(422, "Canonical quantity is outside the supported range")
    canonical_price = None
    if asking_price is not None:
        # Asking prices are always contracted per canonical quintal, independent of
        # the farmer's entered quantity unit.
        canonical_price = asking_price
        if canonical_price > Decimal("10000000.00"):
            raise HTTPException(422, "Asking price is outside the supported range")
        canonical_price = canonical_price.quantize(Decimal("0.01"))
        if normalized * canonical_price > MAX_GROSS_VALUE:
            raise HTTPException(422, "Indicative gross exceeds the supported currency precision")
    return normalized.quantize(QUANTITY_QUANTUM), canonical_price, unit


def _lot_projection(lot: Lot) -> dict:
    return {
        "id": str(lot.id),
        "public_id": lot.public_id,
        "crop": lot.crop_name,
        "crop_id": str(lot.crop_id) if lot.crop_id else None,
        "quantity": str(lot.quantity),
        "unit": lot.unit or "quintal",
        "original_quantity": str(lot.original_quantity) if lot.original_quantity is not None else None,
        "original_unit": lot.original_unit,
        "grade": lot.grade,
        "status": lot.status,
        "location": lot.location_text,
        "district": lot.district,
        "asking_price": str(lot.asking_price) if lot.asking_price is not None else None,
        "expected_price": str(lot.asking_price) if lot.asking_price is not None else None,
        "available_from": lot.available_from.isoformat() if lot.available_from else None,
        "available_until": lot.available_until.isoformat() if lot.available_until else None,
        "created_at": lot.created_at.isoformat() if lot.created_at else None,
    }


@router.post("/quote", response_model=dict)
def quote_lot(
    data: LotQuoteRequest,
    request: Request,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("farmer", "fpo")),
):
    try:
        crop = db.query(Crop).filter_by(id=uuid.UUID(data.crop), is_active=True, is_tradable=True).first()
    except (ValueError, TypeError):
        crop = None
    if not crop:
        crop = resolve_crop(db, data.crop, include_inactive=False)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    variety = None
    if data.variety_id:
        try:
            variety_uuid = uuid.UUID(data.variety_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid crop variety")
        variety = db.query(CropVariety).filter(
            CropVariety.id == variety_uuid,
            CropVariety.crop_id == crop.id,
            CropVariety.is_active.is_(True),
            CropVariety.is_tradable.is_(True),
        ).first()
        if not variety:
            raise HTTPException(status_code=422, detail="Crop variety does not belong to this crop")
    quantity, price, unit = _canonical_lot_values(crop, data.quantity, data.unit, data.asking_price)

    observation_query = (
        db.query(PriceObservation, Market, DataSourceRegistry)
        .join(Market, PriceObservation.market_id == Market.id)
        .join(PriceSource, PriceObservation.source_id == PriceSource.id)
        .join(DataSourceRegistry, PriceSource.registry_id == DataSourceRegistry.id)
        .filter(
            PriceObservation.crop_id == crop.id,
            PriceObservation.price_unit == "INR/quintal",
            PriceSource.adapter == PARSER_VERSION,
            PriceSource.is_active.is_(True),
            DataSourceRegistry.source_key == "agmarknet-daily-reported-prices",
            DataSourceRegistry.is_active.is_(True),
        )
    )
    if data.district:
        observation_query = observation_query.filter(Market.district.ilike(f"%{data.district.strip()}%"))
    if variety:
        observation_query = observation_query.filter(PriceObservation.variety_id == variety.id)
    matched = observation_query.order_by(PriceObservation.price_date.desc(), PriceObservation.id).first()
    reference = None
    warning = False
    deviation_pct = None
    if matched:
        observation, market, source = matched
        fresh_state = freshness_state(observation.price_date)
        reference = {
            "modal_price": str(observation.modal_price),
            "unit": observation.price_unit,
            "crop": crop.name,
            "market": market.name,
            "district": market.district,
            "price_date": observation.price_date.isoformat() if observation.price_date else None,
            "source": source.name,
            "freshness_state": fresh_state,
            "location_verified": bool(
                market.verification_status == "verified" and market.is_active
                and market.latitude is not None and market.longitude is not None
                and market.coordinate_confidence is not None and market.coordinate_confidence >= Decimal("0.85")
            ),
        }
        if price is not None and fresh_state != "stale" and Decimal(str(observation.modal_price)) > 0:
            deviation_pct = (abs(price - Decimal(str(observation.modal_price))) / Decimal(str(observation.modal_price)) * Decimal("100")).quantize(Decimal("0.01"))
            warning = deviation_pct > settings.lot_price_deviation_warning_pct
    gross = (quantity * price).quantize(Decimal("0.01")) if price is not None else None
    return {
        "success": True,
        "data": {
            "crop_id": str(crop.id), "crop": crop.name,
            "entered_quantity": str(data.quantity), "entered_unit": unit,
            "canonical_quantity": str(quantity), "canonical_unit": "quintal",
            "asking_price_per_quintal": str(price) if price is not None else None,
            "indicative_gross": str(gross) if gross is not None else None,
            "reference_price": reference,
            "deviation_pct": str(deviation_pct) if deviation_pct is not None else None,
            "price_warning": warning,
            "warning_threshold_pct": str(settings.lot_price_deviation_warning_pct),
        },
        "message": "Server-validated lot quote",
        "request_id": getattr(request.state, "request_id", None),
    }


def gen_public_id(db: Session):
    return f"KL-LOT-{uuid.uuid4().hex[:10].upper()}"


@router.post("", response_model=dict, status_code=201)
def create_lot(
    data: CreateLotRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo", "admin")),
):
    if user.role.lower() == "fpo":
        raise HTTPException(status_code=409, detail="FPO lots must be published from a persisted intake pool")
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    # Accept the canonical registry ID from the UI and legacy canonical names from API clients.
    try:
        crop = db.query(Crop).filter_by(id=uuid.UUID(data.crop), is_active=True, is_tradable=True).first()
    except (ValueError, TypeError):
        crop = None
    if not crop:
        crop = resolve_crop(db, data.crop, include_inactive=False)
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
    variety = None
    if data.variety_id:
        try:
            variety_uuid = uuid.UUID(data.variety_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid crop variety")
        variety = db.query(CropVariety).filter(
            CropVariety.id == variety_uuid,
            CropVariety.crop_id == crop.id,
            CropVariety.is_active.is_(True),
            CropVariety.is_tradable.is_(True),
        ).first()
        if not variety:
            raise HTTPException(status_code=422, detail="Crop variety does not belong to this crop")
    quantity, asking_price, original_unit = _canonical_lot_values(crop, data.quantity, data.unit, data.asking_price)
    location_text = (data.location_text or user.location or user.district or data.district or "").strip()
    if len(location_text) < 2:
        raise HTTPException(status_code=422, detail="Set a location before publishing this lot")
    if data.available_from and data.available_until and data.available_until < data.available_from:
        raise HTTPException(status_code=422, detail="Availability end date cannot be before start date")
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    now_utc = datetime.now(timezone.utc)
    lot = Lot(
        id=uuid.uuid4(),
        public_id=gen_public_id(db),
        owner_id=user.id,
        crop_id=crop.id,
        crop_name=crop.name,
        variety_id=variety.id if variety else None,
        grade=data.grade,
        quantity=quantity,
        unit="quintal",
        original_quantity=data.quantity,
        original_unit=original_unit,
        asking_price=asking_price,
        location_text=location_text,
        district=data.district or user.district,
        harvest_date=data.harvest_date,
        available_from=data.available_from or today,
        available_until=data.available_until or (today + timedelta(days=14)),
        status="PUBLISHED",
        created_at=now_utc,
        updated_at=now_utc,
    )
    db.add(lot)
    db.flush()
    db.refresh(lot)
    body = {
        "success": True,
        "data": {
            "id": str(lot.id),
            "public_id": lot.public_id,
            "crop": lot.crop_name,
            "quantity": str(lot.quantity),
            "unit": lot.unit or "quintal",
            "original_quantity": str(lot.original_quantity),
            "original_unit": lot.original_unit,
            "grade": lot.grade,
            "asking_price": str(lot.asking_price) if lot.asking_price is not None else None,
            "expected_price": str(lot.asking_price) if lot.asking_price is not None else None,
            "location": lot.location_text,
            "location_text": lot.location_text,
            "district": lot.district,
            "status": lot.status,
            "created_at": lot.created_at.isoformat() if lot.created_at else None,
        },
        "message": "Lot created",
        "request_id": getattr(request.state, "request_id", None),
    }
    save_idempotency(request, db, 201, body, user=user, commit=False)
    db.commit()
    return body


@router.get("", response_model=dict)
def list_lots(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
    farmer_id: str | None = None,
    status: str | None = None,
    crop: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    q = db.query(Lot).filter(Lot.deleted_at.is_(None))
    is_owner_role = user is not None and user.role.lower() in ("farmer", "fpo")
    if is_owner_role:
        if farmer_id and farmer_id != str(user.id):
            raise HTTPException(status_code=403, detail="You may only list your own lots")
        q = q.filter(Lot.owner_id == user.id)
    elif user is None or user.role.lower() not in ("admin", "operator"):
        q = q.filter(Lot.status.in_(["PUBLISHED", "PARTIALLY_ALLOCATED", "active", "matched"]))
    if farmer_id:
        try:
            q = q.filter(Lot.owner_id == uuid.UUID(farmer_id))
        except ValueError:
            raise HTTPException(422, "Invalid farmer ID")
    if status:
        q = q.filter(Lot.status == status)
    if crop:
        q = q.filter(Lot.crop_name.ilike(crop))
    q = q.order_by(Lot.created_at.desc().nullslast(), Lot.id.desc())
    total = q.count()
    items = q.offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "id": str(l.id),
            "public_id": l.public_id,
            "crop": l.crop_name,
            "quantity": float(l.quantity),
            "unit": l.unit or "quintal",
            "grade": l.grade,
            "status": l.status,
            "location": l.location_text,
            "district": l.district,
            "asking_price": float(l.asking_price) if l.asking_price else None,
            "expected_price": float(l.asking_price) if l.asking_price else None,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in items
    ]
    return {
        "success": True,
        "data": {"items": data, "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit},
        "message": f"{len(data)} lots",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/mine", response_model=dict)
def list_my_lots(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo")),
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    q = db.query(Lot).filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None))
    if status:
        q = q.filter(func.upper(Lot.status) == status.upper())
    total = q.count()
    rows = q.order_by(Lot.created_at.desc().nullslast(), Lot.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "success": True,
        "data": {"items": [_lot_projection(lot) for lot in rows], "total": total, "page": page, "limit": limit,
                 "pages": (total + limit - 1) // limit if total else 0},
        "message": f"{len(rows)} of your lots",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.patch("/{lot_id}", response_model=dict)
def update_lot(
    lot_id: str,
    data: UpdateLotRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo")),
):
    try:
        parsed_id = uuid.UUID(lot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Lot not found")
    lot = db.query(Lot).filter(Lot.id == parsed_id).with_for_update().first()
    if not lot or lot.owner_id != user.id or lot.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Lot not found")
    if user.role.lower() == "fpo":
        raise HTTPException(status_code=409, detail="FPO lot terms are controlled by the published intake pool")
    if lot.status.upper() != "PUBLISHED":
        raise HTTPException(status_code=409, detail="This lot can no longer be edited")
    active_offers = db.query(Offer).filter(Offer.lot_id == lot.id, Offer.status.in_(["PENDING", "COUNTERED"])).count()
    accepted = db.query(Offer).filter(Offer.lot_id == lot.id, Offer.status == "ACCEPTED").count()
    if active_offers or accepted:
        raise HTTPException(status_code=409, detail="This lot has an active or accepted offer and cannot be changed")
    changes = data.model_dump(exclude_unset=True)
    crop = db.get(Crop, lot.crop_id) if lot.crop_id else resolve_crop(db, lot.crop_name, include_inactive=False)
    stored_unit = lot.original_unit or lot.unit or "quintal"
    target_unit = changes.get("unit") or stored_unit
    entered_quantity = changes.get("quantity")
    if entered_quantity is None:
        if changes.get("unit") and changes["unit"] != stored_unit:
            raise HTTPException(status_code=422, detail="Send quantity when changing its unit")
        entered_quantity = lot.original_quantity if lot.original_quantity is not None else Decimal(str(lot.quantity))
        target_unit = stored_unit
    if crop is None:
        raise HTTPException(status_code=409, detail="The lot crop is no longer available in the crop registry")
    canonical_quantity, canonical_price, normalized_unit = _canonical_lot_values(
        crop, entered_quantity, target_unit, changes.get("asking_price")
    )
    effective_price = canonical_price if "asking_price" in changes else lot.asking_price
    if effective_price is not None and canonical_quantity * Decimal(str(effective_price)) > MAX_GROSS_VALUE:
        raise HTTPException(status_code=422, detail="Indicative gross exceeds the supported currency precision")
    before = _lot_projection(lot)
    lot.quantity = canonical_quantity
    lot.unit = "quintal"
    lot.original_quantity = entered_quantity
    lot.original_unit = normalized_unit
    lot.asking_price = canonical_price if "asking_price" in changes else lot.asking_price
    for field in ("grade", "location_text", "district", "available_from", "available_until"):
        if field in changes:
            setattr(lot, field, changes[field])
    effective_start = changes.get("available_from", lot.available_from)
    effective_end = changes.get("available_until", lot.available_until)
    if effective_start and effective_end and effective_end < effective_start:
        raise HTTPException(status_code=422, detail="Availability end date cannot be before start date")
    lot.updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor_id=str(user.id), action="lot.updated", entity="lots", entity_id=str(lot.id),
                    before=before, after=_lot_projection(lot), request_id=getattr(request.state, "request_id", None)))
    db.commit()
    db.refresh(lot)
    return {"success": True, "data": _lot_projection(lot), "message": "Lot updated", "request_id": getattr(request.state, "request_id", None)}


@router.post("/{lot_id}/withdraw", response_model=dict)
def withdraw_lot(
    lot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo")),
):
    try:
        parsed_id = uuid.UUID(lot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Lot not found")
    lot = db.query(Lot).filter(Lot.id == parsed_id).with_for_update().first()
    if not lot or lot.owner_id != user.id or lot.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Lot not found")
    if lot.status.upper() != "PUBLISHED":
        raise HTTPException(status_code=409, detail="This lot cannot be withdrawn in its current state")
    if db.query(Transaction).filter(Transaction.lot_id == lot.id).count():
        raise HTTPException(status_code=409, detail="A lot with an accepted trade cannot be withdrawn")
    pool = None
    if user.role.lower() == "fpo":
        pool = db.query(FPOPool).filter(FPOPool.lot_id == lot.id).with_for_update().first()
    pending = db.query(Offer).filter(Offer.lot_id == lot.id, Offer.status.in_(["PENDING", "COUNTERED"])).with_for_update().all()
    lot.status = "CANCELLED"
    lot.updated_at = datetime.now(timezone.utc)
    if pool is not None:
        pool.status = "WITHDRAWN"
    for offer in pending:
        offer.status = "CANCELLED"
        NotificationService.create_notification(
            db=db, user_id=offer.buyer_id, type_="lot_withdrawn", title="Listing withdrawn",
            message=f"The {lot.crop_name} listing is no longer available.", related_id=offer.id, outbox=True,
        )
        db.add(OutboxEvent(aggregate="offers", aggregate_id=str(offer.id), event_type="offer.cancelled_by_lot_withdrawal",
                           payload={"offer_id": str(offer.id), "lot_id": str(lot.id)}))
    db.add(AuditLog(actor_id=str(user.id), action="lot.withdrawn", entity="lots", entity_id=str(lot.id),
                    after={"status": "CANCELLED", "cancelled_offers": len(pending)}, request_id=getattr(request.state, "request_id", None)))
    db.commit()
    return {"success": True, "data": {"id": str(lot.id), "status": lot.status}, "message": "Lot withdrawn", "request_id": getattr(request.state, "request_id", None)}


@router.get("/farmer-summary", response_model=dict)
def get_farmer_summary(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
):
    if not user:
        return {
            "success": True,
            "data": {
                "active_listings": 0,
                "active_listings_sub": "No active listings",
                "offers_received": 0,
                "offers_received_sub": "0 pending offers",
                "pending_payments": 0,
                "pending_payments_formatted": "₹0",
                "pending_payments_sub": "0 transactions pending",
            },
            "message": "Unauthenticated or demo farmer summary",
            "request_id": getattr(request.state, "request_id", None),
        }

    user_lots = db.query(Lot).filter(Lot.owner_id == user.id, Lot.deleted_at.is_(None)).all()
    active_lots = [l for l in user_lots if (l.status or "").lower() in ("published", "active")]
    crops_summary = []
    for l in active_lots[:2]:
        crops_summary.append(f"{int(l.quantity)}{l.unit or 'qtl'} {l.crop_name}")
    sub_listings = ", ".join(crops_summary) if crops_summary else "No active lots"

    user_lot_ids = [l.id for l in user_lots]
    offers = (
        db.query(Offer)
        .filter((Offer.owner_id == user.id) | (Offer.lot_id.in_(user_lot_ids) if user_lot_ids else False))
        .all()
    ) if (user_lots or user) else []
    pending_offers = [o for o in offers if (o.status or "").lower() == "pending"]
    accepted_offers = [o for o in offers if (o.status or "").lower() == "accepted"]
    sub_offers = f"{len(pending_offers)} pending, {len(accepted_offers)} accepted"

    txns = (
        db.query(Transaction)
        .filter(
            Transaction.seller_id == user.id,
            Transaction.status.in_([
                "PAYMENT_PENDING", "PAYMENT_CONFIRMED", "PROCESSING", "READY_FOR_DISPATCH",
                "IN_TRANSIT", "DELIVERED", "payment_pending", "payment_received"
            ]),
        )
        .all()
    )
    total_val = sum(float(t.gross_value or 0) for t in txns)
    if total_val >= 100000:
        formatted_val = f"₹{total_val / 100000:.1f}L"
    else:
        formatted_val = f"₹{total_val:,.0f}"
    sub_payments = f"{len(txns)} transaction{'s' if len(txns) != 1 else ''} pending"

    return {
        "success": True,
        "data": {
            "active_listings": len(active_lots),
            "active_listings_sub": sub_listings,
            "offers_received": len(offers),
            "offers_received_sub": sub_offers,
            "pending_payments": total_val,
            "pending_payments_formatted": formatted_val,
            "pending_payments_sub": sub_payments,
        },
        "message": "Farmer summary retrieved",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{lot_id}", response_model=dict)
def get_lot(
    lot_id: str, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo", "buyer", "admin", "operator")),
):
    lot = None
    try:
        u = uuid.UUID(lot_id)
        lot = db.query(Lot).filter(Lot.id == u).first()
    except (ValueError, AttributeError):
        pass

    if not lot:
        lot = db.query(Lot).filter(Lot.public_id == lot_id).first()

    if not lot or lot.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Lot not found")
    if user.role.lower() not in ("admin", "operator") and lot.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Lot not found")

    return {
        "success": True,
        "data": _lot_projection(lot),
        "message": "OK",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/public/{public_id}", response_model=dict)
def public_lot(public_id: str, request: Request, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.public_id == public_id, Lot.deleted_at.is_(None)).first()
    if not lot or lot.status.upper() not in ("PUBLISHED", "PARTIALLY_ALLOCATED"):
        raise HTTPException(status_code=404, detail="Lot not found")
    return {
        "success": True,
        "data": {
            "public_id": lot.public_id,
            "crop": lot.crop_name,
            "grade": lot.grade,
            "quantity": float(lot.quantity),
            "unit": lot.unit,
            "status": lot.status,
            "district": lot.district,
            "created_at": lot.created_at.isoformat() if lot.created_at else None,
        },
        "message": "Public lot",
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/{lot_id}/earnings", response_model=dict)
def get_lot_earnings(
    lot_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("farmer", "fpo", "admin")),
):
    try:
        data = calculate_farmer_earnings(db, lot_id, str(user.id))
        return {
            "success": True,
            "data": data,
            "message": "Earnings calculated successfully",
            "request_id": getattr(request.state, "request_id", None),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
