# Work Packet 01 — Architecture and Domain Contracts Plan

Date: 2026-09-17  
Branch: `abdulrehman`  
Scope: Architecture/domain contracts only. No commit or push; Packet 02 is out of scope.

## Verified starting point

- FastAPI routers are grouped under `backend/app/modules/`; SQLAlchemy models share one PostgreSQL/PostGIS database and `backend/app/models.py` defines the present persistence boundary.
- Existing bounded contexts are uneven: identity, lots, matching, offers, FPO, prices, trades, disputes, notifications, storage, admin and metrics have modules; standalone logistics, verification, trust, payment-provider and storage-booking modules are absent or represented only by partial tables.
- `/api/v1` routes generally return `{success,data,message,request_id}` on success. Exceptions use a separate error shape. List routes use `page`, `limit`, `total`, `pages` inconsistently; OpenAPI is available outside production.
- Internal IDs are UUIDs. Some resources add `KL-LOT-*` or `KL-TRD-*` public references, while APIs commonly expose both IDs and some use UUID path IDs.
- A transactional outbox exists and is emitted in the same database transaction in several mutation paths. The Celery worker row-locks pending events and publishes to Redis, but delivery is at-least-once in failure windows, retry is fixed at three attempts, and no general consumer deduplication contract is present.
- Trade lifecycle logic is duplicated between `/transactions/{id}/transition` and `/trades/{id}/transition`. The latter lets admin/operator bypass invalid transition checks. Dispute status updates accept arbitrary target strings. Offer transitions are checked procedurally; lot publication is direct on creation and there is no lot lifecycle endpoint. Storage booking and verification case transitions are not implemented.
- Frontend uses React 19, Vite, React Router and client-side rendering. It has an offline status banner and session refresh, but no service worker or general offline mutation queue.
- Existing HTTP adapter, provider service, database constraints, and tests will be extended only where needed to make the architecture contract precise. Packet 00A fixes are not in scope for revisit.

## Intended changes

1. Publish the bounded-context map and current module ownership, including explicit not-yet-implemented contexts.
2. Define the lifecycle graphs and transition ownership for current Lot, Offer, Trade, Grievance, and provider-attempt models; identify staged state machines without endpoints.
3. Record API envelope, pagination, public/internal ID, idempotency and versioning conventions without a breaking endpoint migration.
4. Record decisions for the transactional outbox and normalized external-provider interfaces.
5. Record rendering-stack, offline-write/conflict, and multi-tenancy ADRs.
6. Add regression tests for invalid trade and grievance transitions; close only the transition-enforcement gaps that violate the selected contracts.

## Expected files and surfaces

- Documentation: `docs/work/01-architecture-and-domain-contracts.md`, `docs/work/01-result.md`, `docs/DECISIONS.md`, `PROGRESS_TRACKER.md`.
- Tests: targeted additions to trade/dispute integration tests or a dedicated Packet 01 contract test module.
- Server changes, limited to contract enforcement: shared state graph in `backend/app/core/domain_contracts.py`; adapters in `backend/app/modules/transactions/router.py`, `backend/app/modules/trades/service.py`, `backend/app/modules/offers/router.py`, and `backend/app/modules/disputes/router.py`.
- No public endpoint redesign, no frontend redesign, no new product workflow, and no model/schema addition planned.

## Migration risk

No migration is planned. State graphs will match current persisted status vocabulary where possible. Existing duplicate transaction/trade APIs and legacy status values will be documented as compatibility debt; no data rewrite or endpoint removal is in scope.

## Verification

- Targeted trade/dispute state-transition tests, then the complete backend suite (`python -m pytest -v`) to preserve the 114-test baseline.
- `python -m ruff check app`, `python -m mypy app`.
- Frontend lint, unit tests, build, and existing E2E checks because rendering/offline decisions must describe the actual stack. No frontend implementation is planned.
- Review the final diff and ensure no Packet 02 work, commits, or pushes.
