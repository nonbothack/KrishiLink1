# Work Packet 06 — Farmer Core Pilot

Date: 2026-09-18  
Branch: `abdulrehman`  
Overall status: **PASS_WITH_EXTERNAL_DEPENDENCY**  
Scope: Packet 06 only. No commit or push. Packet 07 was not started.

## 1. Executive summary

Packet 06 delivers the authenticated Farmer Core Pilot. A farmer can sign in, see truthful price and location context, publish a protected lot, manage it, compare genuine offers, counter/decline/accept safely, open the linked Trade Room, inspect records and notifications, and reach the existing grievance/support path. The farmer dashboard is action-led rather than a feature directory.

The complete application test suite passes in an isolated SQLite test database and the browser suite passes with deterministic browser fixtures. Production PostgreSQL/PostGIS was unavailable locally, so the additive migration and real database lock behavior require a PostgreSQL rehearsal before deployment. No payment movement, forecast, trust scoring, logistics marketplace, storage redesign, or Packet 07 work was added.

## 2. Farmer dashboard and first viewport

`frontend/src/pages/FarmerDashboard.jsx` loads lots, offers, prices, markets, transactions and notifications independently, so one failed resource does not replace the whole dashboard with synthetic content. It shows the signed-in farmer, explicit profile location context, a current official reported price only when present, clear freshness/source/date/unit, real urgent actions, and the primary **Sell produce** action. GPS is requested only after the farmer chooses it; absent location remains absent.

Nearby comparison is shown only for valid comparable units, fresh official observations and verified coordinates. When that evidence is missing, the screen says comparison is unavailable rather than calculating a distance, buyer price or opportunity. A screenshot inspection at 360x640 confirmed the greeting/context, price/source and Sell action appear before the bottom navigation without horizontal scrolling.

## 3. Crop preferences, lot builder and unit/money integrity

Crop preferences and last successful lot values are convenience metadata, scoped to the authenticated browser user. They use canonical crop IDs from Packet 03; the UI does not carry a duplicate production crop catalogue. New farmers select a canonical crop and make meaningful quantity/price choices before review. Returning farmers with valid prior data can publish in three actions: **Sell → Review → Publish**. The first-time tested path is five actions: **Sell → select crop → enter quantity → Review → Publish**. These are measured UI paths, not user-study claims.

The server validates crop-supported units, precision and canonical quintal quantity in `backend/app/modules/lots/router.py` and `backend/app/modules/lots/units.py`. It uses `Decimal`, preserves the entered quantity/unit beside the canonical value, and returns a server-calculated quote. The official rate is context only; it never becomes an asking price without confirmation. Review calls gross value **Indicative gross**. The warning threshold for an implausible entered price is configured as a Decimal percentage and is advisory only when a comparable official observation exists.

## 4. Lots, offers, Trade Room and records

`FarmerLotsPage.jsx` provides user-scoped lot list/detail, guarded edits and explicit withdrawal. Material edits are rejected when pending offers would be silently changed. Withdrawal keeps history, cancels eligible pending offers, writes notifications/outbox events and cannot casually withdraw an accepted trade.

`OffersPage.jsx` groups offers by lot, shows only persisted buyer/business identity and verification dimensions, uses server values for quantity/price/gross, displays expiry, and provides a confirmation dialog before acceptance. Counters create immutable child offers rather than mutating negotiation history. The backend owner-checks, expiry-checks, locks offer/lot/allocation rows, calculates in Decimal and scopes idempotency to prevent duplicate acceptance/trades. Farmer views do not expose buyer phone or email.

Acceptance routes directly to the existing Trade Room. The farmer sees agreed terms, reference, lifecycle/timeline and only truthful payment/quality/logistics status. Where the legacy trade aggregate has no real provider state, the UI reports payment/status unavailable rather than a fabricated completion. Transactions, notifications and grievance support are reachable from the five-destination farmer navigation: Home, Prices, Sell, Offers and More.

## 5. Accessibility, i18n, responsive review and performance

New farmer copy uses the existing English, Hindi and Marathi translation structure. Browser tests cover the farmer flow at 360x640, 390x844, 768x1024 and 1440x900, including all three locales for viewport/overflow and core dashboard checks. The critical journey uses keyboard interaction for offer acceptance and Axe checks for dashboard, lot/offer, Trade Room and primary public/accessibility surfaces. The views use visible status text, native dialog focus behavior and large primary touch controls; no heavy chart, map or animation dependency was eagerly introduced.

The production build remains within its budget: 118.33 KiB initial gzip JavaScript against 150 KiB and 125.70 KiB initial JavaScript/CSS/static assets against 400 KiB. The price-key scan and static security-header/CSP checks pass.

## 6. Security and concurrency

- Farmer lot reads, edits and withdrawal are owner-scoped; cross-account requests are rejected.
- Offer acceptance checks farmer ownership, expiry, current state, remaining quantity and unit compatibility on the server.
- Duplicate lot publish and accept requests use scoped idempotency; duplicate accept cannot create an additional trade/allocation.
- Counter history is immutable; expired, declined and withdrawn offers are not actionable.
- Trade Room and notification links retain participant/owner authorization; buyer PII is minimized in farmer projections.
- The full suite and Packet 06 tests cover owner isolation, unit manipulation rejection, expiry/decline rejection, withdrawal history and duplicate-accept behavior. SQL row locks are present in the production implementation, but concurrent PostgreSQL execution remains unverified because PostgreSQL was unavailable.

## 7. Migration

`backend/alembic/versions/73b4c9e10a62_farmer_lot_original_units.py` follows Packet 05 head `f5a71b8c2d04`. It additively adds nullable `original_quantity NUMERIC(12,3)` and `original_unit`, and permits `UNSPECIFIED` where grade is unknown. Existing lots keep their canonical fields and are not reinterpreted. The downgrade drops only the two additive input columns and restores the former grade constraint.

Alembic head/history and generated PostgreSQL SQL pass. The generated SQL contains the expected two `ALTER TABLE ... ADD COLUMN` statements and grade constraint update. A fresh SQLite `alembic upgrade head` fails before Packet 06 at existing migration `0111b944a435`, which creates a PostgreSQL/PostGIS GIST index; this is not a Packet 06 migration regression.

## 8. Tests and verification

| Check | Result |
|---|---|
| Backend full suite: `DATABASE_URL=sqlite:///.../packet06-audit-final.db python -m pytest -q -o addopts='' --tb=short` | **160 passed, 0 failed, 0 skipped**; one existing `pytest-asyncio` deprecation warning; 236.76s. |
| Packet 06 contracts: `python -m pytest tests/test_packet06_farmer_core.py -q` | **5 passed**. |
| Ruff: `python -m ruff check app` | Passed. |
| Mypy: `python -m mypy app` | Passed; 80 source files. |
| Alembic head/history | Passed; `73b4c9e10a62` is head. |
| PostgreSQL static migration SQL | Passed; reviewed expected Packet 06 DDL. |
| Frontend lint | Passed. |
| Frontend units: `npm run test` | **20 passed** across 5 files. |
| Frontend build and price-secret scan | Passed. |
| Bundle budget | Passed: 118.33 KiB gzip JS / 150 KiB; 125.70 KiB total / 400 KiB. |
| Static security headers/CSP | Passed; 6 checks. |
| Browser suite: Playwright direct runner with managed Vite preview | **14 passed** across desktop/mobile. The repository `test:e2e` wrapper leaves an orphan child in this Windows environment; the same configured Playwright suite was rerun successfully against the managed server. |
| `git diff --check` | Passed; Git only emitted normal LF-to-CRLF warnings. |
| PostgreSQL/PostGIS migration and concurrency rehearsal | Not run: local port 5435 is unavailable. |
| Redis/SMS/approved support/payment provider runtime | Not available; no synthetic success was used. |
| Frontend `npm run typecheck` / `npm run format:check` | Not run: TypeScript and Prettier binaries are absent from this checkout despite package declarations. |

## 9. Files changed

- Backend domain changes: `backend/app/models.py`, `backend/app/core/config.py`, `backend/app/core/idempotency.py`, `backend/app/modules/lots/{router.py,service.py,units.py}`, `backend/app/modules/offers/router.py`, `backend/app/modules/transactions/router.py`, `backend/app/modules/trades/{schemas.py,service.py}`.
- Migration and tests: `backend/alembic/versions/73b4c9e10a62_farmer_lot_original_units.py`, `backend/tests/test_packet06_farmer_core.py`, `backend/tests/test_integration_lots.py`, `backend/tests/test_earnings_calculator.py`.
- Farmer frontend: `frontend/src/pages/{FarmerDashboard.jsx,SellPage.jsx,FarmerLotsPage.jsx,OffersPage.jsx,FarmerMorePage.jsx,TransactionsPage.jsx,TradeRoomPage.jsx,GrievancesPage.jsx}`, `frontend/src/{App.jsx,layouts/DashboardLayout.jsx,services/api.js,hooks/useAuth.jsx,utils/copy.js,styles/app.css}`, and `frontend/e2e/critical-journeys.spec.js`.
- Evidence: `docs/work/06-plan.md`, this result, and `PROGRESS_TRACKER.md`.

This is the Packet 06 scope list. The wider working tree includes preserved, uncommitted work from Packets 00–05; it was not collapsed into this packet or committed.

## 10. Regressions checked and deferred work

The 155-test Packet 05 baseline rose to 160 passing backend tests. The 20 frontend unit and 10 earlier browser-test baselines are preserved; browser coverage is now 14. Packet 00A security fixes, Packet 01 lifecycle controls, Packet 03 canonical crop/provenance and Packet 04 official-price semantics remain in the full suite.

Deferred to later packets: buyer redesign (07), FPO redesign (08), public homepage (09), provider-backed payment movement, logistics/storage/quality redesign, forecasts, price alerts, trust scoring, net-realisation ranking, WhatsApp/IVR, PWA/offline sync and broad admin expansion.

## 11. Risks and external dependencies

- A PostgreSQL/PostGIS database is required to rehearse the complete migration chain and real `FOR UPDATE` race cases. SQLite cannot execute the pre-existing PostGIS GIST migration.
- Redis and real SMS/provider services are required for production auth/outbox operation; approved support contact/policy operations remain organizational dependencies.
- Payment movement and settlement integrations are intentionally not implemented; the UI must remain honest until contracted providers and legal/operational controls exist.
- Browser E2E uses isolated deterministic API fixtures. Backend integration tests use persisted SQLite data. A deployment rehearsal should run the same journey against the actual FastAPI/PostgreSQL stack before release.

## 12. Git status and recommended next packet

Branch is `abdulrehman`. Packet 06 and prior packet changes remain uncommitted. No commit or push was made. Temporary SQLite verification databases and logs created for this audit were removed after recording the results.

Recommended next packet: **Packet 07 — Buyer Redesign**, after PostgreSQL/PostGIS migration and concurrency rehearsal is available. Packet 07 was not started.
