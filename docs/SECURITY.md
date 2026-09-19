# KrishiLink Security

## Principles (§58-59)

Secure-by-default; deny-by-default RBAC; never trust client `user_id/role/price/status`.

## Auth (§13)

- Passwords are Argon2/bcrypt hashed, never plaintext. New and reset passwords require at least 10 characters; existing accounts keep their established credential until changed.
- Access tokens expire after 15 minutes. Refresh tokens expire after 7 days and rotate against a persisted session-family digest; reuse revokes the family. Password reset increments a credential version and revokes sessions.
- Browser refresh secrets use `HttpOnly`, `SameSite=Strict` cookies and `Secure` in production, with Origin allowlisting and a double-submit CSRF token. This assumes the deployed frontend/API are same-site; verify the real host topology.
- Indian mobile OTPs are short-lived, one-use and attempt-limited; codes and challenge phone keys are HMAC-digested. Production delivery and sensitive rate limits fail closed without configured SMS and Redis. Development code disclosure needs an explicit setting.
- Password recovery grants are one-use digests. Production email recovery is unavailable until a delivery provider is configured; bearer secrets are not stored in outbox events.
- The browser keeps access tokens in memory and stores only the minimum display identity needed for reload. `localStorage` is not the authentication source of truth.
- Admin/staff second-factor authentication is not implemented and is a production decision/blocker for privileged accounts.

## RBAC (§14)

Roles: `FARMER, FPO, BUYER, ADMIN, OPERATOR`. Self-registration permits only farmer, buyer and FPO; admin/operator provisioning stays privileged. Use `require_role(...)` on protected routes and enforce object ownership. Buyer/FPO profiles currently have one owner and no member model.

The legacy `is_verified` fields are not proof of phone, email, identity, business, GST, bank or organization verification. Use dimension-specific `verification_records`; an admin review must include an evidence reference. Phone/email verification uses dedicated flows.

## Validation & Injection

- Pydantic v2 (backend) + Zod (frontend) on every endpoint; `extra=forbid`, `strip_whitespace`, regex for phone/email
- SQLAlchemy ORM parameterized — no raw string interpolation; SAST via Semgrep
- XSS: CSP, `X-Content-Type-Options: nosniff`, sanitize rich text

## Headers & CORS

- `Strict-Transport-Security`, `X-Frame-Options: DENY`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`
- CORS allowlist from env `CORS_ORIGINS`, credentials only for same-site, no `*`

## Rate Limiting

- Redis sliding window: login 5/min, ingestion 10/min, general 100/min per IP+user

## Secrets

- Never commit `.env`; `.env.example` only; config via `pydantic-settings` validated at startup; secret scanning (gitleaks, GitHub secret scanning); dependency/container scanning (Dependabot, Trivy)

## Data Minimization (§11)

- No Aadhaar unless legal requirement; if needed, encrypted at rest (pgcrypto `pgp_sym_encrypt`, key in vault), never in API responses; audit access to sensitive fields
- GPS is captured only after a user action and explicit consent, omitted from profile responses, and removable. Administrative geography is not inferred from coordinates.
- Terms and privacy acknowledgements are versioned separately from optional marketing. Marketing is off by default; withdrawal preserves the evidence history. Policy drafts are not approved for production use.

## Audit Logging (§59)

- Every login/logout, profile change, lot publish, offer accept/counter, transaction transition, payment, dispute, admin action → `audit_logs(actor, action, entity, entity_id, before, after, request_id, timestamp)` — immutable, append-only.

## Observability Safety

- Never log passwords, tokens, financial PAN, PII; structured logs redacted; request_id correlation.

## Feature Flags (§60)

`system_configurations` guards `VOICE_INPUT, QR_TRACEABILITY, LIVE_PRICE_INGESTION, DEMAND_HEATMAP, REAL_PAYMENT, WHATSAPP_ALERTS, NEW_MATCHING_RULES` — disabled by default, admin-toggle with audit.
