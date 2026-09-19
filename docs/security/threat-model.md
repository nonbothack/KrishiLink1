# Packet 05 identity and consent threat model

**Scope:** Authentication, onboarding, consent, verification, browser sessions and user location. This is an engineering threat model, not a penetration-test report. Tests cover selected application paths; they do not establish production security.

## Assets and trust boundaries

- Account identity: phone, email, password hash, role, profile ownership and verification evidence.
- Authentication material: OTPs, registration tickets, access tokens, refresh tokens and password-reset grants.
- Consent and privacy evidence: accepted policy versions, withdrawals, privacy-request records and audit events.
- User location: optional location text, exact GPS coordinates, coordinate source and accuracy.
- Trust boundaries: browser to API, API to database/Redis, API to SMS/email/verification providers, and user-owned organization profiles to member or administrator operations.

## Threats and implemented controls

| Threat | Control in this packet | Residual risk / evidence needed |
|---|---|---|
| Phone formatting creates duplicate identities | Strict Indian mobile normalization and unique nullable E.164 key; conflict migration preserves and flags ambiguous legacy accounts. | Run migration against a production-like database and resolve collisions manually before OTP login is enabled. |
| OTP guessing, replay, enumeration or leakage | Generic request/error text; six-digit cryptographic random code; HMAC at rest; short expiry; one use; three attempts; phone cooldown/hourly limit; IP rate limit; no code in audit/outbox. New-account ticket expires after 15 minutes. | SMS interception/SIM swap remains possible. Provider fraud controls and staff MFA are not included. Validate Redis atomic limits under concurrency. |
| SMS provider demo path leaks codes | Production OTP adapter bypasses demo behavior and fails closed if provider is unconfigured or delivery fails. Code disclosure is gated to development plus an explicit setting. | Real SMS delivery, template/DLT/compliance policy and callback behavior require configured provider verification. |
| Refresh token theft or replay | Server stores only SHA-256 refresh digest, rotates on refresh, serializes by session row lock, and revokes family on prior-token reuse. Password reset increments token version and revokes sessions. | PostgreSQL row-lock behavior and concurrent replay must be tested with the deployment database. Access tokens remain bearer credentials until short expiry or revocation check. |
| Cross-site browser session action | Strict SameSite refresh cookie, HttpOnly refresh secret, Secure in production, Origin allowlist, double-submit CSRF cookie/header; missing CSRF is rejected on refresh/logout. | Validate configured public origins, TLS termination and proxy header trust. Native clients use bearer tokens and need their own secure storage. |
| Privilege escalation by self-selection | Registration schema accepts only farmer, buyer and FPO; privileged roles require administrative provisioning. Existing route dependencies remain in place. | Audit all protected routes separately; Packet 05 does not redesign every domain authorization boundary. Staff accounts still lack a second factor. |
| Generic verification claim misleads users | Separate verification dimensions; old generic `is_verified` is not mapped to evidence; absent provider adapters return `UNAVAILABLE`; buyer discovery reads business status. | Legacy response surfaces outside the touched routes may still use generic flags. Search and verify before exposing more badges. |
| Consent withdrawal deletes evidence or is ignored | Versioned consent rows preserve acceptance and withdrawal times; marketing defaults off; location opt-in/clear is recorded; APIs scope history to current user. | Downstream campaigns and location consumers must honor withdrawal; current request endpoints only record intake and do not fulfill rights. |
| Location collected without informed action or disclosed in profile | GPS requested only on explicit click; API requires consent and India-bounded coordinates; no coordinate-derived admin geography; profile response omits coordinates; user can clear. | Other internal services may use stored coordinates. Define retention, backup deletion, staff access and user-facing purpose before launch. |
| Validation errors disclose passwords, OTP or PII | Global request-validation handler omits submitted input/context and emits only location/type/plain message. | Review exception, access and provider logs; this fix does not sanitize every existing log statement. |
| Migration destroys prior identity/evidence | Additive migration leaves raw phones and legacy verification flag untouched; unique conflicts require review; downgrade refuses to drop nonempty evidence tables. | Production backup, PostgreSQL/PostGIS rehearsal, rollback/forward-repair plan and operational downtime window remain required. |

## Production gates

Production registration currently fails closed until Terms and Privacy Notice are approved. Production OTP also requires a configured delivery provider and Redis-backed abuse controls. Before enabling either gate, run the migrations and focused auth suite against PostgreSQL/PostGIS and Redis, validate cookie/origin settings behind the actual proxy, obtain counsel approval for policy text and retention, and exercise operational recovery and account-conflict procedures. No external provider or production deployment was exercised in this packet.
# Packet 13 operations controls

- Staff roles map to explicit server-side permissions; marketplace registration cannot create internal roles.
- Sensitive staff actions require a short-lived, one-action, session-bound password reauthentication grant.
- Support context is a safe projection. OTPs, tokens, bank/identity documents, exact GPS and raw provider secrets are excluded.
- Fraud cases are versioned evidence signals for human review. They do not establish guilt or automatically rewrite trades, payments, ledgers or evidence.
- Manual replay is intentionally typed to failed/pending notification delivery. Completed events and payment/trade/domain mutations cannot be replayed from the console.
- Feature flag changes, support lookups, restrictions, verification decisions and retries create immutable audit records with request IDs.
