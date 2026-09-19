# Exit and portability plan

The current FPO export is a standard JSON manifest with SHA-256, row counts and bounded CSV domain exports. It is authorized by the FPO owner and excludes secrets, provider credentials, raw evidence and unrelated staff/admin notes. `schema_version` allows future readers to evolve the format.

## Exit package

- PostgreSQL logical dump/snapshot performed by the deployment owner under the restore runbook.
- Business JSON/CSV exports from `/api/v1/fpo/export` and future approved owner-scoped domains.
- Private object-storage files exported with their documented media type and evidence reference, subject to authorization and retention/legal holds.
- Configuration and infrastructure inventory with secret values removed.
- Bounded audit export with actor, action, entity, time and request ID; no credentials.
- Provider contracts, source licenses and migration ownership handed over under the implementation agreement.

This is a portability design, not proof that a production customer has completed an exit. Provider-specific formats may require adapters. No proprietary lock-in or legal ownership conclusion is claimed.
