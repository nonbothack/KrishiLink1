# PostgreSQL concurrency rehearsal — Packet 15

**Status: PARTIAL**

A disposable PostgreSQL 15.8/PostGIS 3.4.3 rehearsal is running successfully.
A two-connection psycopg probe held a row with `SELECT ... FOR UPDATE` and
confirmed a competing transaction was blocked (`LockNotAvailable` at a 500ms
lock timeout). Static inspection confirms the offer, lot, requirement, FPO,
trade and outbox paths use the expected row locks/`SKIP LOCKED` clauses.

The seeded domain-level simultaneous offer-accept, expiry, withdrawal,
requirement-overfill and duplicate-trade race matrix was not executed. See
`evidence/concurrency-rehearsal.md`; no application race claim is made.
