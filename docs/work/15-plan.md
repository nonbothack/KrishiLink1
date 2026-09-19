# Packet 15 plan — Production hardening and release candidate

## Current state

Packet 14 left the branch with a clean isolated SQLite regression baseline but
without a provisioned PostgreSQL/PostGIS, Redis/Celery, object-storage,
backup/restore or load environment. Packet 15 treats those as execution gates.

## Bounded changes

1. Make production configuration fail closed for SQLite, debug/demo mode,
   development OTP disclosure, loopback dependencies and wildcard CORS.
2. Prevent ordinary pytest runs from creating or reusing the persistent
   `backend/krishilink.db` file.
3. Add a distinct dependency-aware readiness probe.
4. Add internal release-candidate manifest/check tooling and evidence documents.
5. Run every executable local check, and stop with `BLOCKED` when hard
   infrastructure rehearsals cannot be executed.

No product feature, migration, payment flow or Packet 16 work is in scope.
