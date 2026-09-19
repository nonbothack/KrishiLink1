"""Outlet identity and source-registry helpers."""

import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DataSourceRegistry, Market
from app.modules.markets.import_apmc import normalize_name

AGMARKNET_SOURCE_KEY = "agmarknet-daily-reported-prices"
AGMARKNET_RESOURCE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
GODL_URL = "https://data.gov.in/godl"


@dataclass(frozen=True)
class PriceMarketResolution:
    market: Market
    resolution: str


def ensure_agmarknet_source(db: Session, parser_version: str) -> DataSourceRegistry:
    source = db.query(DataSourceRegistry).filter_by(source_key=AGMARKNET_SOURCE_KEY).first()
    if source is None:
        source = DataSourceRegistry(
            id=uuid.uuid4(),
            source_key=AGMARKNET_SOURCE_KEY,
            name="AGMARKNET daily reported mandi prices",
            owner="Directorate of Marketing and Inspection, Ministry of Agriculture and Farmers Welfare",
            url=AGMARKNET_RESOURCE_URL,
            license_name="Government Open Data License - India",
            license_url=GODL_URL,
            license_status="approved",
            retrieval_method="data.gov.in resource API",
            schema_version="data.gov.in resource JSON records",
            expected_cadence="three times daily; source reports daily observations",
            geographic_coverage="India, source-reported markets",
            freshness_sla_seconds=24 * 60 * 60,
            dedupe_key="source+market+crop+variety+grade+price_date",
            parser_version=parser_version,
            unit_conventions={},
            known_gaps=["No physical outlet coordinates from price resource", "Unit may vary by commodity variety"],
            is_active=True,
        )
        db.add(source)
        db.flush()
    elif source.license_status == "unknown":
        # This particular resource page declares the Government Open Data License.
        source.license_status = "approved"
        source.license_name = "Government Open Data License - India"
        source.license_url = GODL_URL
        source.parser_version = parser_version
    return source


def ensure_data_source(
    db: Session,
    *,
    source_key: str,
    name: str,
    owner: str | None,
    url: str | None,
    parser_version: str,
    retrieval_method: str,
    dedupe_key: str,
) -> DataSourceRegistry:
    source = db.query(DataSourceRegistry).filter_by(source_key=source_key).first()
    if source:
        return source
    source = DataSourceRegistry(
        id=uuid.uuid4(), source_key=source_key, name=name, owner=owner, url=url,
        license_status="unknown", retrieval_method=retrieval_method,
        parser_version=parser_version, dedupe_key=dedupe_key,
    )
    db.add(source)
    db.flush()
    return source


def resolve_price_market(
    db: Session,
    *,
    name: str,
    district: str,
    state: str,
    market_code: str | None,
    source_registry: DataSourceRegistry,
    parser_version: str,
) -> PriceMarketResolution:
    name_key, district_key, state_key = map(normalize_name, (name, district, state))
    if market_code:
        coded = db.query(Market).filter(Market.external_identifier == market_code).all()
        if len(coded) == 1:
            market = coded[0]
            return PriceMarketResolution(
                market=market,
                resolution="verified_outlet" if market.verification_status == "verified" and market.is_active else "review_candidate",
            )

    regional = db.query(Market).filter(
        func.lower(Market.state) == state.casefold(),
        func.lower(Market.district) == district.casefold(),
    ).all()
    exact = [
        market for market in regional
        if normalize_name(market.name) == name_key
        and normalize_name(market.district or "") == district_key
        and normalize_name(market.state or "") == state_key
    ]
    if len(exact) == 1:
        market = exact[0]
        return PriceMarketResolution(
            market=market,
            resolution="verified_outlet" if market.verification_status == "verified" and market.is_active else "review_candidate",
        )

    identity = "|".join((state_key, district_key, name_key, market_code or ""))
    source_ref = "price-market:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
    candidate = db.query(Market).filter_by(source_registry_id=source_registry.id, source_ref=source_ref).first()
    if candidate is None:
        candidate = Market(
            id=uuid.uuid4(),
            name=name,
            district=district,
            state=state,
            is_active=False,
            normalized_name=name_key,
            outlet_type="market_candidate",
            source_registry_id=source_registry.id,
            source_ref=source_ref,
            source_confidence=None,
            external_identifier=market_code,
            verification_status="needs_review",
            coordinate_source=None,
            coordinate_confidence=None,
            latitude=None,
            longitude=None,
            location_geog=None,
            metadata_json={
                "source_note": "market label appeared in official price observations; outlet location/access not verified",
                "parser_version": parser_version,
                "ambiguous_existing_matches": len(exact) > 1,
            },
        )
        db.add(candidate)
        db.flush()
    return PriceMarketResolution(market=candidate, resolution="unseen_candidate" if not exact else "review_candidate")
