# PostgreSQL migration evidence

**Status: PASS — isolated PostgreSQL rehearsal.**

- Fresh `alembic upgrade head` completed against PostgreSQL 15.8/PostGIS 3.4.3
  and reached `e1f4a7b9c2d3`.
- A second clean database upgraded from `790546cf29fe` through the
  data-dependent Packet 03 revision `c4e83d2f1a60` and all later revisions to
  `e1f4a7b9c2d3`; both the base and head commands exited 0.
- The application readiness probe returned 200 against the migrated database.

This is a disposable rehearsal, not a production migration window or rollback
approval.
