# Work Packet 00A — Critical Baseline Remediation Result

Date: 2026-09-17  
Branch: `abdulrehman`  
Scope: Packet 00A only. No commit or push was made. Packet 01 was not started.

## Status

**PASS_WITH_EXTERNAL_DEPENDENCY** — scoped code changes and available verification are complete. The production frontend image could not be built or started because the Docker engine is not running in this environment. The local frontend production bundle and static Nginx configuration were verified separately.

## Changes

- Removed unauthenticated `GET /api/v1/storage/buckets` and `POST /api/v1/storage/presigned-url`. Dispute evidence retains participant/admin-gated access and server-generated upload keys; caller-submitted evidence keys are restricted to the current dispute namespace.
- Scoped reservation reads: farmers and FPOs see reservations on their own lots, buyers see their own reservations, admins can inspect all, and unsupported roles receive 403.
- Restricted the arbitrary SMS test relay to administrators in development. In production the path is concealed with 404.
- Removed password-reset bearer tokens from outbox payloads. The development-only response token still supports local reset testing; production delivery remains dependent on a reset-email provider/worker, which this packet does not implement.
- Replaced fabricated buyer marketplace type/crops/ratings/distance/prices with persisted BuyerProfile/User data. Buyers without a profile are not advertised; unavailable offer price and distance are null.
- Removed invented trade-room net realization, fee, transport, delivery timing, destination, and party-name fallbacks. Trade snapshot creation uses an actual accepted offer or lot asking price and returns 409 if an agreed price is absent. Existing explicit sandbox payment labeling remains, with a clear no-funds-transferred message.
- Removed inferred district-to-coordinate mapping at registration and fabricated proximity coordinates for matching/map markers. Distance is unscored when either persisted point is unavailable; map markers require stored geometry.
- Changed the frontend Docker image to a Vite production build served by Nginx, with SPA fallback and `/health`, and mapped host port 5173 to container port 8080 in Compose.
- Added `abdulrehman` as a push and pull-request CI branch target.

## Verification

Final verification was completed on 2026-09-17.

- Backend: `python -m pytest -q` — passed, 114 tests, 0 failures, 0 skips. One existing pytest-asyncio deprecation warning was emitted.
- Backend lint: `python -m ruff check app` — passed.
- Backend types: `python -m mypy app` — passed (69 source files).
- Frontend: `npm run lint` — passed; `npm run test` — 2 files / 6 tests passed; `npm run build` — passed.
- Docker: `docker compose build frontend` — unable to run because `//./pipe/docker_engine` is unavailable (Docker daemon not running). Docker image/runtime health and SPA fallback were not verified in a container.
- Compose: `docker compose config --quiet` — passed; CI workflow YAML parsed successfully.
- `git diff --check` — passed.
- Additional exploratory `python -m ruff check app tests` reported 46 existing test-tree lint issues outside the CI lint target. No repository-wide test formatting sweep was made in this packet.

## Residual blockers and risks

- Production password-reset delivery has no configured sender/consumer; production requests remain generic and do not expose reset credentials. Configure an email provider and securely deliver a short-lived reset link before treating reset as production-ready.
- S3-compatible object storage is an external dependency for dispute uploads/downloads. Existing evidence upload remains unavailable when S3 is not configured.
- The map and matching experience now shows less location data until verified coordinates are persisted. This is truthful but may reduce discovery coverage; design a consented/provenance-aware location workflow in a later packet.
- Container image build/runtime behavior awaits an available Docker daemon.
- PostgreSQL/PostGIS, Redis, live S3, SMS and production payment integrations are outside this packet and remain subject to the Packet 00 external dependencies.

## Files changed by Packet 00A

- `.github/workflows/ci.yml`
- `backend/app/modules/auth/service.py`
- `backend/app/modules/disputes/router.py`
- `backend/app/modules/markets/router.py`
- `backend/app/modules/matching/service.py`
- `backend/app/modules/notifications/router.py`
- `backend/app/modules/reservations/router.py`
- `backend/app/modules/storage/router.py`
- `backend/app/modules/trades/schemas.py`
- `backend/app/modules/trades/service.py`
- `backend/app/modules/transactions/router.py`
- `backend/app/modules/users/router.py`
- `backend/tests/test_integration_auth.py`
- `backend/tests/test_packet00a_regressions.py`
- `backend/tests/test_sms_service.py`
- `backend/tests/test_trade_room.py`
- `docker-compose.yml`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `frontend/src/pages/TradeRoomPage.jsx`
- `PROGRESS_TRACKER.md`

Pre-existing user changes in `AGENTS.md`, `docs/krishilink-v4/`, `docs/product/`, and the Packet 00 `docs/work/00-*` artifacts were preserved.

## Next decision

Review Packet 00A and confirm the later product direction for consented coordinates, buyer availability/pricing projections, production password-reset delivery, and payment/logistics terms. Packet 01 remains unstarted.
