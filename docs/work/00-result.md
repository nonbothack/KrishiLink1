# Work Packet 00 — Repository truth and baseline — result

## Overall status

**PASS_WITH_EXTERNAL_DEPENDENCY**

Packet 00 produced the branch comparison, architecture/data map, capability matrix, security/provider inventory, environment and test baselines, a capability register, and a lockfile-derived frontend SBOM. The declared backend/frontend checks and the limited browser/API baseline ran successfully. PostgreSQL/PostGIS migration/runtime evidence, Python dependency vulnerability evidence, Lighthouse metrics, full-route accessibility, and remote CI remain dependent on unavailable production-like infrastructure or tooling. Production blockers found are documented; Packet 00 is an audit, so no application fix was started.

## 1. Executive summary

The repo is a substantial FastAPI/React marketplace, not a blank prototype. It has working local tests, authentication, role-aware operations, a dated official mandi-price ingestion path, lots, matching, offer negotiation, transaction and trade-room models/routes, FPO aggregation, disputes, outbox, and provider interfaces. Local declared gates are green: backend tests (109), Ruff, mypy, frontend lint, six Vitest tests, four Playwright runs and Vite build. npm production dependencies have no reported advisories.

The repository is not production-ready. High-risk findings include unauthenticated S3 bucket enumeration and arbitrary presigning, fabricated buyer rating/distance/offer claims, unscoped reservation reads for FPO/other roles, authenticated arbitrary SMS relay, password reset tokens retained in outbox payloads, fabricated contractual trade defaults, fabricated proximity coordinates, float-based financial calculations, and a Vite development server in the frontend Docker image. The current health endpoint also reports a healthy worker without checking one. These need decisions/fixes before affected workflows handle real users or data.

## 2. Repository state

- Branch `abdulrehman`, HEAD `9d61c0edbfee8bfdab7fafba06d6e019a66b3d7c`; `main` at `43042868f1d09c0a6aa4ae993e1dd2e5eb6becbe`.
- `abdulrehman` is five commits ahead of `main`; `git diff --stat main...HEAD` showed 131 changed paths, about 11,696 insertions and 20,403 deletions.
- At audit start the user’s `AGENTS.md` change and untracked `docs/krishilink-v4/` master/packet inputs were present. Both were preserved.
- Root historical documentation names `feature/production-rebuild-2.0` and old automatic push rules; current `AGENTS.md` and user branch direction use `abdulrehman` and no automatic commits/pushes. The progress tracker’s older claims are stale; a dated correction was appended.
- No source code, migration or endpoint was changed. No commit or push was made.

## 3. Verified capabilities

See [00-capability-matrix.md](00-capability-matrix.md) for the required matrix. Confirmed executable/local behavior includes:

- FastAPI startup, health, OpenAPI, and 70 runtime API operations.
- Protected API probes return 401 without credentials.
- 109 backend tests pass; this includes auth, RBAC/role journeys, lots, market geo, offers, transaction FSM, matching, idempotency, SMS and trade-room tests.
- Frontend route rendering/build, six unit tests, and four desktop/mobile Playwright runs pass. Home-page axe checks have no serious/critical violations in tested states.
- Active official price router filters to `agmarknet-record-v3` observations and preserves source/date/provenance. Missing source records cause unavailable/empty results rather than invoking the legacy fake price fallback.
- Alembic has one graph head `790546cf29fe`; current ORM declares 32 entities.
- npm production dependency audit reported 0 advisories. CycloneDX SBOM is from package lock, not a deployed image.

“Verified” is limited to current test/probe scope. Most backend tests use SQLite and fake spatial functions; Playwright uses mocked APIs.

## 4. Regressions and unreachable code

- Compared with `main`, substantial UI surface and reusable components were deleted. Current `LandingPage.jsx` is 14 lines vs 989 in `main`; Farmer dashboard 10 vs 732; prices 4 vs 583; footer 4 vs 134. Current is simpler and builds, but farmer market intelligence is thin. Review `main` components selectively; old map generates deterministic synthetic buyers/storage/FPOs and must not be revived with its generated data.
- Dense single-line JSX prevents review and makes regressions harder to locate; lint does not enforce formatting.
- Trade Room UI exists but dashboard navigation does not expose a trade link; storage, reservations, admin and notifications are not surfaced as complete workflows. Backend API methods exist for some absent UI.
- `backend/app/modules/prices/mandi_api.py` is a duplicate legacy implementation with fabricated fallback data; active price routes use `sync_service.py` instead. Keep the legacy fallback unreachable or remove it in a scoped future change.
- Frontend still ships unused competing base CSS and experience CSS; verify actual rule usage before removal.
- `/terms` and `/privacy` are generic policy-status content, despite registration collecting personal data. Unknown routes render a styled fallback but have no HTTP 404 status/logging.
- Historical `PROGRESS_TRACKER.md` asserted hardening phases complete and 109 tests, while other docs also name different branch/test counts. The dated correction records this audit.

## 5. Production blockers

See the security/provider inventory. Priorities before a pilot:

1. Close unauthenticated S3 inventory/presign routes and enforce evidence ownership/key constraints.
2. Remove fabricated buyer profiles/metrics and false coordinate/market-distance assumptions.
3. Scope reservation reads by owner/FPO; explicitly gate admin/support reads.
4. Replace synthetic contractual fallbacks with required source terms and validated trade state.
5. Keep Decimal through monetary calculations and enforce canonical quantity units server-side.
6. Restrict/remove arbitrary test-SMS dispatch; prevent reset tokens from being stored in readable event payloads.
7. Run migrations and tests against PostgreSQL/PostGIS; current SQLite tests stub spatial operations and migration bootstrap fails due eager table creation.
8. Replace the frontend Docker Vite dev-server command with a production serving strategy, configure headers/secrets/proxy trust, and validate deployment/backup/restore.
9. Fix health/readiness reporting and prove worker/outbox operation.
10. Add all-route accessibility, critical workflow E2E, route/query contract tests, Lighthouse and dependency-security gates.

## 6. Security issues

Detailed evidence is in `00-security-provider-inventory.md`. Strong existing controls include password hashing, JWT validation/revocation, auth rate limits, role dependencies, transaction participant checks, idempotency, outbox events, dispute evidence ownership checks and upload type/size limits. Their existence does not counteract the confirmed gaps above. No claim of penetration testing, legal compliance, certification, or production secrets scan is made.

## 7. Test/build results

- Backend `python -m pytest -v`: **109 passed, 0 failed, 0 skipped**, 1 deprecation warning; 122.78 sec.
- Backend `python -m ruff check app`: **pass**.
- Backend `python -m mypy app`: **pass**, zero issues in 69 files.
- Frontend `npm run lint`: **pass**.
- Frontend `npm run test`: **2 files, 6 tests passed**.
- Frontend `npm run build`: **pass**. Entry JS 247.52 KB raw / 79.43 KB gzip; Map route chunk 154.79 KB raw / 45.68 KB gzip. No measured initial network waterfall or Web Vitals.
- `npm run test:e2e`: **4 passed**, two specs on desktop and Pixel 5/mobile. APIs mocked; axe scope is public home only.
- API `/api/v1/openapi.json`: OpenAPI 3.1, 70 operations. Health HTTP 200 says development/demo; detailed check observed SQLite DB healthy, Redis down, worker hardcoded healthy and overall degraded.
- `npm audit --omit=dev`: **0 reported vulnerabilities** across 75 production dependencies.
- `python -m pip check`: **fail** in global interpreter due unrelated installed dependency conflicts. `pip-audit -r requirements.txt` could not resolve pinned psycopg binary 3.2.5 under Python 3.14; backend vulnerability scan is **unknown**.
- Alembic history/heads: one head. Isolated SQLite `upgrade head`: **fail** at initial migration because importing `app.core.database` eagerly creates ORM tables before the migration. PostgreSQL/PostGIS upgrade and downgrade were not run.
- Lighthouse: **not run**, executable absent. Full-route/manual accessibility, CI run state and production performance were not verified.
- Docker Compose: inspected; Docker daemon unavailable, so no PostgreSQL/PostGIS, Redis, worker or container baseline run.
- No checks were skipped by the test runners. Unavailable audits/probes above are not counted as skipped tests.

## 8. Changes made

Created documentation/evidence artifacts and appended a dated baseline correction to `PROGRESS_TRACKER.md`. User-provided `AGENTS.md` and `docs/krishilink-v4/` inputs were left as found. No product behavior was modified.

## 9. Files changed

- `docs/work/00-plan.md`
- `docs/work/00-result.md`
- `docs/work/00-capability-matrix.md`
- `docs/work/00-architecture-and-data.md`
- `docs/work/00-baseline-evidence.md`
- `docs/work/00-security-provider-inventory.md`
- `docs/work/00-frontend-sbom.cdx.json`
- `docs/work/00-backend-requirements.txt` (declared direct requirements; not a resolved/transitive SBOM)
- `docs/product/capability-register.md`
- `PROGRESS_TRACKER.md` (append-only dated correction)

## 10. Recommended decisions before Packet 01

- Confirm ordering of Packet 01 against the documented P0 security/truth blockers; do not carry fabricated data into architecture contracts.
- Decide the production and local environment contract (Python version, PostgreSQL/PostGIS, Redis, worker, storage and provider settings) and use it for a clean repeatable baseline.
- Decide canonical quantity units, money Decimal boundaries, public identity/projection and the source of contractual terms.
- Decide if payment remains tracked manually for pilot or requires a licensed provider; no real escrow is implemented.
- Assign owners and launch metrics in the capability register; decide privacy/legal review scope before collecting personal data.
- Make CI run on `abdulrehman` or select a different user-approved branch convention; current `push` trigger omits it.

## 11. Risks

- Documentation and attachment drafts overstate or contradict the executable snapshot; future work could follow stale claims.
- UI restored wholesale from `main` could reintroduce generated/fake marketplace data, obsolete API assumptions and translation defects.
- SQLite test success may conceal spatial/database/concurrency/migration errors on PostgreSQL.
- Local Python 3.14/global packages differ from CI Python 3.13 and include unrelated conflicts.
- Current tests do not establish production authorization, accessibility, performance, provider delivery, disaster recovery or regulatory compliance.
- Metrics and health output can mislead operators if treated as production readiness evidence.

## 12. External dependencies

PostgreSQL/PostGIS service; Redis; Celery worker; S3-compatible storage and malware scanning; data.gov.in API key/source availability; SMS provider credentials/approval; regulated payment provider/legal design; controlled geocoding/outlet provenance source; Python 3.13 environment for dependency audit; Lighthouse/browser profiling; GitHub CI history; privacy/legal review and field usability testing.

## Rollback

No application/schema/data changes were made. Review/revert only the ten Packet 00 documentation artifacts listed above and the appended Packet 00 paragraph in `PROGRESS_TRACKER.md`. Preserve the pre-existing user edits in `AGENTS.md` and `docs/krishilink-v4/`.

## Exact next packet

**Work Packet 01 — Architecture and domain contracts**, after the user reviews Packet 00 decisions and the required PostgreSQL/PostGIS/Redis baseline is provisioned. Packet 01 has not been started.
