# Packet 15 known blockers and resolved gates

## Resolved Packet 15B engineering gates

1. **RESOLVED — application-level PostgreSQL concurrency matrix.** Seeded
   lot, requirement, offer, expiry, FPO, allocation, outbox, Web Push and
   Packet 13 case races passed on isolated PostgreSQL. See
   `evidence/concurrency-rehearsal.md`.
2. **RESOLVED — stale duplicate acceptance.** Locked offer reload now refreshes
   the ORM identity-map state before transition validation.
3. **RESOLVED — genuine two-version rollback.** RC_A and RC_B image/PWA
   artifacts were retained and exercised A→B→A→B with smoke after each switch.
4. **RESOLVED — clean steady-state soak.** The 30-minute 5 RPS run recorded
   8,997/8,997 HTTP 200 and zero errors.
5. **RESOLVED — root runtime gap.** RC_B runs backend, worker and Beat as
   UID 100 `app`, nginx as UID 101 `nginx`; effective/permitted/ambient
   capabilities were zero in local inspection.

## Remaining external or human dependencies

6. **EXTERNAL/HUMAN — VAPT, legal/privacy, manual accessibility, native-speaker
   review and business/UAT sign-offs.** These remain required for production
   approval and are not claimed complete here.
7. **EXTERNAL/HUMAN — deployed infrastructure evidence.** Production TLS,
   managed PostgreSQL/PostGIS, production Redis, observability windows,
   RPO/RTO and real provider delivery still require the target environment and
   named operators.
8. **KNOWN LIMITATION — Docker Scout unavailable.** The installed Docker CLI
   has no Scout command; no vulnerability result is inferred.
9. **KNOWN LIMITATION — Prettier debt.** The global format check still reports
   65 pre-existing files. Packet 15B did not perform an unrelated formatting
   rewrite.

Historical Packet 15A blocker statements remain in `docs/work/15a-result.md`
and the earlier evidence files for auditability.
