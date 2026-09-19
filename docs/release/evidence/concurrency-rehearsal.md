# Packet 15B application concurrency rehearsal

**Status: PASS — isolated PostgreSQL application harness**

The focused harness in `scripts/packet15b_postgres_races.py` ran against a fresh database `krishilink_packet15b` on the real PostGIS/PostgreSQL service, with independent SQLAlchemy sessions and synchronized worker barriers. It called the existing offer, FPO, notification, fraud-review and outbox paths; it did not use SQLite for the assertions. Raw result JSON is retained in `packet15b-race-output.json` (credentials are deliberately omitted).

| Rehearsal | Result | Invariant |
|---|---|---|
| Lot over-allocation | PASS | One of two 8-qtl accepts won a 10-qtl lot; one transaction and 8 qtl reserved |
| Requirement overfill | PASS | Concurrent 8-qtl accepts against a 10-qtl requirement left committed quantity at 8 qtl |
| Accept vs withdraw | PASS | One terminal transition won; no duplicate trade |
| Accept vs counter | PASS | Counter and accept serialized; original offer did not produce two trades |
| Expired offer | PASS | Both accepts rejected by server expiry; zero transaction |
| Duplicate acceptance/idempotency | PASS | Repeated key returned the original response; one transaction and one idempotency row |
| FPO intake contribution | PASS | Competing 6-qtl pool contributions against one 10-qtl receipt left 6 qtl contributed |
| FPO pool sale | PASS | Concurrent accepts serialized; one trade and one allocation set |
| Allocation rounding | PASS | 1.000 qtl and ₹101.00 reconciled exactly using Decimal and deterministic residual handling |
| Outbox multi-worker claim | PASS | PostgreSQL `FOR UPDATE SKIP LOCKED` allowed exactly one claimant |
| Web Push delivery | PASS | One notification/device delivery row and one attempt under concurrent delivery |
| Packet 13 fraud decision | PASS | Row lock allowed one terminal decision; the loser received 409 |

The first run exposed a stale SQLAlchemy identity-map defect in concurrent duplicate acceptance. The locked offer reload now uses `populate_existing()`; the rerun passed and is the accepted evidence. PostgreSQL isolation and row locking are verified here. This is not a production-sized race load or a substitute for a multi-node rehearsal.
