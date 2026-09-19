# Packet 00 — Baseline evidence and verification log

## Repository snapshot

- Date: 2026-09-17 (workspace environment Asia/Calcutta).
- Branch: `abdulrehman`.
- HEAD: `9d61c0edbfee8bfdab7fafba06d6e019a66b3d7c` (`fix(ci): pin cross-platform wasm runtime peers`).
- `main`: `43042868f1d09c0a6aa4ae993e1dd2e5eb6becbe`.
- Initial user working tree: modified `AGENTS.md`, untracked `docs/krishilink-v4/` (master and packet files). Preserved unchanged.
- Existing local dev servers on 5173/8000: Vite and Uvicorn were already started by the prior task; they were used for read-only API probes. Uvicorn fell back to `backend/krishilink.db` after PostgreSQL localhost:5432 failed.
- Remote CI/GitHub Actions state was not queried. No commit or push was performed.

## Branch diff inventory versus main

Current branch is five commits ahead of `main` at this audit point (HEAD plus earlier auth, FPO, UI and trade-room commits in graph). `git diff --stat main...HEAD`: 131 changed paths, approximately 11,696 insertions and 20,403 deletions. Major changes include auth/session hardening, price ingestion/provenance, outbox/security, trade-room backend/page, CI Node 24 alignment, and broad frontend deletions/simplification. Exact paths can be inspected with `git diff --name-status main...HEAD`.

Selected `main` functionality worth evaluating for selective recovery:

- `frontend/src/components/ui/`: reusable EmptyState, Skeleton, Stepper, MoneyBreakdown, FileUploader, MobileBottomNav/Action, Toast and StatusBadge. Review/accessibility/security harden each before recovery; no wholesale merge.
- `frontend/src/components/map/MarketMap.jsx`: richer map layout and categories, but code itself generates fallback buyers/storage/FPOs and deterministic pseudo-data; do not recover its data generator or present fallback entries as real.
- `frontend/src/pages/LandingPage.jsx` (989 lines), `FarmerDashboard.jsx` (732), `PricesPage.jsx` (583), `Footer.jsx` (134): richer product explanation, quick workflows and market intelligence to mine for layout ideas. Their logic/data contract must be compared against current truthful API interfaces before recovery.
- `frontend/src/utils/cropImages.js`, `components/Badges.jsx`, `components/States.jsx`: reusable crop asset mapping/status presentation candidates; verify asset provenance and translated labels.

`main` can be useful for UI behavior and structure, but the old map source has synthetic fallback data and is unsuitable as a direct restoration.

## Commands and results

| Command/check | Result | Notes |
|---|---|---|
| `git branch --show-current`, `git status --short --branch`, `git log -8` | PASS | `abdulrehman`; pre-existing user changes present |
| `git diff --stat main...HEAD` / `git diff --name-status main...HEAD` | PASS | 131 paths, large UI deletions and hardening additions |
| `python -m pytest -v` (from `backend/`) | PASS | 109 passed, 0 failed, 0 skipped, 1 pytest-asyncio deprecation warning; 122.78 sec; Python 3.14.3, pytest 8.4.2 |
| `python -m ruff check app` | PASS | “All checks passed!” |
| `python -m mypy app` | PASS | 0 issues in 69 source files |
| `npm run lint` (from `frontend/`) | PASS | oxlint, no diagnostics |
| `npm run test` | PASS | 2 files, 6 tests passed; no skips reported |
| `npm run build` | PASS | Vite build success; entry JS 247.52 KB raw / 79.43 KB gzip. Leaflet route chunk 154.79 KB raw / 45.68 KB gzip. Other route chunks are lazy; initial resource waterfall was not measured. |
| `npm run test:e2e` | PASS | 4 passed (2 specs × desktop and Pixel 5/mobile), 10.4 sec; public home axe serious/critical and overflow check; APIs mocked in E2E |
| `Invoke-RestMethod /api/v1/openapi.json` | PASS | OpenAPI 3.1.0, 70 operations, KrishiLink API 2.0.0 |
| `GET /api/v1/health` | PARTIAL | HTTP 200; status `ok`, mode `demo`, env `development` |
| `GET /api/v1/health/detailed` | PARTIAL | HTTP 200; observed DB healthy via SQLite, Redis down, API healthy, worker incorrectly hardcoded healthy, overall degraded |
| Unauthenticated protected probes (`users/me`, `admin/users`, outbox, offers, transactions, disputes) | PASS | Each returned HTTP 401 |
| `npm audit --omit=dev --json` | PASS | 0 advisories, 75 runtime deps |
| `python -m pip check` | FAIL | Global Python conflicts: grpcio-status/protobuf, gtts/click, opentelemetry-exporter-otlp-proto-common/opentelemetry-proto |
| `pip-audit -r requirements.txt` | BLOCKED | Python 3.14 cannot resolve pinned psycopg binary 3.2.5 in audit temp env; no backend vulnerability conclusion |
| `python -m alembic heads/history` | PASS | One head `790546cf29fe`; linear chain after no-op merge migration |
| `DATABASE_URL=sqlite:///...packet00_migration_test.db python -m alembic upgrade head` | FAIL | Fails at first migration because Alembic env import eagerly runs ORM `create_all`, then migration creates existing `system_configurations`; SQLite is not a supported migration proof. No real PostgreSQL/PostGIS available to verify production migration. |
| Docker/Compose inspection | PARTIAL | Compose declares PostGIS/Redis/backend/worker/frontend; Docker daemon unavailable, containers not started |
| Lighthouse | NOT RUN | Lighthouse executable not installed; no server/browser profiling or field Web Vitals available |
| Accessibility | PARTIAL | axe passes home only on desktop/mobile E2E. Full-route axe and manual keyboard/TalkBack/200% zoom not performed. |
| `npm sbom --package-lock-only --sbom-format cyclonedx` | PASS | Generated `00-frontend-sbom.cdx.json`, 237,810 bytes; derived from lockfile, not active install attestation |
| `git status --short` | PASS | Must be rerun at finalization; app code not intentionally changed |

## Environment matrix

| Component | Declared | Observed here | Readiness conclusion |
|---|---|---|---|
| Backend CI | Python 3.13 | Python 3.14.3 global; full tests nevertheless pass | Re-run pinned/audit matrix under Python 3.13 |
| Frontend CI | Node 24 | Node 24.13.0, npm 11.6.2 | Matches Node major |
| Production DB | PostgreSQL/PostGIS; Compose maps host 5435 | PostgreSQL connection refused/unavailable; local SQLite fallback | PostGIS functions/indexes/concurrency not dynamically validated |
| Redis | Redis 7 in Compose, host 6380 | DOWN at default redis://localhost:6379/0 | Single-process fallback only; multi-worker session/rate correctness not assured |
| Celery | Compose worker service | no Docker daemon/worker | Outbox dispatch/worker health unverified |
| Object storage | optional S3 endpoint/credentials | absent | Upload/download flows external dependency |
| Mandi source | data.gov.in key optional | no confirmed key/source health | Active sync truthfully returns unavailable without key |
| Payment | sandbox/mock | explicitly simulated | Real settlement external/regulatory dependency |
| Browser | Playwright Edge channel | E2E succeeds desktop/mobile | limited route/workflow coverage |
| GitHub CI | GitHub Actions | not queried | green remote CI not established |

## Test inventory

Backend: 17 test modules, 109 collected/executed tests, covering health/OpenAPI/crops, auth, four role journeys, earnings, FPO, auth/integration, lots, geo/prices, offers, transactions, matching, pagination, rate limit, scoped idempotency, SMS and Trade Room. Fixture `backend/conftest.py` calls `Base.metadata.create_all`, creates fixed test users/markets/crops and SQLite defines PostGIS stubs; these tests are reproducible behavior checks but not a production database migration or data provenance audit. 0 skipped.

Frontend: Vitest `frontend/src/lib/produce.test.js` and `session.test.js` (6 tests total); E2E has two specs, each desktop and mobile (4 runs). API responses are mocked. E2E covers public home/axe/overflow and a mocked login intent to sell form. No route contract, query-parameter contract, all-role journey, transaction/payment E2E, production API schema contract, Lighthouse or CI E2E.

## Performance and UI baseline

`npm run build` emits lazy route chunks. Entry gzip is 79.43 KB, but no browser network waterfall determined actual initial JS. Build lists the Leaflet chunk at 45.68 KB gzip. No measured LCP/INP/CLS or Slow-3G/CPU throttle baseline; image dimensions/individual bytes were not audited. The E2E checks horizontal overflow at its configured desktop and Pixel 5 viewports only. Frontend sources are frequently minified into one-line JSX; current `LandingPage.jsx` is 14 lines vs 989 on `main`; `FarmerDashboard.jsx` 10 vs 732; `PricesPage.jsx` 4 vs 583; Footer 4 vs 134. `npm run lint` does not enforce formatting or Prettier.

## Baseline backup / reproducibility

The source baseline is identified by branch+HEAD+main SHA above; complete branch delta remains recoverable in Git. Frontend lockfile-derived CycloneDX SBOM is checked in under this packet. `docs/krishilink-v4/MASTER_SPEC.md` and packet files are user-provided untracked inputs and retained. No secrets, production database, SQLite test DB, or generated app assets are intentionally archived. User-provided `AGENTS.md` modification is retained. This document set is itself the audit snapshot; no branch archive was created to avoid duplicating the repository.
