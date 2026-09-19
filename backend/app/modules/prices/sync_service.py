"""Idempotent persistence and Redis coordination for reported AGMARKNET prices."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.rate_limit import get_redis
from app.models import Crop, CropVariety, DataSourceRegistry, IngestionRun, PriceObservation, PriceSource
from app.modules.crops.service import create_unclassified_crop, normalize_crop_name, resolve_crop
from app.modules.markets.service import ensure_agmarknet_source, resolve_price_market
from app.modules.prices.provider import (
    NORMALIZATION_VERSION,
    PARSER_VERSION,
    NormalizedPriceRecord,
    PriceProviderError,
    ProviderFailureKind,
    configured_provider,
    normalize_price_unit,
)

logger = logging.getLogger(__name__)
RESOURCE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
MIN_REFRESH_INTERVAL = timedelta(minutes=15)
SYNC_LOCK_KEY = "krishilink:prices:agmarknet:national-sync"
SYNC_LOCK_TTL_SECONDS = 15 * 60
PRICE_CACHE_TTL_SECONDS = 15 * 60


class CoordinationUnavailable(RuntimeError):
    pass


def freshness_state(price_date: date | None, *, today: date | None = None) -> str:
    if price_date is None:
        return "unavailable"
    age = ((today or datetime.now(ZoneInfo("Asia/Kolkata")).date()) - price_date).days
    if age <= 0:
        return "reported_today"
    if age == 1:
        return "reported_yesterday"
    if age <= 7:
        return "reported_within_7_days"
    return "stale"


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _normalize_scope(scope: dict[str, str] | None) -> dict[str, str] | None:
    if not scope:
        return None
    allowed = {"commodity", "district", "state.keyword"}
    if set(scope) - allowed:
        raise ValueError("Unsupported official price sync scope")
    normalized = {key: str(value).strip() for key, value in scope.items() if value and str(value).strip()}
    if not normalized.get("commodity") or not normalized.get("district"):
        raise ValueError("On-demand price sync requires both crop and district")
    if any(len(value) > 120 for value in normalized.values()):
        raise ValueError("Price sync scope value is too long")
    return normalized


def _latest_national_attempt(db: Session, source_id: uuid.UUID) -> datetime | None:
    last_run = (
        db.query(IngestionRun)
        .filter(IngestionRun.source_id == source_id, IngestionRun.scope_json.is_(None))
        .order_by(IngestionRun.started_at.desc())
        .first()
    )
    return _as_utc(last_run.started_at) if last_run else None


def _ensure_price_source(db: Session, registry: DataSourceRegistry) -> PriceSource:
    source = db.query(PriceSource).filter_by(adapter=PARSER_VERSION).first()
    if source is None:
        source = PriceSource(
            id=uuid.uuid4(),
            name="AGMARKNET daily reported prices",
            url=RESOURCE_URL,
            adapter=PARSER_VERSION,
            is_active=True,
            registry_id=registry.id,
        )
        db.add(source)
        db.flush()
    elif source.registry_id != registry.id:
        source.registry_id = registry.id
    return source


def _create_run(db: Session, source: PriceSource) -> IngestionRun:
    run = IngestionRun(
        id=uuid.uuid4(), source_id=source.id, status="running", records_fetched=0,
        records_ok=0, records_accepted=0, records_updated=0, records_unchanged=0,
        records_rejected=0, records_quarantined=0, unresolved_markets=0,
        unresolved_crops=0, parser_version=PARSER_VERSION,
    )
    db.add(run)
    db.flush()
    return run


def _run_counts(run: IngestionRun) -> dict[str, int]:
    return {
        "fetched": int(run.records_fetched or 0),
        "accepted": int(run.records_accepted or 0),
        "updated": int(run.records_updated or 0),
        "unchanged": int(run.records_unchanged or 0),
        "rejected": int(run.records_rejected or 0),
        "quarantined": int(run.records_quarantined or 0),
        "unresolved_markets": int(run.unresolved_markets or 0),
        "unresolved_crops": int(run.unresolved_crops or 0),
    }


def _unit_for_record(record: NormalizedPriceRecord, registry: DataSourceRegistry) -> tuple[str | None, str | None]:
    if record.source_unit:
        unit = normalize_price_unit(record.source_unit)
        return unit, "provider_field" if unit else "unsupported_provider_unit"
    conventions = registry.unit_conventions or {}
    crop_key = normalize_crop_name(record.commodity)
    variety_key = normalize_crop_name(record.variety or "")
    convention_key = f"{crop_key}::{variety_key}" if variety_key else crop_key
    configured_key = convention_key if conventions.get(convention_key) else crop_key
    configured = conventions.get(configured_key)
    if configured in {"INR/quintal", "INR/number"}:
        return configured, f"source_registry:{configured_key}"
    return None, "unit_unconfirmed"


def _resolve_variety(db: Session, crop: Crop, label: str | None) -> CropVariety | None:
    if not label:
        return None
    key = normalize_crop_name(label)
    matches = [
        variety for variety in db.query(CropVariety).filter(CropVariety.crop_id == crop.id).all()
        if key in {
            normalize_crop_name(variety.name),
            normalize_crop_name(variety.code or ""),
            normalize_crop_name(variety.agmarknet_name or ""),
        }
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return None
    candidate = CropVariety(
        id=uuid.uuid4(), crop_id=crop.id, name=label.strip(), agmarknet_name=label.strip(),
        code=None, is_active=False, is_tradable=False,
    )
    db.add(candidate)
    db.flush()
    return candidate


def observation_identity(
    *, source: PriceSource, crop: Crop, market_id: uuid.UUID, variety: CropVariety | None,
    raw_variety: str | None, grade: str | None, price_date: date,
) -> str:
    identity = "|".join((
        source.adapter,
        str(market_id),
        str(crop.id),
        str(variety.id) if variety else normalize_crop_name(raw_variety or ""),
        normalize_crop_name(grade or ""),
        price_date.isoformat(),
    ))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _upsert_observation(db: Session, values: dict[str, Any]) -> None:
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        insert = pg_insert(PriceObservation)
    elif dialect == "sqlite":
        insert = sqlite_insert(PriceObservation)
    else:
        existing = db.query(PriceObservation).filter_by(observation_key=values["observation_key"]).first()
        if existing:
            for name, value in values.items():
                if name != "id":
                    setattr(existing, name, value)
        else:
            db.add(PriceObservation(**values))
        return
    excluded = insert.excluded
    update_fields = (
        "variety_id", "grade", "min_price", "modal_price", "max_price", "price_unit", "source_unit",
        "unit_provenance", "arrival_quantity", "arrival_unit", "source_record_id", "source_url",
        "published_at", "fetched_at", "retrieved_at", "ingestion_run_id", "parser_version",
        "normalization_version", "raw_payload_hash", "quality_status",
    )
    statement = insert.values(**values).on_conflict_do_update(
        index_elements=[PriceObservation.observation_key],
        set_={name: getattr(excluded, name) for name in update_fields},
    )
    db.execute(statement)


def _lock(redis_client: Any) -> str:
    if redis_client is None:
        raise CoordinationUnavailable("redis_unavailable")
    token = uuid.uuid4().hex
    try:
        acquired = redis_client.set(SYNC_LOCK_KEY, token, nx=True, ex=SYNC_LOCK_TTL_SECONDS)
    except Exception:
        raise CoordinationUnavailable("redis_lock_unavailable") from None
    if not acquired:
        raise CoordinationUnavailable("sync_already_running")
    return token


def _unlock(redis_client: Any, token: str) -> None:
    try:
        redis_client.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
            1,
            SYNC_LOCK_KEY,
            token,
        )
    except Exception:
        # The lease expires if Redis is unavailable; a different owner is never removed.
        logger.warning("Price sync lock release failed; lease will expire")


def run_price_sync(
    db: Session,
    *,
    provider_factory: Callable[[], Any] = configured_provider,
    redis_client: Any | None = None,
    retry_run_id: str | None = None,
    scope: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Fetch and upsert one official provider run under a Redis owner-token lease."""
    normalized_scope = _normalize_scope(scope)
    client = redis_client if redis_client is not None else get_redis()
    try:
        lock_token = _lock(client)
    except CoordinationUnavailable as exc:
        if exc.args and exc.args[0] == "sync_already_running":
            return {"status": "already_running", "inserted": 0, "updated": 0, "rejected": 0}
        raise

    started_clock = time.monotonic()
    attempted_at = now or datetime.now(timezone.utc)
    registry = None
    run = None
    source = None
    try:
        registry = ensure_agmarknet_source(db, PARSER_VERSION)
        source = _ensure_price_source(db, registry)
        if retry_run_id:
            run = db.get(IngestionRun, uuid.UUID(retry_run_id))
            if run is None or run.source_id != source.id:
                raise ValueError("Price sync retry run is unavailable")
            normalized_scope = run.scope_json
            run.status = "running"
            run.error = None
            run.provider_failure = None
        else:
            if normalized_scope:
                rate_scope = {key: normalize_crop_name(value) for key, value in normalized_scope.items()}
                canonical_scope = json.dumps(rate_scope, sort_keys=True, separators=(",", ":"))
                scope_digest = hashlib.sha256(canonical_scope.encode("utf-8")).hexdigest()
                try:
                    accepted = client.set(
                        f"krishilink:prices:scope-cooldown:{scope_digest}", "1", nx=True,
                        ex=int(MIN_REFRESH_INTERVAL.total_seconds()),
                    )
                except Exception:
                    raise CoordinationUnavailable("scope_rate_limit_unavailable") from None
                if not accepted:
                    db.rollback()
                    return {"status": "rate_limited", "retry_after_seconds": int(MIN_REFRESH_INTERVAL.total_seconds()),
                            "inserted": 0, "updated": 0, "rejected": 0}
            else:
                previous_attempt = _latest_national_attempt(db, source.id)
                if previous_attempt and attempted_at - previous_attempt < MIN_REFRESH_INTERVAL:
                    db.rollback()
                    retry_after = max(1, int((MIN_REFRESH_INTERVAL - (attempted_at - previous_attempt)).total_seconds()))
                    return {"status": "rate_limited", "retry_after_seconds": retry_after,
                            "inserted": 0, "updated": 0, "rejected": 0}
            run = _create_run(db, source)
            run.scope_json = normalized_scope
            registry.last_attempt_at = attempted_at
        db.commit()

        try:
            fetch_result = provider_factory().fetch(scope=normalized_scope) if normalized_scope else provider_factory().fetch()
        except PriceProviderError as exc:
            raise exc
        fetched_at = datetime.now(timezone.utc)
        run.records_fetched = fetch_result.fetched_count
        run.records_rejected = fetch_result.rejected_count
        run.error = None
        run.provider_failure = None
        if fetch_result.rejected_count:
            run.error = ";".join(sorted(set(fetch_result.rejection_reasons))[:10])[:1000]

        seen_keys: set[str] = set()
        unresolved_crops: set[str] = set()
        unresolved_markets: set[str] = set()
        inserted = updated = unchanged = quarantined = accepted_count = 0
        for record in fetch_result.records:
            row_inserted = row_updated = row_unchanged = row_quarantined = row_accepted = 0
            try:
                with db.begin_nested():
                    crop = resolve_crop(db, record.commodity)
                    if crop is None:
                        crop = create_unclassified_crop(db, record.commodity)
                        unresolved_crops.add(normalize_crop_name(record.commodity))
                    market_resolution = resolve_price_market(
                        db,
                        name=record.market,
                        district=record.district,
                        state=record.state,
                        market_code=record.market_code,
                        source_registry=registry,
                        parser_version=PARSER_VERSION,
                    )
                    market = market_resolution.market
                    if market_resolution.resolution != "verified_outlet":
                        unresolved_markets.add(str(market.id))
                    variety = _resolve_variety(db, crop, record.variety)
                    key = observation_identity(
                        source=source,
                        crop=crop,
                        market_id=market.id,
                        variety=variety,
                        raw_variety=record.variety,
                        grade=record.grade,
                        price_date=record.price_date,
                    )
                    if key in seen_keys:
                        row_unchanged = 1
                        continue
                    seen_keys.add(key)
                    unit, unit_provenance = _unit_for_record(record, registry)
                    if unit is None:
                        row_quarantined = 1
                    else:
                        row_accepted = 1
                    existing = db.query(PriceObservation).filter_by(observation_key=key).first()
                    old_hash = existing.raw_payload_hash if existing else None
                    values = {
                        "id": existing.id if existing else uuid.uuid4(),
                        "crop_id": crop.id,
                        "variety_id": variety.id if variety else None,
                        "market_id": market.id,
                        "price_date": record.price_date,
                        "fetched_at": fetched_at,
                        "min_price": record.min_price,
                        "modal_price": record.modal_price,
                        "max_price": record.max_price,
                        "grade": record.grade,
                        "price_unit": unit,
                        "source_unit": record.source_unit,
                        "unit_provenance": unit_provenance,
                        "arrival_quantity": record.arrival_quantity,
                        "arrival_unit": record.arrival_unit,
                        "volume_tonnes": None,
                        "source_id": source.id,
                        "source_record_id": record.source_record_id or record.raw_payload_hash,
                        "source_url": RESOURCE_URL,
                        # The provider supplies a report date, not a publication timestamp.
                        "published_at": None,
                        "retrieved_at": fetched_at,
                        "ingestion_run_id": run.id,
                        "parser_version": PARSER_VERSION,
                        "normalization_version": NORMALIZATION_VERSION,
                        "raw_payload_hash": record.raw_payload_hash,
                        "observation_key": key,
                        "quality_status": "MEDIUM" if unit else "LOW",
                    }
                    _upsert_observation(db, values)
                    if existing is None:
                        row_inserted = 1
                    elif old_hash == record.raw_payload_hash:
                        row_unchanged = 1
                    else:
                        row_updated = 1
                inserted += row_inserted
                updated += row_updated
                unchanged += row_unchanged
                quarantined += row_quarantined
                accepted_count += row_accepted
            except SQLAlchemyError as exc:
                logger.warning("Price record quarantined after persistence validation (%s)", type(exc).__name__)
                run.records_rejected = int(run.records_rejected or 0) + 1
                quarantined += 1
                db.expire_all()

        run.records_accepted = accepted_count
        run.records_updated = updated
        run.records_unchanged = unchanged
        run.records_quarantined = quarantined
        run.records_ok = inserted + updated + unchanged
        run.unresolved_crops = len(unresolved_crops)
        run.unresolved_markets = len(unresolved_markets)
        run.finished_at = datetime.now(timezone.utc)
        run.duration_ms = int((time.monotonic() - started_clock) * 1000)
        if fetch_result.fetched_count and not fetch_result.records:
            run.status = "failed"
            run.provider_failure = ProviderFailureKind.SCHEMA_DRIFT.value
            run.error = "no_valid_records"
            registry.last_failure_at = run.finished_at
            registry.last_run_status = "failed"
        else:
            run.status = "partial" if run.records_rejected or quarantined else "completed"
            registry.last_success_at = run.finished_at
            registry.last_run_status = run.status
        registry.last_run_counts = _run_counts(run)
        db.commit()
        return {
            "status": run.status,
            "run_id": str(run.id),
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "rejected": int(run.records_rejected or 0),
            "quarantined": quarantined,
            "unresolved_markets": run.unresolved_markets,
            "unresolved_crops": run.unresolved_crops,
        }
    except PriceProviderError as exc:
        db.rollback()
        run = db.get(IngestionRun, run.id) if run is not None else None
        registry = db.get(DataSourceRegistry, registry.id) if registry is not None else None
        ended = datetime.now(timezone.utc)
        if run:
            run.status = "retrying" if exc.retryable else "failed"
            run.provider_failure = exc.kind.value
            run.error = exc.kind.value
            run.finished_at = ended
            run.duration_ms = int((time.monotonic() - started_clock) * 1000)
        if registry:
            registry.last_failure_at = ended
            registry.last_run_status = "retrying" if exc.retryable else "failed"
            registry.last_run_counts = _run_counts(run) if run else {}
        db.commit()
        logger.warning("Official price provider failed (%s)", exc.kind.value)
        exc.run_id = str(run.id) if run else None
        raise
    except Exception:
        db.rollback()
        if run is not None:
            run = db.get(IngestionRun, run.id)
            if run:
                run.status = "failed"
                run.provider_failure = "internal_error"
                run.error = "internal_error"
                run.finished_at = datetime.now(timezone.utc)
                run.duration_ms = int((time.monotonic() - started_clock) * 1000)
                db.commit()
        logger.exception("Official price ingestion failed with an internal error")
        raise
    finally:
        _unlock(client, lock_token)


def sync_daily_prices(db: Session, force: bool = False) -> dict[str, Any]:
    """Compatibility name for existing callers; `force` never bypasses the refresh floor."""
    return run_price_sync(db)


def price_cache_key(db: Session, **dimensions: Any) -> str:
    source = db.query(DataSourceRegistry).filter_by(source_key="agmarknet-daily-reported-prices").first()
    generation = source.last_success_at.isoformat() if source and source.last_success_at else "never"
    canonical = json.dumps({"generation": generation, **dimensions}, sort_keys=True, default=str, separators=(",", ":"))
    return "krishilink:prices:v1:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_cached_price_payload(redis_client: Any | None, key: str) -> dict[str, Any] | None:
    if redis_client is None:
        return None
    try:
        value = redis_client.get(key)
        return json.loads(value) if value else None
    except Exception:
        logger.warning("Price cache unavailable; reading authoritative database")
        return None


def set_cached_price_payload(redis_client: Any | None, key: str, value: dict[str, Any]) -> None:
    if redis_client is None:
        return
    try:
        redis_client.set(key, json.dumps(value, separators=(",", ":")), ex=PRICE_CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("Price cache write failed; authoritative database remains available")
