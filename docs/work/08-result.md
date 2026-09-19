# Packet 08 / 08A — FPO Core Pilot acceptance result

## Status

**PASS_WITH_EXTERNAL_DEPENDENCY**

Packet 08A closes the local test, browser, roster import, localization, and conservation evidence gaps. The persisted chain remains `member → intake receipt → pool contribution → FPO pool → marketplace lot → offer/trade → member trade allocation`. PostgreSQL/PostGIS migration and real row-lock race behavior remain unverified because no local PostgreSQL service is available.

## Executive summary

The FPO pilot provides member roster and secure CSV import, append-only intake receipts, Decimal canonical quantities, contribution-backed pools, published FPO lots, offer negotiation, canonical Trade Room links, traceable member allocations, and projected (not paid) allocation records. Direct FPO lot creation and editing outside the pool ledger are rejected. Published pool composition and contributed receipt values cannot be silently changed. The generic withdrawal path marks the linked pool withdrawn and preserves its evidence.

Evidence is separated below into deterministic local API/UI tests, static production-path inspection, and externally unverified infrastructure behavior. No Packet 09 work was started; there was no commit or push.

## Intake integrity and correction auditability

`backend/app/modules/fpo/service.py` computes net quantity as gross minus tare, rejects tare greater than gross and non-positive net, validates the crop-supported unit, retains entered gross/tare/net and original unit, and stores canonical quintals using `Decimal`/`NUMERIC`. A 1,000 kg receipt produces exactly 10.000 qtl. Repeating the same intake with its idempotency key returns the original receipt.

Unpooled corrections void rather than overwrite the original receipt, create a linked replacement, and persist actor, reason, timestamp, and before/after audit evidence. A receipt with any contribution cannot be corrected destructively.

Evidence: `test_intake_calculates_net_canonical_quantity_and_is_idempotent`, `test_intake_rejects_invalid_net_and_unsupported_unit`, `test_append_only_correction_records_actor_reason_timestamp_and_original`, and the published-pool correction check in `test_published_pool_contribution_cannot_be_added_removed_or_corrected`.

## Pool and contribution conservation

Contribution values are server-validated and the pool total is derived from persisted contributions, not trusted from the request. A multi-member/multi-receipt pool of 4 + 7 + 9 qtl persists exactly 20.000 qtl. A 1,000 kg receipt contributes 6.000 qtl to one pool and 2.000 qtl to another, leaving 2.000 qtl. A further 3.000 qtl is rejected; specifically, attempting 5.000 qtl after the 6.000 qtl contribution is rejected.

After publication, add/remove contribution APIs and correction of a contributed intake fail. The generic FPO lot PATCH path also fails, so crop/quantity/price/grade/availability cannot silently diverge from published terms. Generic FPO lot creation returns 409; an untraced legacy FPO lot cannot be accepted into a trade because the allocator fails closed when its pool trace is missing.

FPO withdrawal cancels the published lot and pending offers through existing notification/outbox paths, marks the pool `WITHDRAWN`, and retains the pool contribution ledger. An accepted trade prevents casual withdrawal.

Evidence: `test_intake_conserves_across_multiple_pools_and_rejects_overallocation`, `test_pool_total_is_server_sum_for_multiple_members_and_receipts`, `test_published_pool_contribution_cannot_be_added_removed_or_corrected`, `test_fpo_lot_withdrawal_preserves_pool_ledger_and_marks_pool_withdrawn`, and `test_fpo_direct_lot_cannot_bypass_pools_and_untraced_legacy_lot_cannot_be_sold`.

## Partial sales, multi-member trace, and allocations

For contributions A=40, B=35, C=25 qtl, repeated accepted trades of 40 then 35 qtl create allocations once per trade and leave 25 qtl. A subsequent 30 qtl acceptance is rejected. After each accepted trade, allocation sums, original contributions, lot quantity, active reservations, and remaining availability reconcile. Accepted trade quantities never exceed pool quantity.

Allocation traces join each accepted transaction to its pool, exact contribution, original intake receipt, and member. A 10 qtl trade from three members produces three allocation rows and resolves to all three members and their respective receipts. Trade allocations have `PROJECTED` status; settlement/payment is not asserted.

Quantity residuals are rounded down to canonical 0.001 qtl first, then distributed in stable contribution-ID order without exceeding remaining contribution balances. Monetary allocation is separate: member gross amounts use Decimal currency precision and the final allocation receives the exact paise residual. The rounding fixture verifies 0.334/0.333/0.333 qtl sum to 1.000 qtl and ₹0.33/₹0.33/₹0.35 sum to the exact ₹1.01 gross.

Evidence: `test_partial_sales_reconcile_pro_rata_and_reject_excess`, `test_proportional_quantity_and_money_rounding_are_separate_and_exact`, and `test_accept_retry_is_idempotent_and_trace_crosses_pool_contribution_receipt_member`.

## Offer idempotency, interoperability, authorization, and privacy

The same accepted-offer request with the same idempotency key returns the same transaction ID. It creates one transaction and one set of member allocations. The existing acceptance path locks the marketplace lot, offer, active reservations, and linked buyer requirement; FPO allocation additionally locks the linked pool, contributions, and prior allocations. This is static/code-path evidence only; SQLite does not establish PostgreSQL row-lock or race behavior.

The API contract journey publishes a pool-backed FPO lot, creates a buyer offer, lets the FPO counter, and has the buyer accept the counter. Buyer and FPO then resolve the same canonical Trade Room and identical terms; the FPO trace resolves the member chain. No role-specific duplicate trade is created.

Cross-FPO API tests prove a second FPO cannot read or edit a member, read/correct an intake, use the intake in a pool, read the owner’s pools, publish the owner’s pool, accept the owner’s offer, or read the owner’s trade trace. FPO role alone is not treated as ownership; owner/profile scoping is enforced.

Buyer discovery returns marketplace-appropriate FPO seller identity and lot facts while excluding member names/phones, intake receipt IDs, contribution data, member IDs, and allocation values. FPO trace remains owner-scoped.

Evidence: `test_accept_retry_is_idempotent_and_trace_crosses_pool_contribution_receipt_member`, `test_buyer_fpo_counter_acceptance_shares_one_trade_room_and_trace`, `test_cross_fpo_member_intake_pool_offer_and_trace_access_is_denied`, and `test_buyer_fpo_projection_has_group_identity_but_no_member_or_ledger_data`.

## Member roster and CSV import

No adequate CSV import existed, so the minimum preview-and-import workflow was implemented. It is scoped to the authenticated FPO owner, does not create or link platform `User` accounts, and requires an explicit import after preview. The member schema has no `user_id` linkage, and an attempted CSV `fpo_id` assignment is rejected. Repeated submission with the same idempotency key is safe. Validation bounds input to 1 MiB and 1,000 rows and handles strict UTF-8, malformed CSV, duplicate/missing headers, row-level invalid phones, canonical duplicate phones, duplicate member codes, and control characters. Phone values are normalized only when valid; omitted village/district remain unknown. Rejected rows do not block accepted preview rows. There is no CSV export endpoint, so spreadsheet formula execution/export injection is not applicable; imported strings are stored as data and never executed.

Evidence: `test_csv_preview_import_is_scoped_validated_idempotent_and_creates_no_users`, `test_csv_import_rejects_invalid_encoding_and_oversized_body`, and `test_csv_import_bounds_rows_and_rejects_malformed_invalid_phone_and_controls`. Browser coverage selects a CSV file, previews it, and explicitly imports its accepted row.

## Browser, responsive, localization, and accessibility review

`frontend/e2e/critical-journeys.spec.js` includes a deterministic FPO browser journey covering dashboard, member creation, CSV preview/import, intake, receipt, pool, publish, offer, counter, Trade Room, trace, and projected allocation. The buyer acceptance of the counter is modeled in the isolated browser fixture; the API contract test separately executes buyer-authenticated acceptance against persisted test data and confirms the shared canonical Trade Room.

The FPO browser test checks horizontal overflow at 360×640, 390×844, 768×1024, and 1440×900 in English, Hindi, and Marathi. Axe WCAG 2.2 AA-tag checks pass for the FPO dashboard, allocation view, and Trade Room. Core forms have labels and keyboard submission is exercised. Basic validation and request-failure messages preserve entered form state and expose a retry path. This is automated browser/accessibility evidence; manual screen-reader and native-speaker review remain follow-ups.

FPO user-facing dashboard, member, intake, receipt, correction, pool, contribution, publish, offer, trace, projected allocation, loading/empty/error, and CSV import copy uses the established translation catalog in English, Hindi, and Marathi (`frontend/src/utils/copy.js`).

## Migration and production-path verification

Revision `9b8c7d6e5f4a` remains the single Alembic head. Python compile succeeds. Packet 08 range SQL generation (`8a7d6e5f4c3b:9b8c7d6e5f4a`) succeeds and was inspected: FPO intake/pool/contribution/allocation quantities use `NUMERIC(12,3)`; member code has an FPO-scoped unique constraint. The migration is additive; downgrade drops only Packet 08 tables.

The full-chain offline `alembic upgrade head --sql` command remains unsupported by the pre-existing data-dependent Packet 03 migration `c4e83d2f1a60`: it executes a SELECT and expects result rows during offline SQL generation. No code in Packet 03 was changed for this packet. A live PostgreSQL/PostGIS upgrade and downgrade rehearsal could not run: localhost ports 5432 and 5435 were unavailable. Therefore production migration compatibility and row-lock races remain external verification items; SQLite was used only for deterministic functional tests.

## Full verification

- Isolated backend full suite: **180 passed, 0 failed, 0 skipped in 367.81 seconds** (`python -m pytest -v --tb=short --durations=0`; shell stopwatch 372.5 seconds). One warning: pytest-asyncio calls deprecated `asyncio.get_event_loop_policy`, scheduled for removal in Python 3.16. No tests were skipped.
- Packet 08/FPO targeted API and dashboard suite: **21 passed** (17 Packet 08 contract tests and 4 dashboard tests).
- Backend: `python -m ruff check app`, `python -m mypy app`, and `python -m compileall -q app alembic/versions` pass.
- Frontend: `npm run lint` passes; `npm run test` passes **20 tests**; `npm run build` and provider-key scan pass. FPO dashboard JS is 2.97 KiB gzip; initial JS is 80.23 KiB gzip.
- Static production checks: `npm run check:security` verifies 6 matching security headers and baseline CSP directives; `npm run check:bundle` passes (122.24 KiB initial JS gzip / 150 KiB budget; 129.61 KiB initial JS + CSS + static assets / 400 KiB budget).
- Browser: `npm run test:e2e` — **16 passed** in 1.9 minutes across desktop/mobile. The FPO browser journey uses deterministic isolated fixtures; the persisted API integration journey separately exercises buyer-authenticated counter acceptance.
- `git diff --check` passes; Git emits only line-ending normalization warnings for existing LF files on Windows.
- `npm run typecheck` and `npm run format:check` were attempted earlier in the packet and cannot run because repository-local `tsc` and `prettier` executables are not installed. No claim is made for those checks.
- The full-chain offline Alembic SQL command fails at the existing data-dependent Packet 03 migration as described above; the Packet 08 migration-range SQL command passes.

## Files changed in Packet 08A closure

- `backend/app/modules/lots/router.py` — prohibit FPO generic lot create/edit; synchronize withdrawal with the pool ledger.
- `backend/app/modules/fpo/service.py` — fail closed if an FPO-owned legacy/untraced lot reaches acceptance/allocation.
- `backend/tests/test_packet08_fpo_core.py` — add direct-lot bypass and withdrawal regression tests; retain the full Packet 08 conservation/security/import contracts, including rejection of a forged CSV FPO owner column.
- `backend/tests/test_e2e_journeys.py` — replace the obsolete FPO generic-lot scenario with the persisted intake → pool → publish journey.
- `frontend/src/utils/copy.js` — translate the withdrawn-pool state.
- `docs/work/08-result.md`, `PROGRESS_TRACKER.md`, and `docs/DECISIONS.md` — acceptance evidence and closure decisions.

## Remaining risks and external dependencies

- Provision PostgreSQL/PostGIS and rehearse the full migration chain, downgrade safety, and concurrent pool/lot/offer acceptance races against PostgreSQL. SQLite tests are not concurrency proof.
- The data-dependent Packet 03 migration prevents full offline SQL generation; a live database run is required to validate it.
- FPO staff membership/multi-user authorization remains deferred; current owner scoping is single-account.
- Provider-based payments/settlement, payout execution, legal operating policy, and manual usability/native-language review remain outside this packet. Allocation values remain projected gross only.
- TypeScript and Prettier checks remain unavailable because binaries are absent.

No Packet 09 work was started. No commit or push was made.
