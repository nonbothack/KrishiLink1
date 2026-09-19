import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.models import Crop, IngestionRun, Market, PriceObservation, PriceSource
from app.modules.markets.service import ensure_agmarknet_source
from app.modules.prices.provider import (
    PARSER_VERSION,
    AgmarknetProvider,
    PriceProviderError,
    ProviderFailureKind,
    normalize_record,
)
from app.modules.prices.sync_service import (
    freshness_state,
    observation_identity,
    run_price_sync,
)


class FakeRedis:
    def __init__(self):
        self.values = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def eval(self, _script, _key_count, key, owner):
        if self.values.get(key) == owner:
            del self.values[key]
            return 1
        return 0


class FakeProvider:
    def __init__(self, records):
        self.result = type("FetchResult", (), {
            "records": tuple(records), "fetched_count": len(records), "rejected_count": 0,
            "rejection_reasons": (),
        })()

    def fetch(self, *, scope=None):
        self.scope = scope
        return self.result


def raw_record(*, market: str, unit: str | None = "Rs/Quintal", crop: str = "Onion"):
    row = {
        "state": "Maharashtra", "district": "Nashik", "market": market,
        "commodity": crop, "arrival_date": "01/09/2026", "min_price": "1800.00",
        "modal_price": "2000.00", "max_price": "2200.00", "record_id": f"record:{market}",
    }
    if unit is not None:
        row["price_unit"] = unit
    return row


def test_official_record_normalization_keeps_decimal_date_unit_and_hash():
    normalized = normalize_record(raw_record(market="Yard"))
    assert normalized.modal_price == Decimal("2000.00")
    assert normalized.price_date == date(2026, 9, 1)
    assert normalized.price_unit == "INR/quintal"
    assert len(normalized.raw_payload_hash) == 64
    assert normalize_record(raw_record(market="Yard")).raw_payload_hash == normalized.raw_payload_hash


@pytest.mark.parametrize("changes,reason", [
    ({"modal_price": "0"}, "negative_or_zero_modal_price"),
    ({"modal_price": "2300"}, "price_range_order_invalid"),
    ({"min_price": "1.001"}, "unsupported_price_precision"),
    ({"arrival_date": "not-a-date"}, "invalid_price_date"),
])
def test_invalid_source_price_record_is_rejected(changes, reason):
    row = raw_record(market="Yard")
    row.update(changes)
    with pytest.raises(ValueError, match=reason):
        normalize_record(row)


def test_provider_rejects_non_official_endpoint_without_echoing_secret():
    key = "packet04-secret-sentinel"
    with pytest.raises(ValueError) as error:
        AgmarknetProvider(api_key=key, resource_url="https://data.gov.in.attacker.invalid/resource")
    assert key not in str(error.value)


def test_provider_classifies_rate_limit_without_exposing_api_key():
    secret = "packet04-provider-secret"
    request_params = {}

    class Response:
        status_code = 429
        headers = {"Retry-After": "45"}

    class Client:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def get(self, *_args, **kwargs):
            request_params.update(kwargs["params"])
            return Response()

    with patch("app.modules.prices.provider.httpx.Client", Client):
        with pytest.raises(PriceProviderError) as error:
            AgmarknetProvider(api_key=secret).fetch(scope={"commodity": "Onion", "district": "Nashik"})
    assert error.value.kind == ProviderFailureKind.RATE_LIMIT
    assert error.value.retry_after == 45
    assert secret not in str(error.value)
    assert request_params["filters[commodity]"] == "Onion"
    assert request_params["filters[district]"] == "Nashik"


def test_freshness_uses_report_date_not_fetch_timestamp():
    today = date(2026, 9, 17)
    assert freshness_state(today, today=today) == "reported_today"
    assert freshness_state(today - timedelta(days=1), today=today) == "reported_yesterday"
    assert freshness_state(today - timedelta(days=6), today=today) == "reported_within_7_days"
    assert freshness_state(today - timedelta(days=8), today=today) == "stale"


def test_sync_is_idempotent_and_keeps_unverified_market_location_null(db_session, client, monkeypatch):
    suffix = uuid.uuid4().hex[:10]
    crop = db_session.query(Crop).filter_by(name="Onion").first()
    source_registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    source_registry.unit_conventions = {"onion": "INR/quintal"}
    db_session.commit()
    record = normalize_record(raw_record(market=f"Official price yard {suffix}"))
    redis_client = FakeRedis()
    first_time = datetime(2026, 9, 17, 4, tzinfo=timezone.utc)

    first = run_price_sync(db_session, provider_factory=lambda: FakeProvider([record]),
                           redis_client=redis_client, now=first_time)
    assert first["status"] == "completed"
    assert first["inserted"] == 1
    second = run_price_sync(db_session, provider_factory=lambda: FakeProvider([record]),
                            redis_client=redis_client, now=first_time + timedelta(minutes=16))
    assert second["status"] == "completed"
    assert second["unchanged"] == 1

    observation = db_session.query(PriceObservation).filter_by(source_record_id=record.source_record_id).order_by(
        PriceObservation.fetched_at.desc()
    ).first()
    assert observation.crop_id == crop.id
    assert observation.min_price == Decimal("1800.00")
    assert observation.price_unit == "INR/quintal"
    assert db_session.query(PriceObservation).filter_by(observation_key=observation.observation_key).count() == 1
    market = db_session.get(Market, observation.market_id)
    assert market.verification_status == "needs_review"
    assert market.latitude is None and market.longitude is None

    response = client.get("/api/v1/prices/live", params={"crop": "Onion", "market": market.name})
    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert item["modal_price"] == "2000.00"
    assert item["unit"] == "INR/quintal"
    assert item["location_verified"] is False
    assert item["price_date"] == "2026-09-01"
    assert item["source"]


def test_unconfirmed_unit_is_quarantined_and_never_published(db_session, client):
    suffix = uuid.uuid4().hex[:10]
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    registry.unit_conventions = {}
    db_session.commit()
    record = normalize_record(raw_record(market=f"Unit review yard {suffix}", unit=None))
    result = run_price_sync(db_session, provider_factory=lambda: FakeProvider([record]), redis_client=FakeRedis())
    assert result["quarantined"] == 1
    observation = db_session.query(PriceObservation).filter_by(source_record_id=record.source_record_id).order_by(
        PriceObservation.fetched_at.desc()
    ).first()
    assert observation.price_unit is None
    assert observation.quality_status == "LOW"
    public = client.get("/api/v1/prices/live", params={"market": f"Unit review yard {suffix}"})
    assert public.status_code == 200
    assert public.json()["data"]["items"] == []


def test_on_demand_scope_is_persisted_and_15_minute_limited(db_session):
    suffix = uuid.uuid4().hex[:10]
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    registry.unit_conventions = {"onion": "INR/quintal"}
    db_session.commit()
    record = normalize_record(raw_record(market=f"Scoped yard {suffix}"))
    provider = FakeProvider([record])
    redis_client = FakeRedis()
    scope = {"commodity": "Onion", "district": "Nashik"}

    first = run_price_sync(db_session, provider_factory=lambda: provider, redis_client=redis_client,
                           scope=scope)
    assert first["status"] == "completed"
    assert provider.scope == scope
    source = db_session.query(PriceSource).filter_by(adapter=PARSER_VERSION).first()
    run = db_session.query(IngestionRun).filter_by(source_id=source.id).order_by(
        IngestionRun.started_at.desc()
    ).first()
    assert run.scope_json == scope

    limited = run_price_sync(db_session, provider_factory=lambda: provider, redis_client=redis_client,
                             scope=scope)
    assert limited["status"] == "rate_limited"
    assert limited["retry_after_seconds"] == 900



def test_observation_identity_changes_with_variety_or_grade(db_session):
    suffix = uuid.uuid4().hex[:8]
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    source = PriceSource(name=f"Identity source {suffix}", url="https://data.gov.in", adapter=PARSER_VERSION,
                         registry_id=registry.id, is_active=True)
    crop = Crop(name=f"Identity crop {suffix}", is_active=True, is_tradable=True)
    market = Market(name=f"Identity market {suffix}", district="Nashik", state="Maharashtra", is_active=False)
    db_session.add_all([source, crop, market])
    db_session.flush()
    base = dict(source=source, crop=crop, market_id=market.id, variety=None, raw_variety="Red",
                grade="A", price_date=date(2026, 9, 1))
    first = observation_identity(**base)
    assert first != observation_identity(**{**base, "grade": "B"})
    assert first != observation_identity(**{**base, "raw_variety": "White"})


def test_admin_can_record_source_unit_conventions_and_sync_is_queued(client, db_session, admin_auth_headers,
                                                                      auth_headers, monkeypatch):
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    db_session.commit()
    response = client.patch(
        f"/api/v1/markets/sources/{registry.id}", headers=admin_auth_headers,
        json={"unit_conventions": {"Onion": "INR/quintal"}},
    )
    assert response.status_code == 200
    assert response.json()["data"]["unit_conventions"]["onion"] == "INR/quintal"

    assert client.get("/api/v1/prices/ops/health", headers=auth_headers).status_code == 403
    assert client.get("/api/v1/prices/ops/health", headers=admin_auth_headers).status_code == 200
    assert client.post("/api/v1/prices/sync", headers=auth_headers).status_code == 403
    monkeypatch.setattr("app.workers.celery_app.sync_official_prices.delay",
                        lambda **_kwargs: SimpleNamespace(id="task-packet04"))
    queued = client.post("/api/v1/prices/sync?force=true", headers=admin_auth_headers)
    assert queued.status_code == 202
    assert queued.json()["data"]["status"] == "queued"
    assert queued.json()["data"]["task_id"] == "task-packet04"
