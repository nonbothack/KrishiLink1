# Application-security assurance matrix

Engineering evidence is not a VAPT or certification. Residual external verification is explicit.

| Control | Evidence | Status |
|---|---|---|
| Password/OTP/session security | `backend/app/core/security.py`, auth/session tests, threat model | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED |
| Server-side RBAC/object authorization | route dependencies and packet authorization tests | IMPLEMENTED_AND_TESTED |
| IDOR/BOLA | ownership checks across lots/offers/trades/FPO routes | IMPLEMENTED_AND_TESTED |
| CSRF/CORS/rate limiting | cookie/origin checks, rate limiter, configuration | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED |
| Input/schema validation | Pydantic schemas, strict CSV import, global validation handler | IMPLEMENTED_AND_TESTED |
| Upload/evidence access | evidence metadata and signed-access checks | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED |
| SSRF/webhooks | provider boundaries and host allowlists where implemented | PARTIAL |
| Secrets/cryptography | secret settings, hashed credentials, frontend secret scan | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED |
| Audit/logging/error handling | AuditLog, request IDs, redacted validation errors | IMPLEMENTED_AND_TESTED |
| PWA/service worker | offline safety and safe push-route tests | IMPLEMENTED_AND_TESTED |
| Staff/admin least privilege | Packet 13 permissions and step-up grants | IMPLEMENTED_NOT_EXTERNALLY_VERIFIED |
| Replay/idempotency | idempotency keys and safe outbox-only retry | IMPLEMENTED_AND_TESTED |
| VAPT | No independent assessment in repository | EXTERNAL_DEPENDENCY |

See [vapt-checklist.md](vapt-checklist.md) for environment and retest preparation.
