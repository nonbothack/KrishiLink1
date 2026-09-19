# Sanitized configuration inventory

No secret values belong in this document. Production values must come from an approved environment/secret manager with rotation, revocation and access audit.

| Setting | Purpose | Secret | Absent behavior |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL/PostGIS connection | Yes | startup/connection failure; never silently use production SQLite |
| `REDIS_URL` | rate limits, broker/cache | Yes | degraded/fail-closed features as configured |
| `JWT_SECRET` | token signing | Yes | production validation fails for the development default |
| `CORS_ORIGINS` | browser origin allowlist | No | only configured origins should be accepted |
| `S3_*` | private evidence/object storage | Yes | uploads unavailable/manual review |
| `AGMARKNET_API_KEY`/`MANDI_API_KEY` | official price source | Yes | prices remain latest persisted/stale/unavailable |
| `SMS_*` | OTP/messaging provider | Yes | production OTP fails closed |
| `WEB_PUSH_VAPID_*` | opt-in Web Push | Private key yes | Web Push unavailable; in-app remains |
| `PAYMENT_PROVIDER` | future payment boundary | Usually secret | participant-reported state only |
| `ENV`, `DEBUG`, `DEMO_MODE` | environment behavior | No | production must be explicit and debug-off |
| `VITE_PUBLIC_SUPPORT_*` | approved public support contacts | No | omit rather than show placeholders |

Secret managers, TLS, database-at-rest encryption, object-store encryption, Redis auth/TLS and key rotation are deployment requirements, not configured facts of this repository.
