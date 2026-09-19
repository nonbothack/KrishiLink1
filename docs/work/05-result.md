# Work Packet 05 — Identity, Onboarding, Authorization and Consent

Date: 2026-09-17  
Branch: `abdulrehman`  
Overall status: **PASS_WITH_EXTERNAL_DEPENDENCY**  
Scope: Packet 05 only. No commit or push. Packet 06 was not started.

## 1. Executive summary

Packet 05 adds a canonical Indian mobile identity path, OTP sign-in/registration, server-tracked refresh-token families, browser CSRF protection, distinct verification evidence, versioned consent history, privacy-request intake, and role-specific farmer/buyer/FPO registration. Existing password accounts and authenticated domain behavior remain compatible. Phone/business/bank/organization verification is no longer represented to clients as one generic verified state.

The implementation and automated tests pass. Production activation remains gated on real SMS and email delivery, Redis, PostgreSQL/PostGIS migration rehearsal, approved legal policy text, and operating processes for verification/privacy requests. The additive migration is in Alembic history but could not be upgraded end-to-end here because an earlier migration requires PostgreSQL's PostGIS GIST index.

## 2. Identity/authentication architecture

Identity remains the `User` record; farmer, buyer and FPO profiles remain separate. Canonical phone identity is stored beside the unchanged legacy phone value. Profile and organization verification live in their own status/evidence records. Authorization continues to use backend dependencies and resource ownership checks. No organization membership model was inferred or added.

`backend/app/modules/auth/identity.py` contains the shared Indian mobile canonicalizer and OTP/phone digest primitives. It accepts valid 10-digit national forms, a leading trunk zero, and `+91` forms; it rejects unsupported country codes and invalid numbers. The database adds a nullable unique canonical identity key. Migration backfill preserves every legacy phone string, populates only unambiguous canonical values, and records collisions for manual review instead of merging accounts.

## 3. OTP implementation

`POST /api/v1/auth/otp/request` and `POST /api/v1/auth/otp/verify` support OTP login and short-lived registration tickets. Codes are cryptographically generated, stored as keyed digests, expire according to configuration, allow three verification attempts, are consumed once, and invalidate prior active challenges. Requests are generic to limit account enumeration. Phone limits use a one-hour window plus resend cooldown; route-level IP limits complement them. Challenges and tickets are not persisted as plaintext secrets.

Only development with the explicit code-exposure setting can return a code. Staging/production cannot use that provider. Production fails closed when Redis coordination or a real SMS provider is unavailable. OTP outcome audit events contain outcome metadata, not the code.

## 4. Session and refresh security

Refresh-token families and one-way current-token digests are persisted. Refresh rotates the token, replay of an old token revokes the family, logout/reset revokes managed sessions, and session expiry is enforced. A valid legacy JWT session can be adopted once if it is not revoked and its credential version still matches. Existing access tokens remain in memory in the frontend; only a limited user display identity is cached.

Browser refresh credentials remain HttpOnly cookies. Production uses `Secure` and `SameSite=Strict`; refresh/logout also require an allowed Origin and double-submit CSRF token. Bearer-only API calls do not gain unnecessary CSRF state.

## 5. Farmer onboarding

The mobile-first flow is role/name/phone → OTP → optional profile/location/preferences → required policy acknowledgements. Email and password are optional for a new OTP account; email/password login remains available for existing accounts. GPS denial or absent structured geography does not block registration. Draft state contains no password, OTP, refresh/reset token, bank detail or identity document.

## 6. Buyer onboarding

Buyer self-registration creates a buyer profile with the supplied business/contact fields and `UNVERIFIED` business status. Entered details do not claim verification. Admin review requires a named verification dimension, evidence reference, method and status. Marketplace buyer capabilities check the profile's business-verification state where defined by the current implementation. External GST/business lookup is unavailable; no checksum or format validation is reported as verification.

## 7. FPO onboarding

FPO self-registration creates an owner-linked FPO profile with `UNVERIFIED` organization status. A registration/reference number is information only and does not establish verification. FPO data remains single-owner scoped. There is no multi-user membership/representative authorization model, so cross-member access is not inferred from `role == fpo`.

## 8. Location onboarding

No fabricated State/District/Taluka or nearby-market inference was introduced. Structured geography can be used when authoritative data exists; otherwise location may remain incomplete or user-entered text. GPS is requested only after an explicit user action, must be consented to, and stores coordinates without inventing administrative IDs. Clearing coordinates withdraws the corresponding GPS consent. GPS is not returned in the general user response.

The location purpose is nearby market/price relevance and later explicitly requested logistics. It is not background tracking. Exact retention and precision policy still needs the approved privacy notice and retention schedule.

## 9. Authorization matrix

| Actor | Authentication and permitted boundary | Packet 05 result / limitation |
|---|---|---|
| Visitor | Public pages, current policy metadata, and generic OTP/register entry points | Cannot call protected user, trade, offer, transaction, dispute, storage, reservation or admin operations. |
| Farmer | Authenticated farmer routes and records owned/participated in by that user | Own profile, verification view and location controls are scoped to the current user. Existing lot/offer/trade/transaction/dispute checks remain server-side. |
| Buyer | Authenticated buyer flows, limited to its own user/profile and related records | Business status is separate; configured buyer capabilities require the dimension-specific status where enforced. No shared-organization membership exists. |
| FPO | Authenticated FPO flows, limited to the current owner's records | No access is granted to another FPO's records through role alone; multi-user member access is not implemented. |
| Admin | Existing admin-only operations | Can review dimension-specific verification with evidence; generic `/users/{id}/verify` returns 409. |
| Operator | Existing narrowly scoped operational market source/review routes | Cannot self-register as operator; admin-only mutations stay admin-only. No new operator identity workflow was added. |
| Support / reviewer | No public self-registration or new elevated support role | Dedicated least-privilege support/reviewer roles and MFA remain deferred. |

The following route families were inspected against server dependencies and object scoping: offers, transactions, trades/trade room, grievances, storage/reservations, admin/verification, market source/price operations and user/profile endpoints. Their frontend guards remain usability controls only. Packet 05 did not rewrite domain authorization unrelated to identity; the existing suite plus Packet 05 privacy-owner and admin-verification tests cover the changed boundaries. A complete enumerated role-by-route test matrix and multi-user buyer/FPO isolation tests require the membership/authorization model decision described below.

## 10. Verification-state model

Verification evidence is stored by dimension: phone, email, identity, business, GST, bank and organization. Records include status, method, reviewer/provider reference, timestamps and bounded evidence metadata. Provider adapters report unavailable when no provider is configured. Buyer/FPO profile states are separate from verification evidence. The legacy `is_verified` database flag is retained for compatibility, but the user response omits it and it is never backfilled into a new verification dimension. The retired generic admin verify route rejects writes.

No real GST, business, bank or identity verification was performed. Status values such as `VERIFIED` must be set through dimension-specific admin evidence review, not by entering a field.

## 11. Consent and policy architecture

Terms and Privacy Notice acceptance are separate versioned records; marketing is optional and defaults off. Acceptance/withdrawal history is append-only. Users can inspect consent history and withdraw marketing; GPS consent is recorded only after explicit location collection and withdrawn when coordinates are cleared. Consent IP addresses are not stored; bounded user-agent, source, version and time are retained for audit context.

Policy metadata is versioned and displayed in English, Hindi and Marathi with a prominent `DRAFT — PENDING LEGAL REVIEW` state. Production registration is blocked until approved policy versions are configured. Privacy endpoints provide owner-scoped access/correction/erasure request intake only; they do not claim fulfillment or automatic deletion. `docs/compliance-matrix.md` maps the current staged DPDP commencement based on official Gazette sources and marks unresolved legal decisions for counsel.

## 12. Recovery and sensitive account changes

Password login remains compatible; newly set/reset passwords require at least ten characters. Reset grants are one-use and stored as hashes; reset completion increments credential version and revokes sessions. Packet 00A's removal of reset secrets from persistent outbox payloads is preserved. Production email delivery is unavailable, so production password reset does not claim delivery.

Self-service phone/email factor replacement, bank-detail changes, organization ownership transfer and membership administration are not implemented in this packet. These need reauthentication and purpose-specific workflows before exposure; current profile editing does not silently rewrite canonical phone identity.

## 13. Provider boundaries

SMS has a provider boundary but no production credentials/provider was available. Email reset delivery, GST/business lookup, bank account verification and external identity verification remain unavailable. The adapters return an unavailable/pending state and do not fabricate success. Redis is required for production OTP coordination and abuse limits; a production Redis outage fails closed.

## 14. Security controls

- Server-side Indian phone normalization and unique canonical identity key; collision records preserve historical accounts.
- Keyed OTP/phone digests, one-time challenges, attempt/expiry/cooldown and generic auth responses.
- Production OTP, email recovery and rate-limit behavior fail closed when required services/providers are absent.
- Refresh rotation, replay family revocation, server-side logout/reset revocation and credential-version checks.
- HttpOnly refresh cookie, production Secure/Strict flags, Origin allowlist and double-submit CSRF on cookie-authenticated refresh/logout.
- Self-registration restricted to farmer, buyer and FPO; user-controlled role escalation is rejected.
- User-scoped privacy, consent, verification and location endpoints; audited verification/consent changes.
- Validation errors omit submitted values/context to avoid echoing secrets/PII and serialization failures.
- Precise coordinates are opt-in, purpose-bound and excluded from the general user response.

Residual production risks include absent MFA for elevated accounts, no multi-user organization policy, no privacy request fulfillment/retention operation, and no operational monitoring for live SMS abuse until Redis and provider operations are provisioned.

## 15. Accessibility and internationalization

The six-cell OTP control supports keyboard progression, backspace, paste, numeric input, accessible labels and Web OTP as progressive enhancement. Login/register copy and errors are localized in English, Hindi and Marathi. Protected-route safe redirects remain supported. Playwright includes desktop/mobile sign-in, OTP, safe redirect and axe accessibility coverage; the prior invalid autocomplete token was corrected. Full screen-reader testing, 200% scaling, reduced-motion review and native Web OTP device testing remain manual/device checks.

## 16. Migrations

Added `backend/alembic/versions/f5a71b8c2d04_identity_consent_sessions.py` after Packet 04 head `e47b91c6a2d0`. It additively introduces canonical phone/review and verification timestamps/version, buyer/FPO status fields, and auth sessions, OTP challenges, phone conflict, consent, verification evidence, reset-grant and privacy-request tables. Legacy phone values and verification flags are preserved. Downgrade refuses to discard accumulated identity/security evidence.

Migration Python compilation and Alembic head/history checks pass. Full `alembic upgrade head` was attempted on an isolated SQLite database but stops earlier at existing migration `0111b944a435_domain_core_tables.py`, which creates a PostgreSQL/PostGIS GIST index. No PostgreSQL/PostGIS service was available, so the new migration has not been applied against its production dialect.

## 17. Tests added or changed

Added `backend/tests/test_packet05_identity.py` (9 tests) covering Indian phone normalization, privileged-role and GPS-consent rejection, OTP digest/ticket/one-use behavior, refresh replay family revocation, production provider/policy fail-closed behavior, distinct consent/marketing withdrawal, FPO onboarding state, owner-scoped privacy/GPS consent, and dimension/evidence-required admin review. Updated auth regression fixtures for CSRF cookie/origin expectations. Added `frontend/src/components/OtpInput.test.jsx` and OTP sign-in Playwright coverage.

## 18. Full verification results

| Check | Result |
|---|---|
| Backend full suite: `python -m pytest -o addopts='' --tb=short` (fresh isolated SQLite) | **155 passed, 0 failed, 0 skipped**, one `pytest-asyncio` deprecation warning; 200.45 seconds. |
| Packet 05 focused: `python -m pytest tests/test_packet05_identity.py -o addopts='' -q` (fresh isolated SQLite) | **9 passed**, one same plugin deprecation warning. |
| Ruff: `python -m ruff check app tests/test_packet05_identity.py tests/test_integration_auth.py` | Passed. |
| Mypy: `python -m mypy app` from `backend/` | Passed; 79 source files. |
| Compile: `python -m compileall -q app alembic/versions/f5a71b8c2d04_identity_consent_sessions.py` | Passed. |
| Alembic head/history | Passed; `f5a71b8c2d04` is head after `e47b91c6a2d0`. |
| Frontend unit: `npm run test -- --run` | **20 passed** across 5 files. |
| Frontend lint: `npm run lint` | Passed. |
| Frontend browser: `npm run test:e2e` | **10 passed** across desktop/mobile journeys, including OTP login and safe redirect. |
| Frontend production build and provider-key scan | Passed. |
| Static security-header check | Passed; 6 matching headers/CSP directives. |
| Bundle budget | Passed; 116.89 KiB gzip combined against 400 KiB budget. |
| `npm run typecheck` | Unavailable: `tsc` executable is not installed in this checkout. |
| `npm run format:check` | Unavailable: `prettier` executable is not installed in this checkout. |
| PostgreSQL/PostGIS migration execution | Unavailable; no service, SQLite stops at pre-existing PostGIS GIST migration. |
| Redis/SMS/email/GST/bank provider runtime | Unavailable; external dependencies listed below. |
| `git diff --check` | Passed; Git printed normal LF-to-CRLF working-tree warnings. |

The first focused-test invocation used the default fallback database and failed fixture setup because the pre-existing local SQLite schema predates `crops.slug`. The focused and full test results above were rerun on new isolated SQLite files and passed. The configured mypy command was run from `backend/`; an exploratory invocation from the repository root did not load `backend/mypy.ini` and is not the project check.

## 19. Files changed

Packet 05 implementation/evidence touched:

- Backend config/database/auth models and migration: `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/models.py`, `backend/alembic/env.py`, `backend/alembic/versions/f5a71b8c2d04_identity_consent_sessions.py`, `backend/.env.example`.
- Auth/security/rate limiting: `backend/app/core/deps.py`, `errors.py`, `rate_limit.py`, `security.py`, `backend/app/modules/auth/{identity.py,otp_service.py,session_service.py,verification.py,router.py,schemas.py,service.py}`, `backend/app/modules/notifications/sms_service.py`.
- Identity/privacy/admin and truth semantics: `backend/app/main.py`, `backend/app/modules/admin/router.py`, `backend/app/modules/users/router.py`, `backend/app/modules/privacy/router.py`, `backend/app/modules/markets/router.py`, `backend/app/modules/matching/service.py`.
- Tests: `backend/tests/test_packet05_identity.py`, `backend/tests/test_integration_auth.py`.
- Frontend: `frontend/src/components/OtpInput.jsx`, `OtpInput.test.jsx`, `frontend/src/pages/LoginPage.jsx`, `RegisterPage.jsx`, `InfoPage.jsx`, `frontend/src/hooks/useAuth.jsx`, `frontend/src/lib/http.js`, `session.js`, `frontend/src/content/policies.js`, `frontend/src/utils/copy.js`, `translations.js`, `frontend/e2e/critical-journeys.spec.js`.
- Governance: `docs/DECISIONS.md`, `docs/SECURITY.md`, `docs/compliance-matrix.md`, `docs/security/threat-model.md`, `docs/work/05-plan.md`, `docs/work/05-result.md`, `PROGRESS_TRACKER.md`.

This is the Packet 05 scope list. The working tree also contains uncommitted changes from Packets 00–04 and pre-existing project work; those changes were preserved and not treated as Packet 05 edits.

## 20. Regression checks

Backend remains above the 145-test Packet 04 baseline at 155 passing tests. Frontend unit coverage is 20 (the 19-test baseline plus OTP coverage). Browser coverage is 10 cases including desktop/mobile OTP and safe redirect flows (the 8-case baseline plus Packet 05 journeys). Lint, build, provider-secret scan, headers and bundle budget pass. Packet 00A reset-secret remediation, Packet 01 lifecycle contracts, Packet 03 provenance and Packet 04 reported-price semantics remain covered by the full backend suite; no demo price data or broad product feature was added.

## 21. Deferred work

- Multi-user buyer/FPO memberships, delegated representative roles and organization ownership transfer.
- Self-service phone/email changes with step-up authentication; dedicated bank-detail workflows.
- Staff/reviewer least-privilege roles and MFA.
- Privacy request fulfillment, retention/deletion schedules and accountable privacy contact operations.
- Broader route-by-role matrix tests and cross-organization tests after membership semantics are decided.
- Full device/screen-reader/200%-text/reduced-motion accessibility review.
- Production monitoring and operational playbooks for OTP abuse/provider failure.

## 22. Risks

- Existing single-owner Buyer/FPO data cannot safely support shared company accounts or multiple representatives.
- Legacy duplicate phone collisions need a staffed resolution process before canonical login migration for those accounts.
- Production auth remains unavailable if required Redis/SMS is not provisioned; enabling the development code provider in production is blocked by environment checks.
- The additive schema has not been exercised on PostgreSQL/PostGIS and needs a backup, migration rehearsal and rollback review before rollout.
- Current privacy endpoints are intake records, not fulfillment guarantees; DRAFT policies must not be represented as approved legal terms.

## 23. External dependencies

- Production SMS provider credentials, sender/template registration and delivery verification.
- Production email delivery for reset links.
- Redis for production OTP coordination/rate limiting.
- PostgreSQL/PostGIS instance to rehearse all migrations.
- Counsel/organization-approved Terms and Privacy Notice, effective versions, purposes, retention, grievance/contact and DPDP launch mapping.
- Real business/GST, bank and identity verification providers or an approved staffed manual-review process.
- Organization decisions on elevated-user MFA, support/reviewer permissions, privacy-request operations and multi-user membership.

## 24. Git status

Branch is `abdulrehman`. Packet 05 changes and the broader Packet 00–04 working tree remain uncommitted. No commit or push was made. Temporary Packet 05 SQLite verification databases were removed; pre-existing `backend/krishilink.db` and other packet data are preserved. Packet 06 was not started.
