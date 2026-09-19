"""Typed boundary for the official daily reported AGMARKNET resource."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx

from app.core.config import Settings, settings

RESOURCE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
PARSER_VERSION = "agmarknet-data-gov-v1"
NORMALIZATION_VERSION = "reported-price-decimal-v1"
REQUIRED_FIELDS = (
    "state",
    "district",
    "market",
    "commodity",
    "arrival_date",
    "min_price",
    "modal_price",
    "max_price",
)
MAX_PAGE_SIZE = 1000
MAX_PAGES = 10
REQUEST_TIMEOUT_SECONDS = 12.0


class ProviderFailureKind(StrEnum):
    TIMEOUT = "timeout"
    UPSTREAM_HTTP = "upstream_http_error"
    MALFORMED_PAYLOAD = "malformed_payload"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth_failure"
    SCHEMA_DRIFT = "schema_drift"


class PriceProviderError(RuntimeError):
    def __init__(self, kind: ProviderFailureKind, *, status_code: int | None = None, retry_after: int | None = None):
        super().__init__(kind.value)
        self.kind = kind
        self.status_code = status_code
        self.retry_after = retry_after

    @property
    def retryable(self) -> bool:
        return self.kind in {ProviderFailureKind.TIMEOUT, ProviderFailureKind.RATE_LIMIT} or (
            self.kind == ProviderFailureKind.UPSTREAM_HTTP and (self.status_code or 0) >= 500
        )


@dataclass(frozen=True)
class NormalizedPriceRecord:
    state: str
    district: str
    market: str
    market_code: str | None
    commodity: str
    variety: str | None
    grade: str | None
    min_price: Decimal
    modal_price: Decimal
    max_price: Decimal
    price_date: date
    source_unit: str | None
    price_unit: str | None
    arrival_quantity: Decimal | None
    arrival_unit: str | None
    source_record_id: str | None
    raw_payload_hash: str


@dataclass(frozen=True)
class ProviderFetchResult:
    records: tuple[NormalizedPriceRecord, ...]
    fetched_count: int
    rejected_count: int
    rejection_reasons: tuple[str, ...]


def normalize_price_unit(value: str | None) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.casefold().replace("₹", "rs").split())
    normalized = normalized.replace(".", "").replace(" ", "")
    if normalized in {"rs/quintal", "rsperquintal", "inr/quintal", "inrperquintal", "rs/qtl", "inr/qtl"}:
        return "INR/quintal"
    if normalized in {"rs/number", "rspernumber", "inr/number", "inrpernumber"}:
        return "INR/number"
    return None


def _decimal(raw: Any, field: str) -> Decimal:
    if isinstance(raw, bool) or raw is None:
        raise ValueError(f"missing_{field}")
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"invalid_{field}") from None
    if not value.is_finite():
        raise ValueError(f"invalid_{field}")
    return value


def _reported_date(value: Any) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing_price_date")
    raw = value.strip()
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            result = datetime.strptime(raw, pattern).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError("invalid_price_date")
    if result > datetime.now(ZoneInfo("Asia/Kolkata")).date():
        raise ValueError("future_price_date")
    return result


def normalize_record(raw: Any) -> NormalizedPriceRecord:
    if not isinstance(raw, dict):
        raise ValueError("record_not_object")
    missing = [key for key in REQUIRED_FIELDS if raw.get(key) is None or not str(raw.get(key)).strip()]
    if missing:
        raise ValueError(f"missing_required:{','.join(missing)}")
    state, district, market, commodity = (str(raw[key]).strip() for key in ("state", "district", "market", "commodity"))
    price_date = _reported_date(raw.get("arrival_date"))
    minimum, modal, maximum = (
        _decimal(raw.get(key), key) for key in ("min_price", "modal_price", "max_price")
    )
    if min(minimum, modal, maximum) < 0 or modal <= 0:
        raise ValueError("negative_or_zero_modal_price")
    if not minimum <= modal <= maximum:
        raise ValueError("price_range_order_invalid")
    if min(minimum.as_tuple().exponent, modal.as_tuple().exponent, maximum.as_tuple().exponent) < -2:
        raise ValueError("unsupported_price_precision")
    unit_text = raw.get("price_unit") or raw.get("price_unit_name")
    unit_text = str(unit_text).strip() if unit_text is not None else None
    arrival_raw = raw.get("arrival_quantity") or raw.get("arrival_qty") or raw.get("arrival")
    arrival_unit = str(raw.get("arrival_unit") or "").strip() or None
    arrival_quantity = _decimal(arrival_raw, "arrival_quantity") if arrival_raw not in (None, "") else None
    if arrival_quantity is not None and (arrival_quantity <= 0 or not arrival_unit):
        # Price data remains useful; unknown arrival units are deliberately omitted.
        arrival_quantity, arrival_unit = None, None
    raw_bytes = json.dumps(raw, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    raw_id = raw.get("record_id") or raw.get("id")
    return NormalizedPriceRecord(
        state=state,
        district=district,
        market=market,
        market_code=str(raw.get("market_code")).strip() if raw.get("market_code") else None,
        commodity=commodity,
        variety=str(raw.get("variety")).strip() if raw.get("variety") else None,
        grade=str(raw.get("grade")).strip() if raw.get("grade") else None,
        min_price=minimum,
        modal_price=modal,
        max_price=maximum,
        price_date=price_date,
        source_unit=unit_text,
        price_unit=normalize_price_unit(unit_text),
        arrival_quantity=arrival_quantity,
        arrival_unit=arrival_unit,
        source_record_id=str(raw_id).strip() if raw_id else None,
        raw_payload_hash=digest,
    )


def _safe_retry_after(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return min(max(int(value), 1), 900)
    except ValueError:
        return None


class AgmarknetProvider:
    def __init__(self, *, api_key: str, resource_url: str = RESOURCE_URL, timeout: float = REQUEST_TIMEOUT_SECONDS):
        parsed = urlparse(resource_url)
        if parsed.scheme != "https" or not parsed.hostname or not (
            parsed.hostname == "data.gov.in" or parsed.hostname.endswith(".data.gov.in")
        ):
            raise ValueError("AGMARKNET endpoint must use HTTPS on a data.gov.in host")
        if not api_key.strip():
            raise PriceProviderError(ProviderFailureKind.AUTH)
        self._api_key = api_key.strip()
        self.resource_url = resource_url
        self.timeout = timeout

    @classmethod
    def from_settings(cls, source_settings: Settings = settings) -> AgmarknetProvider:
        secret = source_settings.agmarknet_api_key or source_settings.mandi_api_key
        if secret is None:
            raise PriceProviderError(ProviderFailureKind.AUTH)
        return cls(api_key=secret.get_secret_value(), resource_url=source_settings.mandi_api_url)

    def fetch(self, *, limit: int = MAX_PAGE_SIZE, scope: dict[str, str] | None = None) -> ProviderFetchResult:
        page_size = min(max(limit, 1), MAX_PAGE_SIZE)
        accepted: list[NormalizedPriceRecord] = []
        rejected_count = 0
        rejection_reasons: list[str] = []
        total = None
        fetched = 0
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False, headers={"Accept": "application/json", "User-Agent": "KrishiLink-Reported-Prices/1.0"}) as client:
                for page in range(MAX_PAGES):
                    offset = page * page_size
                    params = {"api-key": self._api_key, "format": "json", "limit": page_size, "offset": offset}
                    if scope:
                        params.update({f"filters[{field}]": value for field, value in scope.items()})
                    response = client.get(
                        self.resource_url,
                        params=params,
                    )
                    if response.status_code == 429:
                        raise PriceProviderError(ProviderFailureKind.RATE_LIMIT, status_code=429, retry_after=_safe_retry_after(response.headers.get("Retry-After")))
                    if response.status_code in {401, 403}:
                        raise PriceProviderError(ProviderFailureKind.AUTH, status_code=response.status_code)
                    if response.status_code >= 400:
                        raise PriceProviderError(ProviderFailureKind.UPSTREAM_HTTP, status_code=response.status_code)
                    try:
                        payload = response.json()
                    except (ValueError, json.JSONDecodeError):
                        raise PriceProviderError(ProviderFailureKind.MALFORMED_PAYLOAD) from None
                    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
                        raise PriceProviderError(ProviderFailureKind.SCHEMA_DRIFT)
                    rows = payload["records"]
                    if rows and isinstance(rows[0], dict):
                        keys = set(rows[0])
                        if all(key not in keys for key in REQUIRED_FIELDS):
                            raise PriceProviderError(ProviderFailureKind.SCHEMA_DRIFT)
                    fetched += len(rows)
                    try:
                        total = int(payload["total"]) if payload.get("total") is not None else total
                    except (ValueError, TypeError):
                        total = total
                    for raw in rows:
                        try:
                            accepted.append(normalize_record(raw))
                        except ValueError as exc:
                            rejected_count += 1
                            rejection_reasons.append(str(exc))
                    if len(rows) < page_size or (total is not None and offset + len(rows) >= total) or not rows:
                        break
                else:
                    if total is not None and fetched < total:
                        raise PriceProviderError(ProviderFailureKind.SCHEMA_DRIFT)
        except httpx.TimeoutException:
            raise PriceProviderError(ProviderFailureKind.TIMEOUT) from None
        except httpx.RequestError:
            raise PriceProviderError(ProviderFailureKind.UPSTREAM_HTTP) from None
        return ProviderFetchResult(tuple(accepted), fetched, rejected_count, tuple(rejection_reasons))


def configured_provider() -> AgmarknetProvider:
    return AgmarknetProvider.from_settings()
