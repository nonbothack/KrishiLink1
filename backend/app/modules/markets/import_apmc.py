"""License-aware, idempotent APMC candidate ingestion.

This module intentionally does not geocode or verify imported records. A source
row is evidence that a name appeared in a dataset, not proof of a selling outlet
or a precise coordinate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import DataSourceRegistry, District, Market, State, Subdistrict

PARSER_VERSION = "apmc-candidate-csv-v1"
OUTLET_TYPES = {
    "apmc_principal",
    "apmc_sub",
    "enam_market",
    "private_mandi",
    "fpo_centre",
    "processor_point",
    "government_procurement",
    "warehouse",
    "cold_storage",
    "collection_centre",
    "verified_trader",
    "haat_candidate",
    "market_candidate",
}
HEADER_ALIASES = {
    "name": {"name", "market", "market_name", "outlet", "outlet_name"},
    "district": {"district", "district_name"},
    "state": {"state", "state_name"},
    "subdistrict": {"subdistrict", "taluka", "tehsil", "sub_district"},
    "lat": {"lat", "latitude"},
    "lng": {"lng", "lon", "longitude"},
    "source_ref": {"source_ref", "record_id", "market_code", "apmc_code", "enam_code"},
    "outlet_type": {"outlet_type", "market_type", "type"},
    "state_lgd_code": {"state_lgd_code", "state_code_lgd"},
    "district_lgd_code": {"district_lgd_code", "district_code_lgd"},
    "subdistrict_lgd_code": {"subdistrict_lgd_code", "taluka_lgd_code", "sub_district_code_lgd"},
}


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[\w]+", normalized, flags=re.UNICODE))


def in_india_bounds(latitude: float, longitude: float) -> bool:
    return math.isfinite(latitude) and math.isfinite(longitude) and 6 <= latitude <= 38 and 68 <= longitude <= 98


def _canonical_row(raw: dict[str, str]) -> dict[str, str]:
    headers = {
        re.sub(r"[^a-z0-9]+", "_", unicodedata.normalize("NFKC", key or "").strip().casefold()).strip("_"): value
        for key, value in raw.items()
    }
    result: dict[str, str] = {}
    for canonical, aliases in HEADER_ALIASES.items():
        match = next((headers[key] for key in aliases if key in headers), "")
        result[canonical] = (match or "").strip()
    return result


def _resolve_geography(db: Session, row: dict[str, str]) -> tuple[Any, Any, Any]:
    state = db.query(State).filter(State.lgd_code == row["state_lgd_code"]).first() if row["state_lgd_code"] else None
    district = db.query(District).filter(District.lgd_code == row["district_lgd_code"]).first() if row["district_lgd_code"] else None
    subdistrict = (
        db.query(Subdistrict).filter(Subdistrict.lgd_code == row["subdistrict_lgd_code"]).first()
        if row["subdistrict_lgd_code"]
        else None
    )
    if district and state and district.state_id != state.id:
        raise ValueError("district LGD code does not belong to supplied state")
    if subdistrict and district and subdistrict.district_id != district.id:
        raise ValueError("subdistrict LGD code does not belong to supplied district")
    if subdistrict and not district:
        raise ValueError("subdistrict LGD code requires a resolvable district LGD code")
    return state, district, subdistrict


def ingest_apmc_csv(db: Session, csv_path: Path, source_key: str) -> dict[str, Any]:
    source = db.query(DataSourceRegistry).filter(DataSourceRegistry.source_key == source_key).first()
    if not source or not source.is_active:
        raise ValueError("source_key must reference an active data_source_registry entry")
    if source.license_status not in {"approved", "not_applicable"}:
        raise ValueError("source license/terms are not approved for ingestion")
    if not source.parser_version:
        raise ValueError("source registry must declare parser_version")

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV header row is missing")
            canonical_headers = set(_canonical_row({key: "" for key in reader.fieldnames}).keys())
            if not {"name", "district", "state"}.issubset(canonical_headers):
                raise ValueError("CSV must contain name, district and state columns")
            rows = list(reader)
    except UnicodeDecodeError as exc:
        raise ValueError("CSV encoding is not UTF-8; identify the source encoding before conversion") from exc

    report: dict[str, Any] = {"source_key": source_key, "parser_version": source.parser_version, "fetched": len(rows), "inserted": 0, "duplicates": 0, "review": 0, "rejected": 0, "issues": []}
    for row_number, raw in enumerate(rows, start=2):
        row = _canonical_row(raw)
        try:
            name = " ".join(row["name"].split())
            district_name = " ".join(row["district"].split())
            state_name = " ".join(row["state"].split())
            if not name or not district_name or not state_name:
                raise ValueError("name, district and state are required")
            normalized = normalize_name(name)
            if len(normalized) < 2:
                raise ValueError("name is malformed")
            outlet_type = row["outlet_type"].casefold() or "market_candidate"
            if outlet_type not in OUTLET_TYPES:
                raise ValueError("outlet_type is not a supported canonical type")

            latitude = longitude = None
            if row["lat"] or row["lng"]:
                if not row["lat"] or not row["lng"]:
                    raise ValueError("latitude and longitude must be supplied together")
                latitude, longitude = float(row["lat"]), float(row["lng"])
                if not in_india_bounds(latitude, longitude):
                    raise ValueError("coordinates fall outside India bounds")

            state, district, subdistrict = _resolve_geography(db, row)
            if row["state_lgd_code"] and not state:
                raise ValueError("unknown state LGD code")
            if row["district_lgd_code"] and not district:
                raise ValueError("unknown district LGD code")
            if row["subdistrict_lgd_code"] and not subdistrict:
                raise ValueError("unknown subdistrict LGD code")
            if state and normalize_name(state.name) != normalize_name(state_name):
                raise ValueError("state label does not match the supplied state LGD code")
            if district and normalize_name(district.name) != normalize_name(district_name):
                raise ValueError("district label does not match the supplied district LGD code")

            external_ref = row["source_ref"] or hashlib.sha256(
                "|".join((normalized, normalize_name(district_name), normalize_name(state_name), row["lat"], row["lng"], outlet_type)).encode("utf-8")
            ).hexdigest()
            existing = db.query(Market).filter(
                Market.source_registry_id == source.id, Market.source_ref == external_ref
            ).first()
            if existing:
                report["duplicates"] += 1
                continue

            identity_filters = [Market.normalized_name == normalized]
            identity_filters.append(Market.state_id == state.id if state else Market.state.ilike(state_name))
            identity_filters.append(Market.district_id == district.id if district else Market.district.ilike(district_name))
            similar = db.query(Market).filter(*identity_filters).all()
            review_reasons = []
            if similar:
                review_reasons.append("same normalized name and resolved administrative area exists")
            if not state or not district:
                review_reasons.append("administrative LGD mapping is incomplete")
            if latitude is None:
                review_reasons.append("coordinates unavailable")
            if latitude is not None:
                review_reasons.append("dataset coordinates require independent review")

            market = Market(
                name=name,
                district=district_name,
                state=state_name,
                state_id=state.id if state else None,
                district_id=district.id if district else None,
                subdistrict_id=subdistrict.id if subdistrict else None,
                normalized_name=normalized,
                outlet_type=outlet_type,
                source_registry_id=source.id,
                source_ref=external_ref,
                source_confidence=None,
                external_identifier=row["source_ref"] or None,
                latitude=latitude,
                longitude=longitude,
                location_geog=WKTElement(f"POINT({longitude} {latitude})", srid=4326, extended=True) if latitude is not None else None,
                coordinate_source="dataset_import" if latitude is not None else None,
                coordinate_confidence=None,
                verification_status="needs_review",
                market_type=outlet_type,
                is_active=False,
                metadata_json={"parser_version": source.parser_version, "review_reasons": review_reasons},
            )
            db.add(market)
            db.flush()
            report["inserted"] += 1
            report["review"] += 1
            if review_reasons:
                report["issues"].append({"row": row_number, "status": "needs_review", "reasons": review_reasons})
        except (ValueError, TypeError, OverflowError) as exc:
            report["rejected"] += 1
            report["issues"].append({"row": row_number, "status": "rejected", "reason": str(exc)})
    source.last_success_at = datetime.now(timezone.utc)
    source.parser_version = source.parser_version or PARSER_VERSION
    db.commit()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Import licensed APMC data as unverified review candidates")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--source-key", required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        print(json.dumps(ingest_apmc_csv(db, args.csv_path, args.source_key), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
