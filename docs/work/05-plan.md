# Work Packet 05 — Identity, onboarding, authorization and consent plan

Date: 2026-09-17  
Branch: `abdulrehman`  
Scope: Packet 05 only. Preserve Packets 00–04 and the current working tree; no commit or push.

## Verified starting point

- `User` is the authentication identity and stores one legacy `is_verified` boolean; Farmer, Buyer and FPO profiles are separate tables, but organization profiles are currently one-user-owned and there is no multi-user organization membership model.
- `backend/app/modules/auth/service.py` accepts raw ten-digit phone strings, password registration, password login and JWT refresh tokens. `User.phone` is unique but formatting variants can bypass that uniqueness. Registration roles are already limited to farmer/buyer/FPO by Pydantic.
- Refresh JWTs have a `sid`, but refresh reissues a token with the same `sid` without tracking the prior token. Revocation is Redis/node-local plus a session-revoked audit event. Browser refresh credentials use an HTTP-only cookie (`SameSite=Lax`); access tokens remain in memory. There is origin checking, but no explicit CSRF token.
- OTP endpoints and OTP persistence do not exist. SMS adapters exist, but their demo mode logs message bodies; the OTP implementation must never invoke that path in production or persist/log a code.
- Registration currently requires a password, state/district/location and one combined consent checkbox. It persists a `registration-draft` in sessionStorage. `InfoPage` renders generic placeholder terms/privacy text. There is no consent history, verification evidence, or privacy-request workflow.
- Packet 03 geography tables/endpoints exist but are intentionally empty pending an authoritative LGD source. Location text can remain optional/unverified. GPS must only be requested by a user click, without reverse-geocoding guesses.
- Packet 00A removed reset secrets from the outbox payload. Production email/SMS/verification providers are not configured. Existing password accounts and current role-protected domain routes must remain usable.

## Intended changes

1. Add one strict server-side Indian mobile normalizer. Store a canonical E.164 key beside the legacy phone field; backfill only unambiguous legacy numbers and flag collisions for manual review without merging accounts.
2. Add HMAC-hashed, short-lived, one-time OTP challenges and keyed phone digests, generic request/verification errors, 3-attempt and resend/phone/IP limits, a provider boundary, and an explicitly development-only code disclosure switch. OTP login creates a session; verified new phones receive a short-lived registration ticket.
3. Require OTP registration in production; retain a legacy password-registration path only in the development environment for existing test/demo flows. Keep password login; make password optional on new OTP registrations and strengthen new/reset password minimum length.
4. Persist refresh sessions by family and current refresh-token hash. Rotate on each refresh, detect reused/old tokens and revoke the family. Migrate legacy JWT sessions on their first refresh without invalidating them. Keep session IDs on access tokens so logout/reset can revoke server-side.
5. Use `SameSite=Strict`, Secure in production, and a double-submit CSRF cookie/header on browser cookie refresh/logout. Preserve in-memory access tokens and stop storing unnecessary contact/location data in the browser session cache.
6. Add versioned consent records (terms/privacy acknowledgements separate from optional marketing), append-only acceptance/withdrawal history for marketing and exact GPS, a read/withdraw API, and a privacy-request intake foundation. New production registrations stay unavailable while policy text remains explicitly draft pending legal review.
7. Add distinct verification evidence records and explicit phone/email timestamps. Do not backfill legacy `is_verified` into any verification dimension. Create Buyer/FPO profiles during OTP onboarding; their organization verification remains `UNVERIFIED` until evidence-backed review. Keep current owner-only organization scope and document missing membership support.
8. Provide OTP-first login and a short role/name/phone → OTP → optional profile/location/consent registration journey. Add accessible six-digit OTP controls, Web OTP as progressive enhancement, structured geography selection when data exists, optional manual location, and a click-only GPS path. GPS denial must not block account creation.
9. Replace placeholder policy-status sections with versioned English/Hindi/Marathi policy documents clearly marked `DRAFT — PENDING LEGAL REVIEW`; add a DPDP commencement matrix with official Gazette sources and explicitly unresolved counsel decisions.
10. Add a security threat model and tests for phone canonicalization/collisions, OTP lifecycle/provider absence/no-secret persistence, registration roles/consent, refresh rotation/replay/logout, authorization boundaries, verification truth, consent history/withdrawal, location fallback, translations, OTP accessibility, and safe redirect compatibility.

## Files, tables and endpoints expected to change

- Backend: `models.py`; auth schemas/service/router; user/location and privacy/consent routers; security/dependency helpers; rate-limit and SMS-provider adapter; settings/env examples; one Alembic migration after Packet 04.
- New persistence: `auth_sessions`, `otp_challenges`, `phone_identity_conflicts`, `consent_records`, `verification_records`, `password_reset_grants`, `privacy_requests`; additive user/profile verification and phone/location columns.
- New API: `/api/v1/auth/otp/request`, `/api/v1/auth/otp/verify`, versioned current policy and consent read/withdraw endpoints, authenticated privacy-request endpoints, and explicit user-location update. Preserve existing `/register`, `/login`, `/refresh`, `/logout`, `/forgot-password`, `/reset-password` compatibility.
- Frontend: `useAuth`, session/http helpers, Login/Register/Info pages, translation copy, shared OTP component and focused tests/E2E coverage.
- Governance: `docs/DECISIONS.md`, `PROGRESS_TRACKER.md`, `docs/compliance-matrix.md`, `docs/security/threat-model.md`, this plan, and `docs/work/05-result.md`.

## Migration and rollback risk

The migration is additive. Legacy `users.phone` values are never rewritten; normalized conflict-free values populate a unique nullable canonical column. Multiple legacy rows mapping to one canonical number are preserved, flagged, and listed for review. The generic legacy verification boolean is left unchanged and is not promoted into phone/business/bank/email evidence. Downgrade must refuse to discard any OTP, session, verification, consent, reset, or privacy-request records. PostgreSQL/PostGIS verification may remain unavailable; test schema creation and migration compilation/history locally.

## Verification plan

Run all existing backend tests (Packet 04 baseline: 145), Ruff on application plus Packet 05 test files, mypy, frontend lint/unit/build/E2E, TypeScript/Prettier if installed, migration compile/history/smoke where supported, `git diff --check`, and targeted secret-scrub assertions. Preserve any unrelated pre-existing Ruff findings in the test tree. Record unavailable services/providers as external dependencies rather than successes.

## Risks / constraints

- No SMS credentials/provider approval, email reset delivery, GST/business lookup, bank verification, lawyer-approved policy text, authoritative LGD rows, PostgreSQL/PostGIS, or Redis runtime are available in this checkout.
- Password recovery remains truthful/unavailable in production until an email delivery provider exists; Packet 00A outbox secret removal stays intact.
- Multi-user buyer/FPO membership is not present and will not be inferred from role. Existing organization resources remain creator-owned until a separately modeled membership workflow exists.
- Exact GPS and user-provided location remain separate from administrative geography; no coordinate-derived State/District/Taluka is invented.
