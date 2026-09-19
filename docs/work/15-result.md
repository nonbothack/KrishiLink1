# Packet 15 — Production hardening and release candidate

## Status

**BLOCKED**

The user-required hard gate applies: PostgreSQL migration/concurrency, backup/
restore, load/soak and rollback cannot be claimed without execution evidence.
Docker is installed but its daemon is unavailable (`docker version` cannot
connect to `//./pipe/docker_engine`). Packet 15 therefore stops here without
starting Packet 16.

## Executive summary

Release-candidate evidence tooling and several safe fail-closed hardening fixes
were added. Production rejects SQLite, debug/demo mode, development OTP
disclosure, loopback database/Redis and wildcard CORS. Pytest creates an
isolated disposable local database rather than `backend/krishilink.db`. A
dependency-aware `/api/v1/health/ready` probe now returns 503 when DB or Redis
is unavailable. The candidate manifest records branch, SHA, dirty state,
diff/lock/artifact hashes and migration head without exposing secrets.

## Verification boundary

See `docs/release/production-readiness.md` and the individual evidence files.
Static inspection and SQLite tests are explicitly separated from unexecuted
PostgreSQL/Redis/object-storage/runtime rehearsals. External legal, VAPT,
manual accessibility and UAT evidence remains pending, but those are not the
reason for the current blocked status.

## Changes made

- fail-closed production settings and database engine;
- isolated pytest database setup;
- liveness/readiness separation;
- release candidate manifest and structural gate checker;
- release evidence envelope and blocker register.

## Required next action

Start a supported Docker daemon, provision the production-like compose stack,
then rerun migration, restore, concurrency, Redis/Celery, object storage,
load/soak, failure-drill and rollback evidence before reassessing Packet 15.
Do not begin Packet 16.

## Verification results

- `python -m pytest -q --durations=0`: **222 passed, 0 failed, 0 skipped**, exit 0. One pre-existing `pytest-asyncio` deprecation warning (`asyncio.get_event_loop_policy`). The run used a unique disposable SQLite database and did not reuse `backend/krishilink.db`.
- `python -m pytest -q tests/test_packet15_release.py`: **3 passed**.
- `python -m ruff check app tests/test_packet15_release.py`: **PASS**.
- `python -m mypy app`: **PASS**, 91 source files.
- `python -m compileall -q app alembic/versions`: **PASS**.
- `python -m alembic -c alembic.ini heads`: **PASS**, `e1f4a7b9c2d3`.
- `python -m alembic -c alembic.ini upgrade head --sql`: **BLOCKED/FAILS** at the pre-existing data-dependent Packet 03 migration `c4e83d2f1a60` because offline SQL has no result rows for its `SELECT`; no live PostgreSQL rehearsal was possible.
- `npm ci`: **BLOCKED** by local npm EACCES while fetching `@emnapi/wasi-threads` and inability to write the npm cache. No dependency install claim is made.
- `npm run lint`, `npm run test`, `npm run build`, `npm run typecheck`, `npm run format:check`: **UNAVAILABLE** after the failed clean install; local `oxlint`, `vitest`, `vite`, `tsc`, and `prettier` executables are absent.
- `python scripts/create_release_candidate_manifest.py`: **PASS**.
- `python scripts/check_release_candidate.py`: **PASS** structural evidence check.
- `git diff --check`: **PASS** (only existing LF/CRLF conversion warnings).
- `docker version`: **BLOCKED** — Docker client 29.7.2 is installed but cannot connect to `//./pipe/docker_engine` because the daemon is not running.

## Files changed

Application hardening: `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/modules/health/router.py`, `backend/conftest.py`, `backend/tests/test_packet15_release.py`.

Release evidence/tooling: `scripts/create_release_candidate_manifest.py`, `scripts/check_release_candidate.py`, `docs/release/`, `docs/work/15-plan.md`, `docs/work/15-result.md`, `PROGRESS_TRACKER.md`.

## Scope and rollback

No migration, product feature or Packet 16 work was started. The code changes
are isolated and can be reverted from the working-tree diff after review. No
commit, tag or push was created.

## Packet 15A continuation

The frontend npm environment was subsequently repaired in Packet 15A using a
temporary writable cache; see `docs/work/15a-result.md`. The original Packet 15
status remains historically accurate, while Docker infrastructure is still the
active hard blocker.
