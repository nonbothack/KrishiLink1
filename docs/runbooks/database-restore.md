# Database restore runbook

This procedure is a controlled operational guide. Use an approved snapshot/backup and keep credentials out of tickets and logs.

1. Declare maintenance/degraded state, assign incident commander and record request/correlation ID.
2. Confirm target environment, backup timestamp, checksum, encryption key availability and legal-hold requirements. Stop writes or place the API in maintenance mode.
3. Restore PostgreSQL/PostGIS into an isolated recovery instance. Verify extensions, timezone, roles and connection settings.
4. Run the repository Alembic upgrade to the intended head; do not blindly downgrade migrations whose packet result records destructive or data-dependent limitations.
5. Run smoke checks: health, authentication/session boundary, price provenance, lot/offer/trade reads, FPO conservation/trace, audit write and outbox state.
6. Compare row counts/checksums for critical tables and inspect failed migrations before redirecting traffic.
7. Re-enable workers and providers in a controlled order, drain/reconcile outbox work, then remove maintenance state.
8. If validation fails, keep the recovery instance isolated, restore the last known-good snapshot or use a forward repair, and escalate. Record recovery time and data loss against the target; do not claim the target was met without a drill.

Packet 14 did not execute this against PostgreSQL. The live rehearsal remains an external/Packet 15 dependency.
