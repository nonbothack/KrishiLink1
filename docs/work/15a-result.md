# Packet 15A — Infrastructure Rehearsal and Release Candidate Closure

## Status

**BLOCKED**

Docker Desktop is repaired and the isolated rehearsal stack is executable, but
Packet 15A acceptance still has release-critical gaps: the seeded application
concurrency race matrix and a genuine two-version rollback are not complete.
The 30-minute soak completed with qualification. Per the supplied Packet 15A rule, these gaps
keep the result `BLOCKED`; this is not `PASS_WITH_EXTERNAL_DEPENDENCY`.

## Executive evidence

- Docker Engine `29.8.0`, Docker Desktop `4.91.0`, Linux/amd64 WSL2,
  Compose plugin `5.5.1` reachable through the Docker Desktop Linux engine
  pipe.
- Isolated Compose project `krishilink_packet15` ran PostgreSQL 15.8 with
  PostGIS 3.4.3, Redis 7, Celery worker/Beat, MinIO (Quay image), FastAPI and
  nginx frontend. All containers reached healthy/running state after the
  immutable-image runtime override.
- FastAPI `/api/v1/health` and `/api/v1/health/ready` returned 200 after boot;
  production-configured disposable API boot also returned readiness 200.
- Fresh Alembic migration reached `e1f4a7b9c2d3`; a second database upgraded
  from `790546cf29fe` through Packet03's data-dependent `c4e83d2f1a60` to head.
- PostgreSQL custom-format backup restored into a clean database with matching
  63 public tables.
- Redis and PostgreSQL outage drills returned readiness 503 and recovered to
  200 after restart.
- MinIO private upload/stat/delete passed; anonymous bucket access remained
  private.
- A real PostgreSQL row-lock probe blocked a competing transaction as expected;
  full seeded offer/trade application races remain unexecuted.

## Frontend environment and runtime

- `npm ci --cache C:\Users\a\AppData\Local\Temp\krishilink-npm-cache-15a`
  passed without changing dependency versions.
- `npm run lint` passed.
- `npm run test` passed: 40 tests.
- `npm run typecheck` passed.
- `npm run build` passed: initial JS 141.80 KiB gzip; initial assets 150.63
  KiB gzip. The Docker build also passed with no API/sample-data substitution.
- `npm run test:e2e` passed: 30 browser tests.
- PWA/offline/security/bundle checks and `npm audit --audit-level=high` passed.
- `npm run format:check` remains failing on 65 existing files; no broad
  formatting rewrite was introduced.
- Container nginx `/health` and `/` returned 200 with the six configured
  security headers.

## Changes made during Packet 15A

- Added `frontend/.dockerignore` and `backend/.dockerignore` to keep local
  dependencies, test output, caches, databases and environment files out of
  build contexts.
- Made the offline/provider truth check tolerate a standalone frontend Docker
  context while retaining the backend check in repository CI when available.
- Corrected the frontend container healthcheck to use `127.0.0.1`.
- Disabled the inherited HTTP healthcheck for Celery Beat in Compose.
- Used a disposable runtime override for the rehearsal to remove bind mounts
  and Uvicorn reload; this prevents source-tree watcher errors in a release
  image. The override is not a new production dependency.

## Evidence boundaries and remaining blockers

- **Concurrency:** live PostgreSQL row-lock primitive and static lock inspection
  passed; domain-level simultaneous offer acceptance/expiry/withdrawal,
  requirement-overfill and duplicate-trade races are still missing.
- **Load/soak:** a 1,800-second, 5 RPS run completed: 8,997 requests, 8,951
  HTTP 200, 46 errors overlapping the planned outage/recreation drills, P50
  3.53 ms, P95 6.28 ms, P99 13.39 ms, and max 2,041 ms. This is qualified
  local evidence, not a clean steady-state SLO measurement.
- **Rollback:** blocked. No independently retained previous release artifact
  was available for a genuine two-version application/database/PWA rollback.
- **Container security:** image inspection found backend and frontend runtime
  users are root. This is recorded as a release-hardening gap; no risky user
  migration was made during this rehearsal.
- **Production approval:** VAPT, deployed TLS, external provider delivery,
  production observability windows, RPO/RTO, manual accessibility, legal,
  business/UAT and support sign-offs remain human/external evidence.
- Docker Scout is unavailable in the installed CLI; no vulnerability scan is
  claimed from that tool.

## Commands and results

- Docker version/info through `dockerDesktopLinuxEngine`: **PASS**.
- Isolated Compose build/up, service health, `docker compose config --quiet`:
  **PASS**.
- `alembic upgrade head` (fresh and upgrade rehearsal): **PASS**.
- PostgreSQL backup/restore and PostGIS inspection: **PASS**.
- Redis/PostgreSQL outage and recovery drills: **PASS**.
- MinIO private object-store check: **PASS**.
- Production config guardrail and disposable production API boot: **PASS**.
- `python -m pytest -q`: **222 passed, 0 failed, 0 skipped** (one existing
  pytest-asyncio deprecation warning).
- `python -m ruff check app`: **PASS**.
- `python -m mypy app`: **PASS**.
- `python -m compileall -q app alembic/versions`: **PASS**.
- `git diff --check`: **PASS** (line-ending warnings only).
- `python scripts/check_readiness.py`: **PASS**.
- `python scripts/check_release_candidate.py`: **PASS**.

## Git and scope

- Branch: `abdulrehman`.
- Working tree intentionally contains the prior Packet 00–15 changes plus the
  small Packet 15A packaging/runtime fixes; no commit, push or tag was made.
- Packet 16 was not started.

## Required next actions before closing Packet 15A

1. Seed real domain records and execute the application-level PostgreSQL race
   matrix, including accepted-offer quantity conservation.
2. Retain two independently identifiable application artifacts and execute the
   documented app/database/PWA rollback and smoke path.
3. Resolve or explicitly accept the root-runtime hardening gap, then rerun the
   security evidence review.
4. Update the release manifest and readiness documents from the final evidence.

Do not start Packet 16.

