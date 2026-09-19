# Work Packet 10 — Trade Operations result

**Status:** PASS_WITH_EXTERNAL_DEPENDENCY  
**Branch:** `abdulrehman`  
**Scope:** Packet 10 only. No commit or push.

## Executive summary

Packet 10 adds operational records to the existing trade aggregate without creating a second trade or timeline. The canonical `Transaction` and immutable accepted-terms snapshot remain authoritative; `TradeEvent` is the shared operational timeline. Payment, quality, weighment, logistics and uploaded-file records are presented as attributed participant statements unless an actual external verifier exists. Storage requests remain pending and do not reserve capacity.

The local automated acceptance suite is green. Production activation still depends on infrastructure and providers that are not configured here. No real payment movement, bank verification, assay, carrier confirmation, storage reservation, PostgreSQL/PostGIS runtime migration, or S3-compatible storage rehearsal is claimed.

## Verified behavior

### Canonical trade and timeline

- Accepted-offer trade creation persists its accepted terms snapshot, initial timeline event, audit entry and outbox event.
- Trade Room and trade-list reads are read-only. They do not synthesize a public reference, reconstruct missing legacy terms, or append a timeline event. Missing legacy terms remain unavailable; actions needing those terms fail closed.
- Payment reports, acknowledgements, quality claims, Decimal weighments, logistics statements, storage requests and evidence submissions append attributed events to the same `TradeEvent` timeline. Linked grievance opening/status/evidence actions also use that timeline and existing audit/outbox paths.
- Trade operation writes lock the canonical transaction, authorize a participant/operator, and persist the operation, event, audit/outbox rows and idempotency result in one DB transaction. SQLite tests establish local contracts, not PostgreSQL lock guarantees.

### Payment truth

- A buyer can submit a payment reference and amount as `PARTICIPANT_REPORTED`; the amount is Decimal-validated and individually capped at the immutable trade gross.
- Seller acknowledgement records a second statement. Neither buyer report nor seller acknowledgement marks a payment provider-verified, changes the trade lifecycle to paid/settled, or claims money moved.
- Legacy payment rows are surfaced as unverified legacy records, separately from current participant reports. Provider-connected and provider-verified remain false.
- Participant payment confirmation is removed from the accessible trade transition path. The UI explicitly says a reference or seller acknowledgement is not bank verification.

### Quality, weighment and evidence provenance

- Quality submissions are participant claims, not verified assays. Weighment net and discrepancy are calculated on the server with `Decimal`; the result does not mutate contracted quantity or price.
- Evidence upload is bounded (10 MiB), streams in bounded chunks, checks allowed file signatures against MIME, normalizes the filename, and computes SHA-256 server-side. Stored evidence records uploader, classification, provenance, MIME, size and timestamp. Client-supplied object keys/hashes cannot establish evidence.
- Evidence remains `PARTICIPANT_SUBMITTED`; neither an image nor a document proves the depicted quality, location, time or event.
- The object-store path was tested with a mocked S3 adapter. Real object-store authorization, lifecycle and signed-URL behavior were not externally exercised.

### Logistics, storage and grievances

- Pickup/dispatch/delivery/receipt are attributed statements; no carrier integration or independent delivery confirmation is asserted.
- Storage discovery hides unknown/unreviewed facilities from the usable list and labels demo records. Trade-linked requests are idempotent `REQUESTED` records with pending facility confirmation; no capacity, price, availability or booking is asserted.
- Trade grievances require a participant or authorized operator. Participant access to unrelated disputes is denied. Legacy evidence attachment using caller-supplied S3 keys/hashes is rejected after authorization; new evidence uses server-side upload validation.

### Frontend and accessibility

- The Trade Room exposes payment report/acknowledgement, quality statement, weighment, logistics update, storage request, evidence upload, canonical timeline and grievance entry points.
- English, Hindi and Marathi catalogues cover the Packet 10 Trade Room copy; unit tests check required keys in all three locales.
- Playwright covers the operations journey with isolated deterministic API fixtures at 360×640, 390×844, 768×1024 and 1440×900; it checks no horizontal overflow and runs axe WCAG 2.2 AA tags at 360×640 for each language. This is browser/UI verification against intercepted fixtures, not a live-backend deployment test or manual assistive-technology review.

## Migration

Added Alembic revision `d10a6f5b4c32` after `9b8c7d6e5f4a`. It adds event metadata/provenance/idempotency, payment provenance/reporter/idempotency, evidence classification/file provenance fields, storage facility provenance, and a pending-only trade storage request table. Existing uncertain payment/evidence/storage rows receive `UNKNOWN_LEGACY`; historical data is not promoted to verified evidence.

Python compilation, Alembic head/history inspection and offline PostgreSQL SQL generation/review passed. The migration was **not** executed against PostgreSQL/PostGIS because that runtime is unavailable. SQLite cannot verify PostGIS DDL or production row-lock behavior.

## Tests and verification

| Check | Result |
|---|---|
| `python -m pytest --tb=short --show-capture=no` (fresh isolated SQLite DB) | **191 passed, 0 failed, 0 skipped**, 449.38 seconds; one pytest-asyncio deprecation warning about `asyncio.get_event_loop_policy` |
| `python -m ruff check app tests/test_packet10_trade_operations.py tests/test_trade_room.py tests/test_domain_transition_contracts.py tests/test_e2e_journeys.py tests/test_integration_transactions_fsm.py` | Passed |
| `python -m mypy app` | Passed; 83 source files |
| `python -m compileall -q app alembic/versions` | Passed |
| Alembic heads/history and offline upgrade SQL review | Passed; head is `d10a6f5b4c32`; live DB upgrade unavailable |
| `npm run lint` | Passed |
| `npm run test` | **22 tests passed** across 6 files |
| `npm run build` | Passed; Vite built 1,898 modules. Dynamic public registry pages were omitted where public API/origin inputs were unavailable; no sample records were substituted. |
| `npm run check:security` | Passed; configured security headers/CSP and provider-key checks |
| `npm run check:bundle` | Passed; initial JS gzip 131.98 KiB (150 KiB budget), JS+CSS+assets 140.35 KiB (400 KiB budget) |
| `npm run test:e2e` | **20 passed**, 4.5 minutes, desktop and mobile projects; deterministic intercepted API fixtures |
| `git diff --check` | Passed; Git emitted only existing LF-to-CRLF working-copy notices |

Additional checks unavailable:

- `npm run typecheck` could not run because the repository-local TypeScript executable (`node_modules/.bin/tsc`) is absent.
- Prettier check could not run because the repository-local Prettier executable is absent; `npx` could not retrieve it in the network-restricted environment.
- PostgreSQL/PostGIS migration and lock-race rehearsal, Redis runtime, live S3-compatible storage, payment provider, assay/lab, carrier and storage operator flows remain externally unverified.

## Files changed for Packet 10

- Backend: `backend/app/models.py`; `backend/app/core/domain_contracts.py`; `backend/app/core/evidence_files.py`; `backend/app/modules/offers/router.py`; `backend/app/modules/trades/{router.py,schemas.py,service.py}`; `backend/app/modules/disputes/router.py`; `backend/app/modules/transactions/router.py`; `backend/app/modules/storage/router.py`; `backend/app/modules/markets/router.py`; `backend/app/seed.py`.
- Migration and tests: `backend/alembic/versions/d10a6f5b4c32_packet10_trade_operations.py`; `backend/tests/test_packet10_trade_operations.py`; updated trade FSM/journey tests.
- Frontend: `frontend/src/pages/TradeRoomPage.jsx`; `frontend/src/pages/GrievancesPage.jsx`; `frontend/src/lib/http.js`; `frontend/src/services/api.js`; `frontend/src/styles/app.css`; `frontend/src/utils/copy.js`; `frontend/src/utils/copy.test.js`; `frontend/e2e/critical-journeys.spec.js`.
- Evidence: `docs/work/10-plan.md`; `docs/work/10-result.md`; `docs/DECISIONS.md`; `PROGRESS_TRACKER.md`.

## Risks and deferred work

- Existing trades without immutable accepted terms cannot safely reconstruct contract facts. They remain readable with unavailable fields, and term-dependent operations reject them pending reviewed data repair.
- No real payment rail, provider settlement callback, assay/lab, weighbridge, carrier, storage operator confirmation, or production support/operations console is activated. Participant statements must not be treated as verified evidence.
- PostgreSQL concurrency, PostGIS migration execution and real S3 access-control behavior must be rehearsed before production activation. E2E browser data is isolated fixture data and does not leak to production, but does not establish a live deployment journey.
- TypeScript/Prettier checks and manual native-speaker/assistive-technology review remain outstanding.
- Packet 11 intelligence and all later packets remain out of scope.

No commit or push was made. Packet 11 was not started.
