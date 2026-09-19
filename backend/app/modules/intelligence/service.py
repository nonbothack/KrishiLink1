from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Crop,
    DataSourceRegistry,
    Market,
    PriceAlertEvaluation,
    PriceAlertRule,
    PriceObservation,
    PriceSource,
)
from app.modules.notifications.service import NotificationService
from app.modules.prices.provider import PARSER_VERSION
from app.modules.prices.router import SOURCE_KEY

ALERT_PRICE_UNIT = "INR/quintal"
ALERT_FRESHNESS_DAYS = 7


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def evaluate_price_alerts(db: Session, *, now: datetime | None = None) -> dict[str, int]:
    """Evaluate new official reports once per rule/observation, in a DB transaction.

    Rules are locked on PostgreSQL; unique evaluation receipts are the final
    duplicate guard. A qualifying observation fires once until a later
    non-qualifying report re-arms the rule.
    """
    now = _as_utc(now or datetime.now(timezone.utc)) or datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo("Asia/Kolkata")).date()
    rules = (
        db.query(PriceAlertRule)
        .filter(PriceAlertRule.is_active.is_(True))
        .order_by(PriceAlertRule.id)
        .with_for_update(skip_locked=True)
        .all()
    )
    evaluated = 0
    triggered = 0
    for rule in rules:
        report_query = (
            db.query(PriceObservation, Crop, Market, PriceSource, DataSourceRegistry)
            .join(Crop, PriceObservation.crop_id == Crop.id)
            .join(Market, PriceObservation.market_id == Market.id)
            .join(PriceSource, PriceObservation.source_id == PriceSource.id)
            .join(DataSourceRegistry, PriceSource.registry_id == DataSourceRegistry.id)
            .filter(
                PriceObservation.crop_id == rule.crop_id,
                PriceObservation.market_id == rule.market_id,
                PriceObservation.variety_id == rule.variety_id,
                func.lower(func.coalesce(PriceObservation.grade, ""))
                == (rule.grade or "").lower(),
                PriceObservation.price_unit == rule.price_unit,
                PriceObservation.quality_status.in_(("HIGH", "MEDIUM")),
                PriceSource.adapter == PARSER_VERSION,
                PriceSource.is_active.is_(True),
                DataSourceRegistry.source_key == SOURCE_KEY,
                DataSourceRegistry.is_active.is_(True),
                Crop.is_active.is_(True),
                Crop.is_tradable.is_(True),
                PriceObservation.price_date >= today - timedelta(days=ALERT_FRESHNESS_DAYS),
                func.coalesce(PriceObservation.fetched_at, PriceObservation.created_at) >= rule.created_at,
                ~db.query(PriceAlertEvaluation.id).filter(
                    PriceAlertEvaluation.alert_id == rule.id,
                    PriceAlertEvaluation.observation_id == PriceObservation.id,
                ).exists(),
            )
            .order_by(func.coalesce(PriceObservation.fetched_at, PriceObservation.created_at), PriceObservation.id)
            .limit(500)
        )
        for observation, crop, market, source, registry in report_query.all():
            report_date = observation.price_date
            if not report_date or (today - report_date).days > ALERT_FRESHNESS_DAYS:
                continue
            modal = Decimal(str(observation.modal_price))
            threshold = Decimal(str(rule.threshold))
            qualifies = modal >= threshold if rule.direction == "AT_OR_ABOVE" else modal <= threshold
            fire = bool(rule.is_armed and qualifies)
            db.add(PriceAlertEvaluation(alert_id=rule.id, observation_id=observation.id, triggered=fire))
            evaluated += 1

            if fire:
                rule.is_armed = False
                rule.last_triggered_at = now
                NotificationService.create_notification(
                    db=db,
                    user_id=rule.user_id,
                    type_="price_alert",
                    title="Reported price alert",
                    message=(
                        f"{crop.name} at {market.name}: reported modal price "
                        f"₹{modal:.2f}/quintal on {report_date.isoformat()} ({registry.name})."
                    ),
                    related_id=observation.id,
                    outbox=True,
                    metadata={
                        "crop": crop.name, "market": market.name, "modal_price": str(modal),
                        "unit": rule.price_unit, "reported_date": report_date.isoformat(),
                        "source": registry.name, "observation_id": str(observation.id),
                        "threshold": str(threshold), "direction": rule.direction,
                    },
                )
                triggered += 1
            elif not qualifies:
                # Hysteresis: a later observation on the opposite side of the
                # configured threshold re-arms the next crossing.
                rule.is_armed = True

    db.commit()
    return {"evaluated": evaluated, "triggered": triggered}
