# Work Packet 13 — Admin, Fraud, Support and Operations

## Status

**PASS_WITH_EXTERNAL_DEPENDENCY**

## 1. Executive summary

Packet 13 is complete locally. The internal surface now uses explicit server-side staff permissions, short-lived action-scoped step-up grants, safe support context, evidence-backed versioned fraud cases, operational queues, provider/configuration inspection, audited feature flags, incident records and notification-only retry. No generic replay endpoint was introduced. Fraud records remain review signals and do not automatically punish users or rewrite trade/payment/FPO evidence.

## 2. Staff permission model

`backend/app/modules/admin/permissions.py` maps `admin`, `operator`, `support`, `reviewer` and `fraud_reviewer` to explicit capabilities. Public registration remains limited to farmer/buyer/FPO (`backend/app/modules/auth/schemas.py`). Staff creation is admin-only, step-up protected and audited at `POST /api/v1/admin/staff`.

## 3. Elevated auth / sessions

`POST /api/v1/admin/step-up` verifies the staff password and issues a ten-minute, one-use grant bound to the staff user, current session ID and action family. Sensitive flag, restriction, fraud decision, session-revocation, staff-management and outbox retry actions consume the grant. Session revocation increments the target token version without exposing tokens.

## 4. Admin console and operations

`/admin/operations` is lazy-loaded and available only to internal roles. It renders partial/degraded data safely and exposes factual system, review, case, failed-delivery and provider configuration state. It does not claim provider health from imports or expose secrets.

## 5. Verification / source review

The existing dimension-specific `VerificationRecord` workflow is retained. Queue projection lists pending dimensions without raw evidence. Existing admin verification compatibility remains intact; reviewer-role access is limited to assigned business/GST/organization dimensions. Market/source review continues through the Packet 03/04 permissioned routes; no direct official-price editing was added.

## 6. Fraud / risk

`FraudCase` and `record_signal()` preserve subject, signal, rule ID/version, severity, evidence references and lifecycle. The unique subject/signal/rule-version key makes repeated signals idempotent. Decisions are reasoned and audited; restrictions are explicit (`ACTIVE`, `RESTRICTED`, `SUSPENDED`) with optional expiry. There is no opaque score, automatic conviction, account deletion, payment hold, trade cancellation or evidence rewrite.

## 7. Support

`SupportCase` and append-only `SupportNote` provide general support distinct from trade disputes. `GET /admin/support/users/{id}/context` returns a bounded projection with masked phone and no email value, OTP/token, bank/identity documents, exact GPS, raw dispute evidence or provider secrets. Support can create cases, add internal notes and revoke sessions with step-up; it cannot approve verification, mutate trades/payments or set passwords.

## 8. Privacy requests

`GET /admin/privacy/queue` exposes only the existing request lifecycle records for authorized privacy reviewers. It does not auto-export, auto-erase, or claim legal completion.

## 9. Outbox / dead-letter / replay

`GET /admin/outbox` is paginated and metadata-only. `POST /admin/outbox/{id}/retry` accepts only pending/failed canonical notification events, requires outbox permission plus step-up, records an audit entry, and rejects completed events and trade/payment/domain events. Provider delivery remains deduplicated by existing notification/Web Push receipts.

## 10. Provider/job health

`GET /admin/provider-health` distinguishes configuration state for SMS and Web Push and does not return credentials, endpoints or keys. Existing price ingestion, alert, notification and Web Push Celery contracts remain the scheduler; Packet 13 adds no second scheduler. Redis/Celery runtime remains externally unverified.

## 11. Feature flags / kill switches

`SystemConfiguration` keys under `flag.*` are server-side and changes require admin permission, step-up and an audit record containing actor, old/new state and reason. Existing backend feature gates remain authoritative; in-app records/history are not deleted when an external provider is disabled.

## 12. Incidents / runbooks / audit

`IncidentRecord` supports open/list/resolve with severity, affected capability, summary, runbook reference and audit. `docs/runbooks/packet13-operations.md` covers price ingestion, Redis/outbox, SMS/OTP, Web Push, evidence, payment-provider and account-takeover failures. Existing `/admin/audit` now supports bounded action/entity/correlation filters and safe projections.

## 13. Security and privacy verification

Passed focused tests for role separation, public buyer denial, support projection minimization, fraud idempotency/no-conviction state, step-up requirement and replay rejection. Audit actor/request IDs are recorded for new privileged mutations. Browser cookie/CSRF and existing IDOR protections remain in force.

## 14. Accessibility / responsive review

The internal operations page reuses Packet 02 primitives, has headings/status text and was checked by Axe in desktop and mobile Playwright projects. Existing full E2E covers 360/390/768/1440 public and role journeys; the Packet 13 route passed at desktop and mobile project sizes. A desktop-first queue/table expansion remains future work.

## 15. Performance

The staff page is lazy-loaded. It makes bounded independent requests with `Promise.allSettled`; one provider/queue failure does not blank the whole page. Public initial bundle remained within the 150 KiB gzip budget (141.80 KiB in the bundle check).

## 16. Tests and verification

- Backend: `python -m pytest -q --disable-warnings -rA` — **215 passed, 0 failed, 0 skipped** on a clean local SQLite schema; the suite includes six Packet 13 tests.
- Focused: `python -m pytest -q tests/test_packet13_operations.py` — **6 passed**.
- Ruff: `python -m ruff check app` — pass.
- Mypy: `python -m mypy app` — pass, 91 source files.
- Compile: `python -m compileall -q app alembic/versions` — pass.
- Frontend lint — pass.
- Frontend unit: **40 passed**.
- Frontend build/SEO/offline/provider-secret checks — pass; no credentials embedded; no synthetic public data.
- Frontend browser: **30 passed** (28 existing + 2 Packet 13 staff-console projects).
- PWA check, security headers/CSP check, bundle budget and `git diff --check` — pass (diff check reports only normal CRLF warnings).
- TypeScript/Prettier executables were not available and were not claimed.

## 17. Migrations

Added `backend/alembic/versions/e1f4a7b9c2d3_packet13_operations.py`, one head after `d73f2c91a604`. It is additive: staff grants, fraud cases, support cases/notes, incidents, account restriction fields, outbox operational metadata and the expanded internal-role check. `python -m alembic heads`, history and PostgreSQL offline SQL generation pass. Live PostgreSQL/PostGIS upgrade and row-lock rehearsal remain unavailable.

## 18. Files changed

Implementation: `backend/app/models.py`, `backend/app/core/deps.py`, `backend/app/modules/admin/router.py`, `backend/app/modules/admin/permissions.py`, `backend/app/modules/admin/fraud.py`, `backend/alembic/versions/e1f4a7b9c2d3_packet13_operations.py`.

Frontend: `frontend/src/lib/session.js`, `frontend/src/services/api.js`, `frontend/src/App.jsx`, `frontend/src/layouts/DashboardLayout.jsx`, `frontend/src/pages/AdminOperationsPage.jsx`, `frontend/e2e/packet13-operations.spec.js`.

Evidence/governance: `docs/work/13-plan.md`, this file, `docs/DECISIONS.md`, `docs/security/threat-model.md`, `docs/runbooks/packet13-operations.md`, `PROGRESS_TRACKER.md`.

## 19. Deferred work / risks

Real MFA/SSO, PostgreSQL lock/concurrency rehearsal, Redis/Celery worker execution, provider delivery, formal SLA/workforce management, full staff dimension assignment administration, and legally approved privacy export/erasure fulfillment remain deferred. The existing admin verification endpoint retains its prior admin-compatible route and therefore should receive a production step-up rollout before unrestricted live use. Temporary restrictions are persisted and audited, but mutation gates across every existing domain write should be expanded in a later security hardening pass.

## 20. External dependencies

PostgreSQL/PostGIS, Redis/Celery, real SMS/Web Push credentials and delivery, and production MFA/provider contracts were unavailable locally. These are why the result is `PASS_WITH_EXTERNAL_DEPENDENCY`; no provider success was fabricated.

## 21. Git status

No commit or push was performed. The working tree contains the existing Packet 00–12A changes plus the Packet 13 files listed above. Packet 14 was not started.
