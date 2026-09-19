# Work Packet 07 — Buyer Core Pilot

Date: 2026-09-18  
Branch: `abdulrehman`  
Overall status: **PASS_WITH_EXTERNAL_DEPENDENCY**  
Scope: Packet 07 only. No commit or push. Packet 08 was not started.

## Executive summary

Packet 07 implements an account-scoped Buyer Core Pilot: a buyer can create a canonical procurement requirement, discover factual published supply, submit a requirement-linked offer, manage counter/accept/withdraw actions, reach the shared Trade Room, and review procurement records. The buyer dashboard presents open requirements, negotiation actions, active trades and notifications instead of fabricated KPIs.

The two critical safeguards are server-side. Buyer discovery returns a privacy-safe seller label/type, broad location and lot facts only; no farmer phone, email, full name, owner ID, exact coordinates or profile details are returned. Requirement commitment is stored as `Decimal` canonical quantity and is incremented only by accepted linked offers while the requirement, offer and lot/allocation rows are locked.

## Buyer requirements and procurement accounting

`backend/app/modules/requirements/router.py` owns buyer requirements. They use canonical crop IDs and supported crop units, retain original entered quantity/unit, normalize to quintals, and return server-calculated requested, committed and remaining amounts. Requirements are account-owned; Packet 05's single-owner buyer limitation remains in force, with no teams or shared organization authorization invented.

Requirement-linked offer creation validates the buyer-owned active requirement and locks it. Farmer acceptance, or buyer acceptance of a farmer counter, locks the requirement again and rejects a commitment that would exceed requested canonical quantity. Only an accepted offer updates `committed_quantity`; pending offers do not count. The requirement becomes `PARTIALLY_FILLED` or `FILLED` based on the server result.

## Data minimization, discovery and offers

`GET /requirements/discover/lots` is an authenticated buyer projection of published supply. It supports a buyer's selected requirement, crop and grade and explains a result descriptively. It deliberately omits farmer contact, private profile and precise-coordinate data. Buyer offer lists also no longer return a farmer full name or owner ID; they use `Farmer listing`/`FPO listing` before a trade.

Buyer counters retain immutable offer-chain history. A buyer may accept a farmer counter, but cannot accept an unrelated buyer's counter. A buyer may withdraw an eligible offer; withdrawal retains history and notifies the seller through the existing notification/outbox path. The canonical Trade Room and transaction list remain the buyer's post-acceptance record, with no fabricated payment, logistics or quality completion.

## Migration

`backend/alembic/versions/8a7d6e5f4c3b_buyer_requirements_and_offer_links.py` follows `73b4c9e10a62`. It additively adds original/canonical/committed requirement amounts, lifecycle and buyer configuration fields, plus `offers.buyer_requirement_id` and an index/foreign key. PostgreSQL static SQL was generated and reviewed. Existing requirements remain intact; new fields are nullable or defaulted safely.

## Tests and verification

| Check | Result |
|---|---|
| Packet 07 buyer contracts | **3 passed**: buyer requirement object isolation, farmer-data-minimized discovery, requirement overfill prevention, buyer counter authorization. |
| Backend full suite | **163 passed, 0 failed, 0 skipped**; one existing pytest-asyncio deprecation warning; 263.02s. |
| Ruff / mypy | Passed; mypy covers 82 app source files. |
| Frontend lint / units | Passed; **20 unit tests**. |
| Frontend production build | Passed; provider-key scan passed. |
| Bundle/security checks | Passed: 119.76 KiB initial gzip JS / 150 KiB; 127.12 KiB first-load assets / 400 KiB; six static header/CSP checks passed. |
| `git diff --check` | Passed, with normal Windows LF-to-CRLF warnings only. |
| PostgreSQL/PostGIS migration and true row-lock concurrency rehearsal | Not available locally. SQLite contract tests do not prove PostgreSQL lock semantics. |
| Browser E2E regression | Existing Packet 06 browser suite remains recorded as passing. Packet 07's new buyer routes need a browser journey against a provisioned FastAPI/PostgreSQL stack before deployment. |

## Files changed

- Backend: `backend/app/models.py`, `backend/app/main.py`, `backend/app/modules/requirements/router.py`, `backend/app/modules/offers/router.py`, `backend/app/modules/transactions/router.py`, and migration `8a7d6e5f4c3b_buyer_requirements_and_offer_links.py`.
- Tests: `backend/tests/test_packet07_buyer_core.py`.
- Frontend: `frontend/src/pages/{BuyerDashboard.jsx,BuyerRequirementsPage.jsx,BuyerDiscoverPage.jsx,OffersPage.jsx,TransactionsPage.jsx}`, `App.jsx`, `layouts/DashboardLayout.jsx`, `services/api.js`, `utils/copy.js`.
- Documentation: `docs/work/07-plan.md` and this result.

## Risks, rollback and external dependencies

- PostgreSQL/PostGIS is required before deployment to rehearse the full migration chain and concurrent acceptance locks. SQLite cannot execute the repository's earlier PostGIS GIST migration.
- Requirement quantities are protected in application transactions and tested serially. A production database stress test must prove simultaneous accepted offers cannot make `committed > requested`.
- Production SMS/Redis/payment/logistics/quality providers remain unavailable and were not simulated as successful. Landed cost is limited to real recorded components; unavailable transport/fee/payment information is stated as unavailable.
- Rollback: downgrade the Packet 07 revision only before production requirement/offer-link data is relied on; otherwise use a forward repair/snapshot because dropping columns removes procurement evidence.

## Git status and next packet

Packet 07 changes and prior packet work remain uncommitted on `abdulrehman`. No commit or push was made. Recommended next packet: **Packet 08 — FPO Core Pilot**. Packet 08 was not started.
