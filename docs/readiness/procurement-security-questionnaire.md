# Procurement security questionnaire (evidence-backed template)

| Question | Answer/status | Evidence |
|---|---|---|
| Authentication and authorization | Implemented server-side; privileged MFA remains unresolved | `docs/SECURITY.md`, Packet 05/13 results |
| Encryption | TLS/password/token controls documented; database/object encryption depends on deployment | configuration/security docs |
| Logging/audit | request IDs, AuditLog and staff audit records | admin router, threat model |
| Backup/DR | design and restore procedure documented; live drill pending | backup architecture/runbook |
| Incident response | role-based process and Packet 13 records | incident-process, Packet 13 runbook |
| Accessibility | automated evidence and manual plan; no certification | accessibility matrix |
| Open standards/portability | JSON/CSV FPO export with manifest/checksum | `/api/v1/fpo/export`, exit plan |
| Data residency | deployment decision required | deployment architecture |
| Subprocessors | inventory exists; contracts/regions require approval | provider inventory |
| VAPT/certification | external dependency; not performed/claimed | VAPT checklist |

This table must be completed with deployment-specific contacts, regions and contracts by procurement/security leadership.
