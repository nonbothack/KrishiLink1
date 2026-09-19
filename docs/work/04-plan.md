# Work Packet 04 — Official Reported Market Price Pipeline Plan

**Branch:** `abdulrehman`  
**Baseline:** Packet 03 worktree, 132 backend tests and 18 frontend unit tests.  
**Scope:** Packet 04 only. No commit/push. Existing user and prior-packet changes are preserved.

## Verified current state

- `/api/v1/prices` and `/live` query persisted `PriceObservation`, but serialize money through `float`, report a hard-coded quintal unit, omit fetch time/freshness, and filter only on parser version `agmarknet-record-v3`.
- `sync_service.py` calls data.gov.in directly, makes a single request, treats provider failure as an empty list, parses money using float, drops varieties/grades, performs application-only duplicate checks, and returns inserted count only. `PriceObservation` has `variety_id`, ingestion run, raw hash and reported date, but no grade, normalized/source unit, fetched timestamp or semantic unique key. The existing unique constraint collapses legitimate varieties/grades.
- `main.py` synchronously starts a provider sync during API startup. Celery already handles retries/outbox and has beat schedules for other jobs, but no price task or beat/scheduler service is configured in Compose.
- `/health/detailed` hardcodes worker healthy and has no price freshness/provider state. Price reads have no Redis cache.
- `mandi_api.py` is not referenced by active routes but contains random generated prices, hardcoded price histories and supplemental “verified” rates. `import_mandi.py` is an unreferenced second loader using a local JSON file and float values.
- `seed.py` explicitly seeds `demo://local` observations from `backend/data/demo_data.py`, but has no production-environment guard.
- `PriceSource`, `IngestionRun`, `DataSourceRegistry` and Packet 03 market/crop candidate helpers already exist and should be extended instead of creating parallel tables.
- Existing public API calls are through the DB-backed router. Frontend `RateLookup` displays a reported date, but hardcodes “per quintal” and does not distinguish freshness/provider source.
- The official AGMARKNET data.gov.in catalog describes daily wholesale min/modal/max prices. AGMARKNET documentation states its standard price unit may be Rs/quintal or Rs/number by variety, and local-unit conversions are source-configured. The upstream API key is not assumed available and no live sync will be triggered during implementation.

## Intended changes

1. Add a typed, injectable data.gov.in provider adapter with bounded pagination/timeout, schema checks, Decimal parsing, date parsing, unit normalization, row-level invalid classification and safe provider error classes. Keep all credential use server-side and avoid secret-bearing logs/errors.
2. Add a deterministic observation identity over provider source, crop, market, variety, grade and `price_date`; persist via database uniqueness/upsert. Preserve corrected same-identity reports as updates. Store `fetched_at`, reported/source price unit, grade, arrival quantity/unit only when supplied, source record/hash, parser version and run ID.
3. Resolve crop and variety canonically. Unknown crops/varieties become inactive candidates. Resolve markets against unique exact existing identities; use verified outlet, review candidate, or create a source-linked inactive review candidate without coordinates. Preserve observations regardless of outlet verification.
4. Record per-run fetched/accepted/updated/rejected/quarantined/unresolved counts, safe failure category, duration and source last-attempt/success/failure. Add admin/operator price health and overall health metadata that distinguishes application state from provider degradation.
5. Move national sync into Celery and configure three India-time daily schedules. Queue the existing admin/operator sync endpoint, support bounded crop+district refresh (optional state), enforce a 15-minute national and per-scope refresh floor, bounded provider retry/backoff and a Redis owner-token lease that expires after worker crashes. If distributed coordination is unavailable, do not start a sync.
6. Add a Redis read-through cache over DB-authoritative responses with every query dimension in the key, 15-minute TTL and a versioned namespace incremented after ingest. Redis failure bypasses cache and reads the DB.
7. Add shared reported-date freshness and enriched price API metadata; preserve route/envelope compatibility, deterministic history, variety/grade dimensions and safe page/date-range bounds. Never label the daily feed “live”.
8. Make minimal RateLookup changes for source/unit/reported date/freshness and stale emphasis; add 3-language copy. No charts, forecast, homepage, or unrelated screen redesign.
9. Remove the unused random/supplemental legacy prices module and duplicate local-file importer. Guard the explicit demo seeder against production/staging use.
10. Add focused backend provider, validation, idempotency, market/crop-resolution, freshness, cache, secret and failure tests; frontend unit coverage for metadata/staleness. Add an Alembic migration preserving existing observation rows, indexes and `retrieved_at` compatibility.

## Expected files/tables/endpoints

- `backend/app/models.py`, price provider/service/router, worker Celery app, health router, config, main lifespan, Compose.
- Alembic additions to `price_sources`, `ingestion_runs`, `price_observations`, `crop_varieties`, `data_source_registry`.
- `/api/v1/prices` compatible read route, existing admin/operator `POST /api/v1/prices/sync` queued, plus protected price operations/health view and detailed system health metadata.
- `frontend/src/components/RateLookup.jsx`, translations and price metadata tests; Vite output secret check.
- `docs/DECISIONS.md`, `PROGRESS_TRACKER.md`, `docs/work/04-plan.md`, `docs/work/04-result.md`.

## Migration/runtime risks

- Replace the old unique constraint without deleting historical rows; preserve legitimate variety/grade distinctions and map legacy rows to stable keys.
- Existing historical observations do not contain a verified unit. Do not backfill them as quintal; keep unit unknown and exclude them from the public price projection until reviewed or source metadata establishes the unit.
- The provider documentation allows per-variety Rs/quintal or Rs/number. Rows lacking an explicit/approved unit mapping must be quarantined, not silently normalized to quintal.
- PostgreSQL/PostGIS/Redis and the real key are unavailable in this environment per prior packet evidence. Migration compilation/history, mocked provider contract tests and local SQLite tests can run; real scheduler/lock/Redis/provider verification must be reported as external.
- AGMARKNET's documented report unit may be Rs/quintal or Rs/number by variety. Unit conventions are source-registry mappings maintained by an administrator; unconfirmed units remain quarantined and are hidden from public price results.

## Test plan

- Preserve the 132 backend / 18 frontend baseline.
- Provider fixture tests for expected field mapping, dates, varieties, units, Decimals, schema drift, timeout/429/auth/upstream errors and row-level rejection.
- Database tests for semantic repeat/upsert identity, concurrent duplicate conflict, unknown crop/market candidates, unresolved vs review vs verified outlet, observation retention and Decimal ranges.
- API tests for envelope/compatibility, truthful source/date/fetch/freshness, unit and outlet status, date bounds, history ordering and protected ops health.
- Cache tests for dimension-complete keys, invalidation and Redis absence.
- Secret regression test: build with test-only server credential environment values and assert they are absent from all frontend output.
- Full backend pytest, Ruff, mypy; frontend lint, unit tests, build and existing bundle/security gates; compile migration, inspect Alembic history, diff check and search prohibited fallbacks.
