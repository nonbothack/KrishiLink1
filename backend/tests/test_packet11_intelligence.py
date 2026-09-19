from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.security import create_access_token
from app.models import (
    Crop,
    Dispute,
    Market,
    Notification,
    OutboxEvent,
    PriceAlertEvaluation,
    PriceAlertRule,
    PriceObservation,
    PriceSource,
    TradeTermSnapshot,
    Transaction,
    User,
)
from app.modules.intelligence.service import evaluate_price_alerts
from app.modules.markets.service import ensure_agmarknet_source
from app.modules.prices.provider import PARSER_VERSION


def new_price_scope(db_session):
    suffix = uuid.uuid4().hex[:10]
    crop = Crop(name=f"Packet11 crop {suffix}", is_active=True, is_tradable=True,
                unit="quintal", valid_units=["quintal"])
    market = Market(name=f"Packet11 market {suffix}", district="Nashik", state="Maharashtra", is_active=True)
    db_session.add_all([crop, market])
    db_session.commit()
    return crop, market


def create_report(db_session, crop, market, registry, *, modal, fetched_at, report_date=None, name=None,
                  quality_status="MEDIUM"):
    source = PriceSource(
        id=uuid.uuid4(), name=f"Packet11 source {name or uuid.uuid4()}", url="https://data.gov.in",
        adapter=PARSER_VERSION, registry_id=registry.id, is_active=True,
    )
    db_session.add(source)
    db_session.flush()
    report_date = report_date or fetched_at.date()
    observation = PriceObservation(
        id=uuid.uuid4(), crop_id=crop.id, market_id=market.id, price_date=report_date,
        fetched_at=fetched_at, min_price=Decimal("1800.00"), modal_price=Decimal(modal),
        max_price=Decimal("3000.00"), price_unit="INR/quintal", source_unit="Rs/Quintal",
        unit_provenance="source_record", source_id=source.id,
        source_record_id=f"packet11:{uuid.uuid4()}", source_url="https://data.gov.in/resource/test",
        parser_version=PARSER_VERSION, normalization_version="packet11-test-v1",
        raw_payload_hash=uuid.uuid4().hex * 2, observation_key=f"packet11:{uuid.uuid4()}",
        quality_status=quality_status,
    )
    db_session.add(observation)
    db_session.commit()
    return observation


def test_forecast_and_sale_window_abstain_without_registered_model(client, db_session):
    crop = db_session.query(Crop).filter(Crop.name == "Onion").first()
    forecast = client.get(f"/api/v1/intelligence/forecasts/{crop.id}")
    assert forecast.status_code == 200
    payload = forecast.json()["data"]
    assert payload["forecast"] is None
    assert payload["model_version"] is None
    assert payload["eligibility"] == "FORECAST_UNAVAILABLE"
    assert payload["abstention_reason"] in ("FORECASTS_DISABLED", "NO_ACTIVE_VALIDATED_MODEL")

    sale = client.get(f"/api/v1/intelligence/sale-window/{crop.id}")
    assert sale.status_code == 200
    assert sale.json()["data"]["recommendation"] == "NOT_ENOUGH_DATA"
    assert sale.json()["data"]["sell_now"] is None
    assert sale.json()["data"]["wait"] is None


def test_demand_abstains_when_requirement_and_supply_geography_are_not_comparable(client, db_session):
    crop = db_session.query(Crop).filter(Crop.name == "Onion").first()
    result = client.get(f"/api/v1/intelligence/demand/{crop.id}")
    assert result.status_code == 200
    data = result.json()["data"]
    assert data["status"] == "INSUFFICIENT_COMPARABLE_DATA"
    assert data["open_requirement_quantity"] is None
    assert data["listed_supply_quantity"] is None


def test_trust_facts_use_completed_snapshots_and_do_not_claim_payment_or_fault(
    client, db_session, auth_headers
):
    buyer = User(id=uuid.uuid4(), email=f"trust-buyer-{uuid.uuid4()}@example.invalid",
                 full_name="Trust test buyer", role="buyer", password_hash="unused", is_active=True)
    db_session.add(buyer)
    db_session.commit()
    buyer_headers = {"Authorization": f"Bearer {create_access_token(str(buyer.id), buyer.role)}"}
    lot = client.post("/api/v1/lots", headers=auth_headers, json={
        "crop": "Onion", "grade": "A", "quantity": "12", "asking_price": "2400",
        "location_text": "Nashik", "district": "Nashik",
    })
    assert lot.status_code == 201, lot.text
    offer = client.post("/api/v1/offers", headers=buyer_headers, json={
        "lot_id": lot.json()["data"]["id"], "quantity": "12", "price_per_unit": "2425",
    })
    assert offer.status_code == 201, offer.text
    accepted = client.post(f"/api/v1/offers/{offer.json()['data']['id']}/accept", headers=auth_headers)
    assert accepted.status_code == 200, accepted.text
    txn_id = uuid.UUID(accepted.json()["data"]["transaction_id"])
    txn = db_session.get(Transaction, txn_id)
    txn.status = "COMPLETED"
    snapshot = db_session.query(TradeTermSnapshot).filter_by(transaction_id=txn_id).one()
    db_session.add(Dispute(transaction_id=txn_id, raised_by=txn.seller_id, reason="test",
                           description="private evidence text must not be projected", status="OPEN"))
    db_session.commit()

    result = client.get(f"/api/v1/intelligence/trust/{buyer.id}", headers=auth_headers)
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["eligible_completed_trade_count"] == 1
    assert data["history_state"] == "LIMITED_HISTORY"
    assert data["disputes_recorded_against_eligible_completed_trades"] == 1
    assert data["dispute_denominator"] == 1
    assert data["dispute_attribution"].startswith("No fault")
    assert data["payment_timing"] == "UNAVAILABLE"
    assert data["composite_score"] is None and data["rates_or_ranking"] is None
    assert "private evidence text" not in str(data)
    assert buyer.phone is None or buyer.phone not in str(data)
    assert snapshot.gross_value == Decimal("29100.00")

    other_buyer = db_session.query(User).filter(User.email == "mehta@demo.com").one()
    denied = client.get(f"/api/v1/intelligence/trust/{other_buyer.id}", headers=buyer_headers)
    assert denied.status_code == 404


def test_channel_comparison_keeps_unknown_costs_null_and_disables_net_ranking(
    client, auth_headers, buyer_auth_headers
):
    lot = client.post("/api/v1/lots", headers=auth_headers, json={
        "crop": "Onion", "grade": "A", "quantity": "10", "asking_price": "2200",
        "location_text": "Nashik", "district": "Nashik",
    })
    assert lot.status_code == 201, lot.text
    offer = client.post("/api/v1/offers", headers=buyer_auth_headers, json={
        "lot_id": lot.json()["data"]["id"], "quantity": "10", "price_per_unit": "2300",
    })
    assert offer.status_code == 201, offer.text
    lot_id = lot.json()["data"]["id"]
    data = client.get(f"/api/v1/intelligence/lots/{lot_id}/channels", headers=auth_headers).json()["data"]
    assert data["net_ranking_enabled"] is False
    assert "best_channel" not in data
    buyer_access = client.get(f"/api/v1/intelligence/lots/{lot_id}/channels", headers=buyer_auth_headers)
    assert buyer_access.status_code == 404
    offer_channel = next(item for item in data["channels"] if item["kind"] == "DIRECT_BUYER_OFFER")
    assert offer_channel["gross"] == "23000.00"
    assert offer_channel["known_net"] is None
    assert {"freight", "commission", "storage"}.issubset(set(offer_channel["unknown_costs"]))


def test_price_alert_crossing_hysteresis_and_outbox_are_deduplicated(
    client, db_session, auth_headers, monkeypatch
):
    monkeypatch.setattr("app.modules.intelligence.router.settings.intelligence_price_alerts_enabled", True)
    crop, market = new_price_scope(db_session)
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    registry.unit_conventions = {"onion": "INR/quintal"}
    db_session.commit()
    response = client.post("/api/v1/intelligence/price-alerts", headers=auth_headers, json={
        "crop_id": str(crop.id), "market_id": str(market.id), "threshold": "2300.00",
        "direction": "AT_OR_ABOVE", "unit": "INR/quintal",
    })
    assert response.status_code == 201, response.text
    rule = db_session.get(PriceAlertRule, uuid.UUID(response.json()["data"]["id"]))
    now = datetime.now(timezone.utc)

    create_report(db_session, crop, market, registry, modal="2200.00", fetched_at=now + timedelta(seconds=1))
    assert evaluate_price_alerts(db_session, now=now + timedelta(minutes=1)) == {"evaluated": 1, "triggered": 0}
    create_report(db_session, crop, market, registry, modal="2400.00", fetched_at=now + timedelta(minutes=2))
    assert evaluate_price_alerts(db_session, now=now + timedelta(minutes=3)) == {"evaluated": 1, "triggered": 1}
    assert rule.is_armed is False
    create_report(db_session, crop, market, registry, modal="2500.00", fetched_at=now + timedelta(minutes=4))
    assert evaluate_price_alerts(db_session, now=now + timedelta(minutes=5)) == {"evaluated": 1, "triggered": 0}
    create_report(db_session, crop, market, registry, modal="2200.00", fetched_at=now + timedelta(minutes=6))
    assert evaluate_price_alerts(db_session, now=now + timedelta(minutes=7)) == {"evaluated": 1, "triggered": 0}
    assert rule.is_armed is True
    create_report(db_session, crop, market, registry, modal="2350.00", fetched_at=now + timedelta(minutes=8))
    assert evaluate_price_alerts(db_session, now=now + timedelta(minutes=9)) == {"evaluated": 1, "triggered": 1}
    assert evaluate_price_alerts(db_session, now=now + timedelta(minutes=10)) == {"evaluated": 0, "triggered": 0}

    notifications = [row for row in db_session.query(Notification).filter_by(user_id=rule.user_id, type="price_alert").all()
                     if (row.metadata_json or {}).get("crop") == crop.name]
    assert len(notifications) == 2
    assert notifications[0].metadata_json["source"] == registry.name
    assert notifications[0].metadata_json["unit"] == "INR/quintal"
    assert db_session.query(PriceAlertEvaluation).filter_by(alert_id=rule.id).count() == 5
    outbox_rows = db_session.query(OutboxEvent).filter(OutboxEvent.event_type == "NOTIFICATION_PRICE_ALERT").all()
    assert sum(1 for row in outbox_rows if (row.payload.get("metadata") or {}).get("crop") == crop.name) == 2


def test_price_alert_api_is_role_and_owner_scoped_and_unit_is_server_checked(
    client, db_session, auth_headers, buyer_auth_headers, fpo_auth_headers
):
    crop, market = new_price_scope(db_session)
    response = client.post("/api/v1/intelligence/price-alerts", headers=auth_headers, json={
        "crop_id": str(crop.id), "market_id": str(market.id), "threshold": "2000",
        "direction": "AT_OR_ABOVE", "unit": "INR/number",
    })
    assert response.status_code == 422
    idempotency_key = str(uuid.uuid4())
    idempotent_headers = {**auth_headers, "Idempotency-Key": idempotency_key}
    alert_body = {
        "crop_id": str(crop.id), "market_id": str(market.id), "threshold": "2000",
        "direction": "AT_OR_ABOVE", "unit": "INR/quintal",
    }
    created = client.post("/api/v1/intelligence/price-alerts", headers=idempotent_headers, json=alert_body)
    assert created.status_code == 201
    alert_id = created.json()["data"]["id"]
    retried = client.post("/api/v1/intelligence/price-alerts", headers=idempotent_headers, json=alert_body)
    assert retried.status_code == 201
    assert retried.json()["data"]["id"] == alert_id
    assert client.get("/api/v1/intelligence/price-alerts", headers=buyer_auth_headers).status_code == 403
    assert client.get("/api/v1/intelligence/price-alerts", headers=fpo_auth_headers).status_code == 403
    other = User(id=uuid.uuid4(), email=f"other-{uuid.uuid4()}@example.invalid", full_name="Other farmer",
                 role="farmer", password_hash="unused", is_active=True)
    db_session.add(other)
    db_session.commit()
    other_headers = {"Authorization": f"Bearer {create_access_token(str(other.id), other.role)}"}
    assert client.delete(f"/api/v1/intelligence/price-alerts/{alert_id}", headers=other_headers).status_code == 404
    own = client.get("/api/v1/intelligence/price-alerts", headers=auth_headers)
    assert own.status_code == 200
    assert any(item["id"] == alert_id for item in own.json()["data"]["items"])


def test_stale_official_observation_does_not_trigger_price_alert(client, db_session, auth_headers):
    crop, market = new_price_scope(db_session)
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    response = client.post("/api/v1/intelligence/price-alerts", headers=auth_headers, json={
        "crop_id": str(crop.id), "market_id": str(market.id), "threshold": "2000",
        "direction": "AT_OR_ABOVE", "unit": "INR/quintal",
    })
    rule = db_session.get(PriceAlertRule, uuid.UUID(response.json()["data"]["id"]))
    now = datetime.now(timezone.utc)
    stale = create_report(db_session, crop, market, registry, modal="3000", fetched_at=now + timedelta(seconds=1),
                          report_date=now.date() - timedelta(days=8))
    result = evaluate_price_alerts(db_session, now=now + timedelta(minutes=1))
    assert result == {"evaluated": 0, "triggered": 0}
    assert db_session.query(Notification).filter_by(user_id=rule.user_id, type="price_alert", related_id=stale.id).count() == 0


def test_trend_requires_seven_distinct_fresh_report_dates(client, db_session):
    crop, market = new_price_scope(db_session)
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    now = datetime.now(timezone.utc)
    for offset in range(2):
        create_report(db_session, crop, market, registry, modal=str(2000 + offset * 10),
                      fetched_at=now - timedelta(days=offset), report_date=now.date() - timedelta(days=offset))
    result = client.get(f"/api/v1/prices/trends/{crop.name}", params={"market": market.name}).json()["data"]
    assert result["eligibility"] == "INSUFFICIENT_DATA"
    assert result["trend"] == "UNKNOWN"
    assert result["observation_count"] == 2


def test_trend_reports_only_descriptive_change_for_seven_same_dimension_reports(client, db_session):
    crop, market = new_price_scope(db_session)
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    now = datetime.now(timezone.utc)
    for offset in range(7):
        create_report(db_session, crop, market, registry, modal=str(2000 + offset * 100),
                      fetched_at=now - timedelta(days=6 - offset),
                      report_date=now.date() - timedelta(days=6 - offset))
    result = client.get(f"/api/v1/prices/trends/{crop.name}", params={"market": market.name}).json()["data"]
    assert result["eligibility"] == "DESCRIPTIVE_ONLY"
    assert result["observation_count"] == 7
    assert result["percentage_change"] == "30.00"
    assert result["unit"] == "INR/quintal"
    assert result["forecast"] is None
    assert result["recommendation"] is None


def test_trend_excludes_low_quality_official_observations(client, db_session):
    crop, market = new_price_scope(db_session)
    registry = ensure_agmarknet_source(db_session, PARSER_VERSION)
    now = datetime.now(timezone.utc)
    for offset in range(7):
        create_report(db_session, crop, market, registry, modal=str(2000 + offset * 100),
                      fetched_at=now - timedelta(days=6 - offset),
                      report_date=now.date() - timedelta(days=6 - offset),
                      quality_status="LOW" if offset == 0 else "MEDIUM")
    result = client.get(f"/api/v1/prices/trends/{crop.name}", params={"market": market.name}).json()["data"]
    assert result["eligibility"] == "INSUFFICIENT_DATA"
    assert result["observation_count"] == 6
    assert result["trend"] == "UNKNOWN"
