import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import DataSourceRegistry, Lot, Market, Offer, PriceObservation, PriceSource
from app.modules.prices.provider import PARSER_VERSION
from app.modules.prices.sync_service import freshness_state


def calculate_farmer_earnings(db: Session, lot_id: str, farmer_id: str) -> dict:
    """
    Calculate estimated earnings for an existing farmer produce lot.
    """
    try:
        u = uuid.UUID(lot_id)
        lot = db.query(Lot).filter(Lot.id == u).first()
    except ValueError:
        lot = db.query(Lot).filter(Lot.public_id == lot_id).first()

    if not lot:
        raise ValueError("Lot doesn't exist")

    if str(lot.owner_id) != str(farmer_id):
        raise ValueError("Farmer doesn't own the lot")

    if lot.quantity is None or lot.quantity <= 0:
        raise ValueError("Invalid/zero quantity")

    if (lot.unit or "quintal").lower() != "quintal":
        raise ValueError("Legacy lot unit cannot be compared safely")

    reference = (
        db.query(PriceObservation, Market, DataSourceRegistry)
        .join(Market, PriceObservation.market_id == Market.id)
        .join(PriceSource, PriceObservation.source_id == PriceSource.id)
        .join(DataSourceRegistry, PriceSource.registry_id == DataSourceRegistry.id)
        .filter(
            PriceObservation.crop_id == lot.crop_id,
            PriceObservation.price_unit == "INR/quintal",
            PriceSource.adapter == PARSER_VERSION,
            PriceSource.is_active.is_(True),
            DataSourceRegistry.source_key == "agmarknet-daily-reported-prices",
            DataSourceRegistry.is_active.is_(True),
            Market.is_active.is_(True),
        )
        .filter(Market.district.ilike(f"%{lot.district}%") if lot.district else True)
        .order_by(PriceObservation.price_date.desc(), PriceObservation.id)
        .first()
    )
    if not reference or freshness_state(reference[0].price_date) == "stale":
        raise ValueError("No recent official comparable market price is available")
    reference_price = Decimal(str(reference[0].modal_price))
    if reference_price <= 0:
        raise ValueError("Official comparable market price is invalid")

    now = datetime.now(timezone.utc)
    offers = db.query(Offer).filter(Offer.lot_id == lot.id, Offer.status.in_(["PENDING", "pending"])).all()
    offers = [
        offer for offer in offers
        if offer.expires_at is None or (offer.expires_at.replace(tzinfo=timezone.utc) if offer.expires_at.tzinfo is None else offer.expires_at) > now
    ]
    if not offers:
        raise ValueError("Lot has no buyer offers")

    best_offer_value = Decimal("0")
    market_value = Decimal("0")
    for o in offers:
        if o.quantity is not None and o.price_per_unit is not None:
            quantity = Decimal(str(o.quantity))
            price = Decimal(str(o.price_per_unit))
            if quantity > 0 and price > 0 and quantity <= Decimal(str(lot.quantity)):
                val = (quantity * price).quantize(Decimal("0.01"))
                comparable = (quantity * reference_price).quantize(Decimal("0.01"))
                if val > best_offer_value:
                    best_offer_value = val
                    market_value = comparable

    if best_offer_value == 0:
        raise ValueError("Lot has no buyer offers")

    potential_additional_earnings = (best_offer_value - market_value).quantize(Decimal("0.01"))

    return {
        "market_value": float(market_value),
        "best_offer_value": float(best_offer_value),
        "potential_additional_earnings": float(potential_additional_earnings),
        "reference_market": reference[1].name,
        "reference_price_date": reference[0].price_date.isoformat(),
        "reference_source": reference[2].name,
        "unit": "quintal",
    }
