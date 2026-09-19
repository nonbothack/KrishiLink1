# Work Packet 04 — Official Reported Market Price Pipeline Result

**Overall status: PASS_WITH_EXTERNAL_DEPENDENCY**  
**Branch:** `abdulrehman` (`9d61c0e` at start; no commit or push)  
**Scope:** Packet 04 only. Packet 05 was not started.

## 1. Executive summary

The active prices path now ingests official AGMARKNET/data.gov.in daily reported observations through a typed server-side adapter, preserves decimal values and provenance, deduplicates by semantic observation identity, records run/source health, and runs through Celery rather than API startup. Farmer-facing prices show the source report date, source, supported unit, stale state and outlet verification state. Rows with unknown or unsupported units remain in the database for review but are excluded from public price results.

The software path is implemented and tested with mocked provider responses and SQLite. A real provider key, PostgreSQL/PostGIS and Redis were unavailable, so a live fetch, production migration and multi-worker Redis behavior remain unverified. The official source describes daily wholesale minimum, modal and maximum prices from AGMARKNET; its manual permits Rs/quintal or Rs/number depending on variety. Those source facts are why unknown units are not silently converted or labeled quintal. [Official AGMARKNET price resource](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi), [AGMARKNET manual](https://www.agmarknet.gov.in/DailyDataEntry/UserManual.pdf).

## 2. Repository state

Work continued on the existing `abdulrehman` checkout. Prior Packet 00–03 working-tree changes were preserved. No commit, push, branch switch, production-data import, or live provider request was performed.

## 3. Source and license evidence

The official catalog describes a daily AGMARKNET-generated resource with wholesale min/modal/max prices and identifies the Directorate of Marketing and Inspection under the Ministry of Agriculture and Farmers Welfare. The Government Open Data License requires source/provider attribution. The source registry stores that source identity, resource URL, license URL, retrieval method, cadence, unit conventions, known gaps and parser version. [Catalog](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi), [Government Open Data License — India](https://ap.data.gov.in/godl).

## 4. Architecture decisions

- `AgmarknetProvider` is the only active HTTP adapter. It validates the HTTPS data.gov.in host, keeps credentials in `SecretStr` configuration, bounds page size/page count and timeouts, and converts timeout, upstream HTTP, rate-limit, malformed-payload, auth and schema-drift failures into safe categories.
- Nationwide jobs run at 06:00, 13:00 and 18:00 Asia/Kolkata through Celery Beat. Admin/operator refresh requests enqueue work. Optional crop+district refresh supports an optional state filter and persists its scope with the ingestion run.
- The API no longer syncs prices during application startup. A Redis owner-token lease prevents overlapping work; national and per-scope refreshes have 15-minute floors. A missing lock service prevents ingestion from starting.
- Public reads remain database-authoritative and use a 15-minute Redis cache keyed by every filter/page dimension and the latest successful source generation. A cache outage falls back to the database.

## 5. Domain boundaries

The source registry owns provider provenance, license, unit conventions, cadence and health. `PriceSource` identifies the parser adapter; `IngestionRun` records scope, counts, outcome, failure category and duration; `PriceObservation` stores the normalized report. The existing crop and market registries remain canonical. No parallel market/crop registry was added.

## 6. Provider input contract

Required provider fields are state, district, market, commodity, arrival date and minimum/modal/maximum price. The adapter parses supported date formats and `Decimal` values, rejects future or malformed dates, non-finite/negative values, a zero modal price, out-of-order ranges and precision beyond two decimal places. It retains an SHA-256 hash of each normalized source row and any supplied record identifier. Arrival quantity is kept only with an arrival unit.

## 7. Units and quality state

`Rs/quintal` and `Rs/number` normalize to `INR/quintal` and `INR/number`. If the feed omits its unit, an administrator can update `/api/v1/markets/sources/{source_id}` with a crop key such as `Onion` or a crop+variety key such as `Onion::Red`; keys normalize consistently. An unsupported or unconfirmed unit is recorded with low quality and quarantine counts, but has no public price projection. The frontend does not offer an `INR/number` report as a per-quintal sell price.

## 8. Observation identity and upsert

The stable observation key includes source adapter, canonical crop, market identity, variety identity/raw variety, normalized grade and report date. A database unique constraint and PostgreSQL/SQLite conflict upsert make repeated reports idempotent; changed values for the same report identity update the row. Legacy duplicates are preserved during migration and receive distinct keys rather than being merged or deleted.

## 9. Crop and market resolution

Known crops resolve through the Packet 03 canonical registry and aliases. Unknown crops and varieties remain inactive/non-tradable candidates. A unique exact market identity can reuse an existing outlet; otherwise the pipeline stores an inactive review candidate with no inferred coordinates. Prices retain the market label, but public responses identify whether the outlet location is verified and never return candidate coordinates.

## 10. Run state and observability

Each run records fetched, accepted, updated, unchanged, rejected, quarantined, unresolved-market and unresolved-crop counts, duration, scope, parser version and a safe provider-failure category. The source registry records latest attempt/success/failure, SLA, last status and counts. `/api/v1/prices/ops/health` is restricted to admin/operator and reports configuration as a boolean only. `/api/v1/health/detailed` includes price-pipeline freshness and no longer reports the worker healthy without evidence.

## 11. API behavior

- `GET /api/v1/prices` and `/api/v1/prices/live` preserve the existing item envelope and filters, adding page/date/variety/grade support and source, `price_date`, `fetched_at`, unit, freshness and outlet-verification fields. The `live` alias explicitly says the data is daily reported, not live.
- `GET /api/v1/prices/trends/{crop_name}` compares only one market and one variety/grade dimension set; insufficient or mixed observations return `UNKNOWN`. Calculations use `Decimal`.
- `GET /api/v1/prices/{crop_name}/history` retains the path and limits history to 90 reported days.
- `GET /api/v1/prices/{observation_id}/provenance` exposes source URL/record ID, report/fetch timestamps, unit provenance, parser/normalization versions and row hash, but no raw payload or credential.
- `POST /api/v1/prices/sync` remains admin/operator-only and now returns HTTP 202 with a Celery task ID. Crop and district must be supplied together; `force` does not bypass refresh floors.
- `PATCH /api/v1/markets/sources/{source_id}` accepts admin-only unit conventions.

## 12. Freshness behavior

Freshness is calculated from the report date in India time, never from fetch time. The API emits `reported_today`, `reported_yesterday`, `reported_within_7_days`, or `stale`. The RateLookup shows the report date, source and unit, labels older results and de-emphasizes stale values. It does not claim that a daily report is a live quote.

## 13. Cache behavior

List/live query responses are cached for 15 minutes under a versioned key containing crop, district, market, state, variety, grade, date range, page and limit. Successful/partial ingestion updates the source generation so old cached reads stop matching. Redis cache read/write errors are logged without key or credential material and authoritative database reads continue. Redis lock failure does not fall through to an uncoordinated provider call.

## 14. Security changes

`AGMARKNET_API_KEY` and the legacy `MANDI_API_KEY` are server-side `SecretStr` settings and are not included in frontend configuration. Empty environment values normalize to unset. Compose passes the key only to backend, worker and scheduler services. The frontend production build scans generated files for configured secret values and Vite-prefixed provider-key names; the build was tested with test-only sentinels. Provider failures do not echo the key or response body. The demo seeder now refuses production/staging and non-demo mode.

## 15. Removed production hazards

The unreferenced `mandi_api.py` random/generated/sample-rate adapter and the duplicate local JSON `import_mandi.py` loader were removed after a repository reference search found no active callers. The explicit demo seed path remains development-only. Active public price reads have no fabricated fallback.

## 16. Migration

Added `e47b91c6a2d0_official_price_pipeline.py` after Packet 03's `c4e83d2f1a60`. It adds source-registry unit/health metadata, ingestion counters/scope, crop-variety activation flags and report dimensions/fetch time/units/arrival data/semantic key. It backfills `fetched_at` only from existing `retrieved_at`; it does not invent report units or publication timestamps. It creates a unique observation-key constraint and indexes. Downgrade checks for collisions before restoring the old uniqueness model.

An in-memory SQLite smoke run applied the Packet 04 migration to a legacy-shaped schema. It retained two legacy rows sharing an old nullable-source identity, generated unique keys, backfilled known retrieval timestamps and added scope/unit metadata. A full `alembic upgrade head` on SQLite cannot pass the older `0111b944a435` migration because it unconditionally creates a PostgreSQL `USING gist` index. PostgreSQL/PostGIS was not available to verify the complete migration chain.

## 17. Files changed for Packet 04

- Backend: `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/main.py`, `backend/app/models.py`, `backend/app/seed.py`, `backend/app/modules/health/router.py`, `backend/app/modules/markets/router.py`, `backend/app/modules/markets/service.py`, `backend/app/modules/prices/provider.py`, `backend/app/modules/prices/router.py`, `backend/app/modules/prices/sync_service.py`, `backend/app/workers/celery_app.py`, `backend/alembic/env.py`, `backend/alembic/versions/e47b91c6a2d0_official_price_pipeline.py`, `backend/tests/test_packet04_price_pipeline.py`.
- Frontend/runtime configuration: `docker-compose.yml`, `.env.example`, `backend/.env.example`, `frontend/package.json`, `frontend/scripts/check-price-key-secrecy.mjs`, `frontend/src/components/RateLookup.jsx`, `frontend/src/components/RateLookup.test.jsx`, `frontend/src/styles/app.css`, `frontend/src/utils/translations.js`.
- Engineering records: `docs/work/04-plan.md`, `docs/work/04-result.md`, `docs/DECISIONS.md`, `PROGRESS_TRACKER.md`.
- Removed: `backend/app/modules/prices/mandi_api.py`, `backend/app/modules/prices/import_mandi.py`.

## 18. Verification results

| Check | Result |
| --- | --- |
| `DATABASE_URL=sqlite:///./packet04_final_test.db python -m pytest -q` | 145 tests passed, zero failures; one existing pytest-asyncio deprecation warning. |
| Packet 04 provider/sync tests plus health regressions | 16 passed. |
| `python -m ruff check app tests/test_packet04_price_pipeline.py` | Passed. |
| `python -m mypy app` | Passed; 73 source files. |
| `npm run lint` | Passed. |
| `npm test` | 19 tests passed across 4 files. |
| `npm run test:e2e` | 8 desktop/mobile tests passed. |
| `npm run build` with test-only server/Vite key sentinels | Passed; no credential material found in built output. |
| `npm run check:security` | Passed; six matching static security headers and baseline CSP directives. |
| `npm run check:bundle` | Passed; 107.92 KiB gzip initial JS and 113.64 KiB gzip combined initial JS/CSS/static assets. |
| Packet 04 migration smoke | Passed on a legacy-shaped in-memory SQLite schema. |
| `git diff --check` | Passed; Git printed working-tree line-ending conversion warnings for existing CRLF/LF files. |
| `docker compose config --quiet` | Exit 0; Docker warned it could not read the user's Docker config file. |

No pytest test was skipped. `npm run typecheck` could not run because the local TypeScript `tsc` executable is absent. `npm run format:check` could not run because the local Prettier executable is absent. Full migration, Redis coordination and provider integration could not run because PostgreSQL/PostGIS, Redis and an official key are unavailable. The configured key check printed only `false`; no credential value was read or recorded.

## 19. Risks and rollback

- A real feed response and its exact unit-field coverage must be verified after an official key is configured. Until then, source unit conventions must be populated by an operator for the crops/varieties that need public display.
- The 10-page bound deliberately fails a provider result that indicates more pages than the configured maximum instead of marking a partial nationwide dataset complete. The live resource's page volume and API quota were not measurable without a key.
- PostgreSQL conflict behavior, PostGIS migration history, worker lease behavior under process death and cache behavior under Redis outage were not exercised against their production services.
- Before deployment, take a database snapshot and run Alembic on PostgreSQL/PostGIS. Roll back code and schema with `alembic downgrade c4e83d2f1a60` only if no observations now collide under the old crop/market/date/source uniqueness. If the migration refuses due to legitimate variety/grade rows, keep the schema and roll forward with a fix or restore the pre-upgrade snapshot; do not delete or merge observations to force downgrade.
- Restore a previous service image/config to roll back application code. Remove the scheduler service/beat entry only as part of that coordinated rollback; do not remove the new tables/columns while updated workers are running.

## 20. External dependencies and next packet

Required before live activation: an authorized data.gov.in API key configured only as a server secret; PostgreSQL with PostGIS to apply and verify the complete migration chain; Redis for queue, per-scope throttle, owner-token lock and cache; and verification of the actual provider response/unit conventions against a fetched official row. The public dataset is covered by the Government Open Data License subject to its attribution/terms; application attribution includes the source and license links.

The exact next work packet is **Work Packet 05 — Identity, onboarding, authorization and consent**. It was not started.
