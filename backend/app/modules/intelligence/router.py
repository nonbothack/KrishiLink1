from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.rate_limit import rate_limit
from app.models import (
    AuditLog,
    BuyerProfile,
    Crop,
    CropVariety,
    DataSourceRegistry,
    Dispute,
    Lot,
    Market,
    Offer,
    PriceAlertRule,
    PriceObservation,
    PriceSource,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.prices.provider import PARSER_VERSION
from app.modules.prices.router import SOURCE_KEY, observations

router = APIRouter(prefix="/intelligence", tags=["intelligence"])
MIN_TRADES_FOR_HISTORY_LABEL = 5
FRESHNESS_DAYS = 7


class PriceAlertCreate(BaseModel):
    crop_id: uuid.UUID
    market_id: uuid.UUID
    variety_id: uuid.UUID | None = None
    grade: str | None = Field(default=None, pattern="^(A|B|C|UNSPECIFIED)$")
    threshold: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    direction: str = Field(pattern="^(AT_OR_ABOVE|AT_OR_BELOW)$")
    unit: str = "INR/quintal"


def _envelope(request: Request, data: dict, message: str) -> dict:
    return {"success": True, "data": data, "message": message,
            "request_id": getattr(request.state, "request_id", None)}


def _uuid_or_404(value: str, message: str):
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(404, message) from None


def _farmer_or_fpo(user: User) -> None:
    if user.role.lower() != "farmer":
        raise HTTPException(403, "Farmer account required")


@router.get("/forecasts/{crop_id}")
def forecast_eligibility(
    crop_id: str,
    request: Request,
    market_id: str | None = None,
    horizon_days: int = Query(7, ge=7, le=30),
    db: Session = Depends(get_db),
):
    """Public forecast contract; abstains unless a validated model is active.

    Packet 11 intentionally registers no model: the locally available series
    are demo/unprovenanced and fail the model card's eligibility gates.
    """
    crop_uuid = _uuid_or_404(crop_id, "Crop not found")
    crop = db.get(Crop, crop_uuid)
    if not crop or not crop.is_active or not crop.is_tradable:
        raise HTTPException(404, "Crop not found")
    market = None
    if market_id:
        market_uuid = _uuid_or_404(market_id, "Market not found")
        market = db.get(Market, market_uuid)
        if not market or not market.is_active:
            raise HTTPException(404, "Market not found")
    if horizon_days not in (7, 14, 30):
        raise HTTPException(422, "Supported forecast horizons are 7, 14, and 30 days")
    enabled = settings.intelligence_forecasts_enabled
    return _envelope(request, {
        "crop_id": str(crop.id), "crop": crop.name,
        "market_id": str(market.id) if market else None,
        "market": market.name if market else None,
        "horizon_days": horizon_days,
        "eligibility": "FORECAST_UNAVAILABLE",
        "abstention_reason": "FORECASTS_DISABLED" if not enabled else "NO_ACTIVE_VALIDATED_MODEL",
        "forecast": None,
        "model_version": None,
        "latest_source_observation_date": None,
        "methodology_version": "packet11-evidence-gates-v1",
    }, "Not enough validated evidence for a forecast")


@router.get("/demand/{crop_id}")
def demand_eligibility(crop_id: str, request: Request, db: Session = Depends(get_db)):
    crop_uuid = _uuid_or_404(crop_id, "Crop not found")
    crop = db.get(Crop, crop_uuid)
    if not crop or not crop.is_active or not crop.is_tradable:
        raise HTTPException(404, "Crop not found")
    # Requirements currently hold free-text locations while lots use district
    # and optional coordinates. Combining those denominators would mislead.
    return _envelope(request, {
        "crop_id": str(crop.id), "crop": crop.name,
        "status": "INSUFFICIENT_COMPARABLE_DATA",
        "reason": "REQUIREMENT_AND_SUPPLY_GEOGRAPHY_NOT_COMPARABLE",
        "open_requirement_quantity": None,
        "listed_supply_quantity": None,
        "unit": "quintal",
        "demand_signal": None,
    }, "Not enough comparable marketplace activity to estimate demand")


@router.get("/trust/{buyer_id}")
def trust_facts(
    buyer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    buyer_uuid = _uuid_or_404(buyer_id, "Buyer not found")
    buyer = db.get(User, buyer_uuid)
    if not buyer or buyer.role.lower() != "buyer" or buyer.deleted_at is not None:
        raise HTTPException(404, "Buyer not found")
    if user.id != buyer.id and user.role.lower() not in ("farmer", "fpo", "admin", "operator"):
        raise HTTPException(404, "Buyer not found")
    if not settings.intelligence_trust_summaries_enabled:
        raise HTTPException(404, "Trust summaries are unavailable")

    eligible = (
        db.query(Transaction.id, Transaction.created_at)
        .join(TradeTermSnapshot, TradeTermSnapshot.transaction_id == Transaction.id)
        .filter(
            Transaction.buyer_id == buyer.id,
            Transaction.seller_id != buyer.id,
            Transaction.status == "COMPLETED",
            TradeTermSnapshot.buyer_id == Transaction.buyer_id,
            TradeTermSnapshot.seller_id == Transaction.seller_id,
            TradeTermSnapshot.quantity > 0,
            TradeTermSnapshot.price_per_unit > 0,
            TradeTermSnapshot.gross_value > 0,
        )
        .order_by(Transaction.created_at)
        .all()
    )
    trade_ids = [row.id for row in eligible]
    dispute_rows = []
    if trade_ids:
        dispute_rows = db.query(Dispute.status).filter(Dispute.transaction_id.in_(trade_ids)).all()
    profile = db.query(BuyerProfile).filter(BuyerProfile.user_id == buyer.id).first()
    count = len(eligible)
    if count == 0:
        history_state = "NO_PLATFORM_HISTORY_YET"
    elif count < MIN_TRADES_FOR_HISTORY_LABEL:
        history_state = "LIMITED_HISTORY"
    else:
        history_state = "DESCRIPTIVE_HISTORY"
    dispute_counts: dict[str, int] = {}
    for (status,) in dispute_rows:
        normalized = (status or "UNKNOWN").upper()
        dispute_counts[normalized] = dispute_counts.get(normalized, 0) + 1
    return _envelope(request, {
        "buyer_id": str(buyer.id),
        "business_verification_status": profile.business_verification_status if profile else "UNVERIFIED",
        "business_verification_is_separate_from_trade_history": True,
        "eligible_completed_trade_count": count,
        "history_state": history_state,
        "minimum_count_for_descriptive_history_label": MIN_TRADES_FOR_HISTORY_LABEL,
        "sample_period": {
            "from": eligible[0].created_at.isoformat() if eligible and eligible[0].created_at else None,
            "through": eligible[-1].created_at.isoformat() if eligible and eligible[-1].created_at else None,
        },
        "disputes_recorded_against_eligible_completed_trades": sum(dispute_counts.values()),
        "dispute_status_counts": dispute_counts,
        "dispute_denominator": count,
        "dispute_attribution": "No fault or outcome is inferred; counts are descriptive only.",
        "payment_timing": "UNAVAILABLE",
        "payment_timing_reason": "No qualifying provider-verified settlement evidence is available.",
        "composite_score": None,
        "rates_or_ranking": None,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_version": "trust-facts-v1",
    }, "Evidence-backed buyer history facts")


@router.get("/lots/{lot_id}/channels")
def lot_channel_comparison(
    lot_id: str,
    request: Request,
    market_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lot_uuid = _uuid_or_404(lot_id, "Lot not found")
    lot = db.get(Lot, lot_uuid)
    if not lot or lot.deleted_at is not None:
        raise HTTPException(404, "Lot not found")
    if user.role.lower() not in ("admin", "operator") and lot.owner_id != user.id:
        raise HTTPException(404, "Lot not found")
    if (lot.unit or "").strip().lower() not in ("quintal", "qtl"):
        raise HTTPException(422, "Lot unit is not comparable to reported INR/quintal prices")

    channels: list[dict] = []
    offers = db.query(Offer).filter(
        Offer.lot_id == lot.id,
        Offer.status == "PENDING",
        Offer.expires_at > datetime.now(timezone.utc),
    ).order_by(Offer.created_at.desc()).all()
    for offer in offers:
        quantity = Decimal(str(offer.quantity))
        price = Decimal(str(offer.price_per_unit))
        channels.append({
            "kind": "DIRECT_BUYER_OFFER", "evidence_id": str(offer.id),
            "label": "Current buyer offer", "price_per_unit": str(price),
            "unit": "INR/quintal", "quantity": str(quantity),
            "gross": str((price * quantity).quantize(Decimal("0.01"))),
            "known_costs": [], "unknown_costs": ["freight", "commission", "storage"],
            "known_net": None, "net_status": "unavailable",
        })

    selected_market = None
    if market_id:
        market_uuid = _uuid_or_404(market_id, "Market not found")
        selected_market = db.get(Market, market_uuid)
        if not selected_market or not selected_market.is_active:
            raise HTTPException(404, "Market not found")
        if lot.crop_id:
            variety_match = PriceObservation.variety_id.is_(None) if lot.variety_id is None else PriceObservation.variety_id == lot.variety_id
            grade_value = None if lot.grade == "UNSPECIFIED" else lot.grade
            grade_match = PriceObservation.grade.is_(None) if grade_value is None else func.lower(PriceObservation.grade) == grade_value.lower()
            row = (
                db.query(PriceObservation, Crop, Market, PriceSource, DataSourceRegistry)
                .join(Crop, PriceObservation.crop_id == Crop.id)
                .join(Market, PriceObservation.market_id == Market.id)
                .join(PriceSource, PriceObservation.source_id == PriceSource.id)
                .join(DataSourceRegistry, PriceSource.registry_id == DataSourceRegistry.id)
                .filter(
                    PriceObservation.crop_id == lot.crop_id, PriceObservation.market_id == selected_market.id,
                    variety_match, grade_match, PriceObservation.price_unit == "INR/quintal",
                    PriceObservation.quality_status.in_(("HIGH", "MEDIUM")),
                    PriceSource.adapter == PARSER_VERSION, PriceSource.is_active.is_(True),
                    DataSourceRegistry.source_key == SOURCE_KEY, DataSourceRegistry.is_active.is_(True),
                )
                .order_by(PriceObservation.price_date.desc(), PriceObservation.fetched_at.desc())
                .first()
            )
            if row:
                observation, crop, market, _source, registry = row
                today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
                age_days = (today - observation.price_date).days if observation.price_date else None
                if age_days is not None and 0 <= age_days <= FRESHNESS_DAYS:
                    price = Decimal(str(observation.modal_price))
                    quantity = Decimal(str(lot.quantity))
                    channels.append({
                        "kind": "OFFICIAL_REPORTED_MARKET_PRICE", "evidence_id": str(observation.id),
                        "label": "Latest comparable reported market price", "market": market.name,
                        "price_per_unit": str(price), "unit": "INR/quintal", "quantity": str(quantity),
                        "gross": str((price * quantity).quantize(Decimal("0.01"))),
                        "reported_date": observation.price_date.isoformat(), "source": registry.name,
                        "known_costs": [], "unknown_costs": ["transport", "commission", "storage"],
                        "known_net": None, "net_status": "unavailable",
                    })

    return _envelope(request, {
        "lot_id": str(lot.id), "crop": lot.crop_name,
        "unit": "INR/quintal", "channels": channels,
        "net_ranking_enabled": False,
        "ranking_reason": "One or more relevant channel costs are unknown; gross values are not ranked as net proceeds.",
        "assumptions": [],
        "comparability_note": "Reported market observations are descriptive; a buyer offer is a contractual proposal. Neither is a guaranteed net realization.",
        "unavailable_channels": ["MSP", "eNAM", "processor", "storage-linked"] ,
    }, "Comparable evidence only; no net winner is available")


@router.post("/price-alerts", status_code=201)
@rate_limit(max_requests=10, window_seconds=60, key_prefix="rl_price_alert")
def create_price_alert(
    data: PriceAlertCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _farmer_or_fpo(user)
    cached = check_idempotency(request, db, user=user)
    if cached:
        return cached.response_body
    if not settings.intelligence_price_alerts_enabled:
        raise HTTPException(503, "Price alerts are temporarily unavailable")
    if data.unit != "INR/quintal":
        raise HTTPException(422, "Price alerts currently require INR/quintal")
    crop = db.get(Crop, data.crop_id)
    market = db.get(Market, data.market_id)
    if not crop or not crop.is_active or not crop.is_tradable:
        raise HTTPException(422, "Select an active canonical crop")
    if not market or not market.is_active:
        raise HTTPException(422, "Select an active canonical market")
    if data.variety_id:
        variety = db.get(CropVariety, data.variety_id)
        if not variety or variety.crop_id != crop.id or not variety.is_active:
            raise HTTPException(422, "Variety does not belong to the selected crop")
    if db.query(PriceAlertRule).filter(PriceAlertRule.user_id == user.id, PriceAlertRule.is_active.is_(True)).count() >= 20:
        raise HTTPException(409, "You can have at most 20 active price alerts")
    grade = None if data.grade in (None, "UNSPECIFIED") else data.grade
    rule = PriceAlertRule(
        id=uuid.uuid4(), user_id=user.id, crop_id=crop.id, market_id=market.id,
        variety_id=data.variety_id, grade=grade, threshold=data.threshold,
        direction=data.direction, price_unit="INR/quintal", is_active=True, is_armed=True,
    )
    db.add(rule)
    db.flush()
    db.add(AuditLog(
        actor_id=str(user.id), action="price_alert.create", entity="price_alert_rules", entity_id=str(rule.id),
        after={"crop_id": str(crop.id), "market_id": str(market.id), "threshold": str(data.threshold),
               "direction": data.direction, "unit": "INR/quintal"},
        request_id=getattr(request.state, "request_id", None),
    ))
    body = _envelope(request, _alert_projection(rule, crop, market), "Price alert created")
    save_idempotency(request, db, 201, body, user=user, commit=False)
    db.commit()
    return body


def _alert_projection(rule: PriceAlertRule, crop: Crop | None = None, market: Market | None = None) -> dict:
    return {
        "id": str(rule.id), "crop_id": str(rule.crop_id), "crop": crop.name if crop else None,
        "market_id": str(rule.market_id), "market": market.name if market else None,
        "variety_id": str(rule.variety_id) if rule.variety_id else None, "grade": rule.grade,
        "threshold": str(rule.threshold), "direction": rule.direction, "unit": rule.price_unit,
        "is_active": bool(rule.is_active), "is_armed": bool(rule.is_armed),
        "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


@router.get("/price-alerts")
def list_price_alerts(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _farmer_or_fpo(user)
    rows = db.query(PriceAlertRule).filter(PriceAlertRule.user_id == user.id).order_by(PriceAlertRule.created_at.desc()).all()
    data = []
    for row in rows:
        data.append(_alert_projection(row, db.get(Crop, row.crop_id), db.get(Market, row.market_id)))
    return _envelope(request, {"items": data, "total": len(data)}, "Your reported-price alerts")


@router.delete("/price-alerts/{alert_id}")
def disable_price_alert(alert_id: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _farmer_or_fpo(user)
    alert_uuid = _uuid_or_404(alert_id, "Alert not found")
    rule = db.query(PriceAlertRule).filter(PriceAlertRule.id == alert_uuid, PriceAlertRule.user_id == user.id).with_for_update().first()
    if not rule:
        raise HTTPException(404, "Alert not found")
    if rule.is_active:
        rule.is_active = False
        db.add(AuditLog(actor_id=str(user.id), action="price_alert.disable", entity="price_alert_rules",
                        entity_id=str(rule.id), request_id=getattr(request.state, "request_id", None)))
        db.commit()
    return _envelope(request, {"id": str(rule.id), "is_active": False}, "Price alert disabled")


@router.get("/sale-window/{crop_id}")
def sale_window_abstention(crop_id: str, request: Request, db: Session = Depends(get_db)):
    crop_uuid = _uuid_or_404(crop_id, "Crop not found")
    crop = db.get(Crop, crop_uuid)
    if not crop or not crop.is_active or not crop.is_tradable:
        raise HTTPException(404, "Crop not found")
    return _envelope(request, {
        "crop_id": str(crop.id), "crop": crop.name, "recommendation": "NOT_ENOUGH_DATA",
        "sell_now": None, "wait": None,
        "reason": "No validated forecast and complete, evidenced waiting-cost inputs are available.",
        "cost_of_waiting_included": False, "methodology_version": "sale-window-v1",
    }, "Not enough reliable evidence to compare selling now with waiting")


@router.get("/requirements/{crop_id}")
def requirement_activity_abstention(crop_id: str, request: Request, db: Session = Depends(get_db)):
    # Kept as an explicit signal for clients: free-text buyer locations cannot
    # currently be reconciled to district-scoped listed supply.
    return demand_eligibility(crop_id, request, db)


@router.get("/history/{crop_name}")
def descriptive_history(crop_name: str, request: Request, market: str, variety: str | None = None,
                        grade: str | None = None, db: Session = Depends(get_db)):
    query = observations(db, crop_name, market, variety=variety, grade=grade)
    query = query.filter(PriceObservation.quality_status.in_(("HIGH", "MEDIUM")))
    rows = query.order_by(PriceObservation.price_date.desc(), PriceObservation.fetched_at.desc()).limit(60).all()
    if not rows:
        return _envelope(request, {"eligibility": "INSUFFICIENT_DATA", "observations": [], "statistics": None,
                                   "abstention_reason": "NO_QUALIFYING_OFFICIAL_OBSERVATIONS"}, "No comparable official observations are available")
    dimensions = {(row[0].variety_id, (row[0].grade or "").strip().casefold(), row[0].price_unit, row[3].adapter) for row in rows}
    markets = {row[0].market_id for row in rows}
    if len(dimensions) != 1 or len(markets) != 1:
        return _envelope(request, {"eligibility": "INSUFFICIENT_DATA", "observations": [], "statistics": None,
                                   "abstention_reason": "PRODUCT_UNIT_OR_SOURCE_DIMENSIONS_DIFFER"}, "Select one comparable crop, market, variety, grade and unit")
    by_date = {}
    for row in rows:
        by_date.setdefault(row[0].price_date, row)
    ordered = sorted(by_date.items())
    latest_date = ordered[-1][0]
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if (today - latest_date).days > FRESHNESS_DAYS:
        return _envelope(request, {"eligibility": "INSUFFICIENT_DATA", "observations": [], "statistics": None,
                                   "abstention_reason": "LATEST_OBSERVATION_STALE",
                                   "latest_observation_date": latest_date.isoformat()}, "The latest comparable observation is stale")
    series = ordered[-7:]
    if len(series) < 7:
        return _envelope(request, {"eligibility": "INSUFFICIENT_DATA", "observations": [
            {"date": day.isoformat(), "modal_price": str(row[0].modal_price)} for day, row in series
        ], "statistics": None, "observation_count": len(series),
                                   "abstention_reason": "FEWER_THAN_SEVEN_DISTINCT_REPORTED_DATES"}, "Not enough comparable history for a seven-observation movement")
    first_price = Decimal(str(series[0][1][0].modal_price))
    last_price = Decimal(str(series[-1][1][0].modal_price))
    movement = ((last_price - first_price) / first_price * Decimal("100")).quantize(Decimal("0.01"))
    return _envelope(request, {
        "eligibility": "DESCRIPTIVE_ONLY", "observation_count": len(series),
        "first_observation_date": series[0][0].isoformat(), "latest_observation_date": latest_date.isoformat(),
        "movement_pct": str(movement), "movement_kind": "CHANGE_ACROSS_SEVEN_MOST_RECENT_DISTINCT_REPORT_DATES",
        "latest_price": str(last_price), "unit": series[-1][1][0].price_unit,
        "source": series[-1][1][4].name,
        "observations": [{"date": day.isoformat(), "modal_price": str(row[0].modal_price)} for day, row in series],
        "forecast": None, "recommendation": None,
    }, "Descriptive reported-price movement; not a forecast")
