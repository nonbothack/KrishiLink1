# Database backup and restore — Packet 15

**Status: PASS — isolated rehearsal**

A PostgreSQL custom-format dump was created from the disposable `krishilink`
database, restored into a clean `krishilink_restore_15a` database with
`pg_restore --exit-on-error`, and checked. Source and restored public table
counts both equalled `63`; the restore database and dump were then removed.

This proves the mechanical procedure only. Production RPO/RTO, encrypted
off-host retention and populated business-data recovery remain unverified.
