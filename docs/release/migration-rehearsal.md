# Migration rehearsal — Packet 15

**Status: BLOCKED**

The current Alembic head is recorded in the release-candidate manifest. A live
fresh PostgreSQL/PostGIS upgrade, old-schema upgrade, data-dependent geography
migration execution, downgrade/forward-repair rehearsal, and PostgreSQL SQL
review could not be run because the Docker daemon was unavailable. Existing
offline SQL limitations around the data-dependent Packet 03 migration remain
documented in Packet 08/14 evidence. SQLite compatibility tests are not a
substitute for PostgreSQL migration evidence.
