# Packet 11 historical evidence audit

Audit date: 2026-09-18. Scope: price-history eligibility for descriptive statistics and forecasting, and availability of trustworthy platform evidence for intelligence. This audit deliberately separates repository artifacts from production-eligible persisted evidence.

## Decision

No forecast, sale-window recommendation, public accuracy statistic, demand imbalance, realized-price benchmark, channel winner, or payment-reliability statement is eligible for production publication from the evidence currently available in this checkout. This is an evidence outcome, not a failed model build. Packet 04's persisted ingestion pipeline is the only eligible official price path; the local cache and JSON exports below do not satisfy its provenance contract.

## Official persisted observation path

`backend/app/modules/prices/router.py::observations` accepts only observations joined to an active source using parser `agmarknet-data-gov-v1`, registry key `agmarknet-daily-reported-prices`, an active/tradable canonical crop, and a non-null normalized `price_unit`. `PriceObservation` preserves report date, fetch/retrieval timestamps, source record/url, parser and normalization versions, unit provenance, raw payload hash, quality status, and unique observation key (`backend/app/models.py`, `PriceObservation`). These fields can support later auditable series checks.

Packet 04 evidence (`docs/work/04-result.md`) records that no real official observations had been fetched in the verified environment because provider credentials were unavailable. The local `backend/krishilink.db` is a legacy database whose `price_observations` schema predates the Packet 04 source/normalization contract; it contains 960 rows attributed to `DemoPriceAdapter`, across 64 crop/market groups and 15 consecutive dates (2026-09-02 through 2026-09-16). The perfect daily coverage is synthetic/demo evidence. The database lacks the current observation key, normalized price unit, and source-registry/ingestion provenance required by the official path. All 960 rows are excluded from model, benchmark, public-statistic, and alert qualification.

## Unreferenced JSON exports

Six unreferenced `backend/mandi_*.json` files were parsed using UTF-8-with-BOM handling. They contain 1,257 rows total and 830 distinct exact `(crop, market, variety, grade, arrival_date)` dimension keys, leaving 427 duplicate excess rows across overlapping exports. There are two report dates only: `30/08/2026` (1,000 rows) and `11/09/2026` (257 rows). The 257-row `mandi_live_all.json` uses `unit=quintal` and includes per-row `trend`/`change_pct`; the other 1,000 rows do not specify a unit. None of the records contains row-level source identity, source record URL/ID, fetch time, registry identity, or parser/normalization provenance. Several IDs and trend fields look application-generated, and their presence does not prove government origin. No repository production code references these files. They are excluded rather than imported or used as a training set.

| File | Rows | Report date | Unit coverage | Provenance assessment |
|---|---:|---|---|---|
| `backend/mandi_100.json` | 100 | 30/08/2026 | absent | unreferenced export; not eligible |
| `backend/mandi_final_100.json` | 100 | 30/08/2026 | absent | unreferenced export; not eligible |
| `backend/mandi_live_all.json` | 257 | 11/09/2026 | `quintal` present | generated trend fields; no row-level source lineage; not eligible |
| `backend/mandi_raw_200.json` | 200 | 30/08/2026 | absent | unreferenced export; not eligible |
| `backend/mandi_raw_500.json` | 500 | 30/08/2026 | absent | unreferenced export; not eligible |
| `backend/mandi_veg_100.json` | 100 | 30/08/2026 | absent | unreferenced export; not eligible |

## Dataset suitability by intelligence level

| Use | Current evidence | Eligibility |
|---|---|---|
| Raw official reported price display | Packet 04 ingestion contract | Eligible only for rows passing the current API's source/unit filters; provider activation is external |
| Descriptive same-market price history | Eligible persisted observations with compatible crop/market/variety/grade/unit | Conditional; minimum sample and freshness rules are required |
| Forecast training/evaluation | No genuine validated history in the local environment; only demo DB/exports observed | Ineligible; no model is trained or promoted |
| Sale-window recommendation | No eligible validated forecast and no complete evidenced waiting-cost inputs | Abstain |
| Net channel comparison | Actual offers/observations can be shown, but freight/commission/storage fields may be unknown | Side-by-side evidence only; no net ranking when any compared cost is unknown |
| Trust/payment metrics | Packet 10 distinguishes participant payment reports from provider verification; local DB is legacy and contains no current verified settlement evidence | Factual completed-trade counts may be computed only from current canonical terms; payment timing unavailable; no composite score |
| Demand comparison | Requirements store free-text `location_text`, while supply has districts and requirements may use coordinates; reliable common geography is not consistently represented | No demand/supply ratio or scarcity claim |
| Realization benchmark | Immutable accepted terms exist, but payment/settlement is not proven by a completed state alone and local official-price evidence is absent | Report agreed trade facts only; benchmark/uplift unavailable unless comparability and outcome evidence qualify |

## Legacy local database counts (not production evidence)

The local SQLite file contains 95 legacy transactions (9 `COMPLETED`, 61 `CREATED`, 25 `PAYMENT_CONFIRMED`), 31 term snapshots, zero `Payment` rows, 45 disputes (27 open, 18 resolved), zero buyer requirements, and 251 lots (72 drafts, 179 published). Its old schema/status distribution and absent current payment evidence mean these counts are not used for public trust, payment, demand, or realization claims. Counts are documented to explain why apparent local volume is not eligibility.

## Series audit requirements before any future training

For every `(canonical_crop_id, market_id, variety_id-or-null, normalized grade, normalized unit, source/parser/normalization version)` segment, compute: row count; earliest/latest `price_date`; distinct report dates; interval/gap distribution; duplicate observation-key and dimensional-key rates; source/version/unit/grade consistency; freshness relative to prediction time; invalid/outlier/quarantine counts; and missing-date pattern. A segment must not be declared forecast-eligible from total row count alone. Real shocks remain in evaluation unless source evidence proves a malformed record or unit error.

## Limitations and external dependencies

This local audit does not establish that production has zero official observations; it establishes that no locally available validated dataset was present for this task. Production AGMARKNET credentials, a current PostgreSQL/PostGIS environment, and operator access are unavailable here. PostgreSQL locking and migration behavior are not inferred from SQLite. Future activation requires a refreshed audit over the live official observation table and a source/provider freshness check.
