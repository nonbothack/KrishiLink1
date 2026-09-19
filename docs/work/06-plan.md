# Work Packet 06 — Farmer Core Pilot Plan

## Verified starting point

Packets 00–05 are treated as repository truth. The authenticated farmer dashboard currently lists lots and four shortcuts, but does not summarize actual prices, offers, trades, or notifications. The sell flow uses the canonical crop registry and a review step, but sends client-converted floats, requires district and location text, uses fixed grade choices, and creates a new idempotency key on each page mount. Farmer offers can be accepted or rejected, but the UI has no counter flow or expiry display. The Trade Room and grievance workflow already exist and will be reconnected rather than replaced.

The backend already has canonical Crop `valid_units`/`default_unit`, user-scoped lot creation idempotency, official price observations, verified outlet coordinates, offer/transaction state machines, transactional notifications/outbox, and participant checks in the Trade Room. Material gaps include float-based lot/offer arithmetic, no authoritative crop-unit validation during lot creation, public unscoped lot listing/details, permissive offer actions, missing expiry validation and incomplete idempotency scoping on acceptance, and buyer PII returned in farmer offer projections.

## Decisions

- Farmer-facing dashboard data will use separate authenticated, user-scoped lots, offers, transactions, notifications, official prices and verified markets resources. One subsystem error will not erase other loaded sections. No generated match score or sample market/offer/transaction value will enter a production farmer surface.
- The first view will prioritize greeting/location context, a latest reported crop price only when available, an action queue from persisted state, and Sell. Location is never inferred; browser GPS is requested only after a farmer action.
- Lot writes will accept a canonical crop ID plus raw entered quantity/unit, validate crop-supported units server-side, and normalize to quintals with Decimal. Existing quantity/unit remain the canonical value for compatibility; additive nullable original quantity/unit columns preserve new farmer entries. Asking price is always INR/quintal, regardless of entered quantity unit. A new `UNSPECIFIED` grade value represents unknown grade without claiming A/B/C. Precision beyond two canonical quantity decimals is rejected. No price is inferred as a contractual ask.
- Existing lot grades are A/B/C; retain these domain values but explain selection plainly. Existing lots with qualified outstanding offers will not allow material edits. Withdrawals are explicit, retain the record, and are blocked after an accepted offer; outstanding pending offers are cancelled with notifications/outbox events in the same transaction.
- Offer acceptance is farmer-only for the farmer flow, owner-checked, expiry-checked against server time, serialized by lot/offer locks, remaining-allocation checked, Decimal-calculated, and user-scoped/idempotent. Buyer-facing history is retained; counter creates a new child offer and does not mutate the parent terms. Counter/reject/accept use existing notification/outbox paths without direct background provider dispatch.
- Farmer offer projection exposes business display name and verification status only, never buyer phone/email. Terms not present in the contract remain unavailable.
- The five mobile farmer destinations are Home, Prices, Sell, Offers and More. More opens transaction records, notifications, support and help. Existing desktop navigation remains role-specific.
- Existing local draft convenience remains user-scoped; idempotency key stays with one saved draft/submission attempt and clears only after success or logout/account switch. No offline submission/sync is introduced.
- No new production analytics provider, forecasting, trust score, advanced matching, payment movement, logistics, or unsupported support contact is introduced.

## Files and contracts expected to change

- Backend: `backend/app/models.py`; new additive Alembic migration after `f5a71b8c2d04`; `backend/app/modules/lots/router.py`; `backend/app/modules/offers/router.py`; price/market and notification routes only if needed for safe authenticated projections.
- Frontend: farmer dashboard, sell/lot, offers, transaction/Trade Room display, role navigation, language copy, authored styles and API helpers; add a compact farmer More destination if the existing routes cannot provide the five-tab model.
- Documentation: this plan and `docs/work/06-result.md`; update `PROGRESS_TRACKER.md` with Packet 06 result.

## Migration risk and rollback

One additive migration adds nullable `original_quantity NUMERIC(12,3)` and `original_unit TEXT` to lots. Existing rows remain readable and are not reinterpreted. New writes keep canonical quintal quantity/unit in existing columns. Downgrade drops only these two new columns; it does not touch lots or users. PostgreSQL/PostGIS migration rehearsal depends on database availability.

## Verification plan

- Extend backend contract tests for crop-supported units, Decimal normalization/precision/bounds, owner-only lot access/edit/withdraw, no edit with pending offers, expiry and participant-safe accept/reject/counter/history, buyer PII minimization, allocations, duplicate accept/publish and persisted farmer journey. Keep concurrency assertions within what the test database supports and state row-lock limits honestly.
- Extend frontend tests for partial failures, empty price context, user-scoped draft/idempotency persistence, honest gross labels, expiry-disabled actions, accept confirmation, five-tab navigation, translations, and farmer journey rendering.
- Run the required full backend pytest, Ruff app, mypy app, frontend lint/unit/build/E2E, security/bundle scripts, and `git diff --check`; record unavailable infrastructure/tools and any failures without hiding them.
- Inspect core screens at 360×640, 390×844, 768×1024 and 1440×900 if browser automation is available; test English, Hindi and Marathi. Report action counts separately for first-time and returning farmer journeys, without presenting local assumptions as user-tested outcomes.
