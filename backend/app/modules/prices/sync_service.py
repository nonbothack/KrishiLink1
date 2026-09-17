"""Import reported observations verbatim. Never interpolate missing dates or prices."""
import hashlib
import json
import logging
import uuid
from datetime import date, datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Crop, Market, PriceObservation, PriceSource

logger = logging.getLogger(__name__)
RESOURCE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
PARSER_VERSION = "agmarknet-record-v3"


def fetch_live_agmarknet_records(limit: int = 5000) -> list[dict]:
    key = settings.agmarknet_api_key or settings.mandi_api_key
    if not key:
        return []
    try:
        response = httpx.get(RESOURCE_URL, params={"api-key": key, "format": "json", "limit": limit}, timeout=12)
        response.raise_for_status()
        return response.json().get("records", [])
    except (httpx.HTTPError, ValueError):
        logger.warning("Market price source unavailable; retaining dated observations")
        return []


def ingest_records(db: Session, records: list[dict]) -> int:
    source = db.query(PriceSource).filter(PriceSource.adapter == PARSER_VERSION).first()
    if not source:
        source = PriceSource(id=uuid.uuid4(), name="Agmarknet reported observations", url=RESOURCE_URL, adapter=PARSER_VERSION, is_active=True)
        db.add(source)
        db.flush()
    count = 0
    seen = set()
    for raw in records:
        try:
            reported = datetime.strptime(raw["arrival_date"], "%d/%m/%Y").date()
            low, modal, high = (float(raw[k]) for k in ("min_price", "modal_price", "max_price"))
            if not (0 < low <= modal <= high) or reported > date.today():
                continue
            name = str(raw["commodity"]).strip()
            market_name = str(raw["market"]).strip()
            district, state = str(raw["district"]).strip(), str(raw["state"]).strip()
            if not all((name, market_name, district, state)):
                continue
        except (ValueError, KeyError, TypeError):
            continue
        # Preserve commodity names: paddy and rice, varieties and grades are not interchangeable.
        if name.lower() in ("soyabean", "soybean"):
            name = "Soybean"
        crop = db.query(Crop).filter(Crop.name.ilike(name)).first()
        if not crop:
            crop = Crop(id=uuid.uuid4(), name=name, category="Produce", unit="quintal")
            db.add(crop)
            db.flush()
        market = db.query(Market).filter(Market.name == market_name, Market.district == district, Market.state == state).first()
        if not market:
            market = Market(id=uuid.uuid4(), name=market_name, district=district, state=state, is_active=True)
            db.add(market)
            db.flush()
        identity = (str(crop.id), str(market.id), reported)
        if identity in seen:
            continue  # Schema stores one observation per crop/market/date/source; do not average varieties.
        seen.add(identity)
        existing = db.query(PriceObservation).filter(PriceObservation.crop_id == crop.id, PriceObservation.market_id == market.id, PriceObservation.price_date == reported, PriceObservation.source_id == source.id).first()
        if existing:
            continue
        digest = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
        db.add(PriceObservation(
            id=uuid.uuid4(), crop_id=crop.id, market_id=market.id, price_date=reported,
            min_price=low, modal_price=modal, max_price=high, source_id=source.id,
            source_record_id=digest, source_url=RESOURCE_URL, raw_payload_hash=digest,
            parser_version=PARSER_VERSION, normalization_version="verbatim-v1",
            retrieved_at=datetime.now(timezone.utc), quality_status="MEDIUM",
        ))
        count += 1
    db.commit()
    return count


def sync_daily_prices(db: Session, force: bool = False) -> dict:
    records = fetch_live_agmarknet_records()
    if not records:
        return {"status": "unavailable", "inserted": 0}
    return {"status": "success", "inserted": ingest_records(db, records)}


def calibrate_15day_history(db: Session, force: bool = False) -> dict:
    # Compatibility for scheduled jobs. Historical prices must never be rewritten.
    return {"status": "disabled", "calibrated": 0}

