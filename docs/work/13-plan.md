# Work Packet 13 — Admin, Fraud, Support and Operations

## Repository truth before implementation

The checkout is on `abdulrehman` with the Packet 00–12A working-tree changes present. The backend had one broad `admin` role guard, a canonical `AuditLog`, `OutboxEvent`, dimension-specific `VerificationRecord`, `PrivacyRequest`, grievance/trade evidence and Web Push delivery records. It did not have explicit support/reviewer/fraud permissions, an action-scoped reauthentication grant, persisted fraud review cases, general support cases/notes, or safe operational replay controls.

## Packet 13 decisions

1. Internal access is role-to-permission mapped server-side. Public registration accepts only farmer, buyer and FPO roles; staff accounts are created through an admin-only audited workflow.
2. Sensitive staff actions use a password reauthentication grant bound to the staff account, current session family and one action family. Grants expire after ten minutes and are single-use.
3. Fraud is a deterministic, versioned review signal. A case records evidence references, rule/version and lifecycle; it never proves wrongdoing or automatically deletes, cancels, withholds or rewrites domain history.
4. Support uses a scoped context projection and append-only internal notes. It does not expose OTPs, bank/identity documents, exact GPS or unrestricted impersonation, and it cannot mutate payments, trades or verification.
5. Manual retry is only exposed for pending/failed canonical notification delivery events. Completed events and domain/payment/trade commands are never replayable from a generic endpoint.
6. Feature flags are server-side `SystemConfiguration` records and changes are audited. Provider status is reported as configuration evidence, not optimistic health.

## Planned verification

Focused authorization, step-up, fraud idempotency, support projection, replay safety, provider redaction, feature-flag audit and migration/compile checks will be added. Existing Packet 00–12A suites remain the regression gate. PostgreSQL/Redis/Celery and real provider delivery remain external runtime dependencies where unavailable.
