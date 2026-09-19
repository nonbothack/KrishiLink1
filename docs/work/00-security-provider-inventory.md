# Packet 00 — Security and provider inventory

Snapshot findings; this is a code/config audit, not a penetration test. Prioritize these before real users, money, sensitive documents, or production data.

## Critical / high production blockers

1. **Unauthenticated S3 bucket listing and arbitrary presigning.** `backend/app/modules/storage/router.py` has no `Depends(get_current_user)` on `GET /storage/buckets` or `POST /storage/presigned-url`. The latter accepts arbitrary `key` and `expiration` and generates a download URL using the service account. If S3 is configured, an unauthenticated caller may enumerate bucket names/timestamps and request signed reads for known keys. Require auth, verify object ownership/purpose, restrict key namespace/expiry, and remove bucket enumeration from the public API.
2. **Fabricated buyer intelligence.** `backend/app/modules/users/router.py:list_buyers` returns calculated ratings, distance, offer price, business type and crop interest from buyer list index/default crop rather than persisted verified data. This creates materially false trust and price claims.
3. **Cross-tenant reservation listing.** `backend/app/modules/reservations/router.py:list_reservations` filters farmer and buyer roles but leaves FPO/admin/other authenticated roles unfiltered. Any authenticated non-farmer/non-buyer can list all reservations, including IDs, quantities, lot and buyer IDs. Must apply explicit admin/operator policy and FPO membership scoping.
4. **Test SMS arbitrary relay.** `/api/v1/notifications/test-sms` is available to any authenticated user and accepts arbitrary destination phone and optional raw message; when credentials are set it can incur costs or be abused for harassment. Restrict to admin/operations, fixed verified destinations, and non-production only, or remove.
5. **Reset token stored in outbox.** `backend/app/modules/auth/service.py:request_password_reset` stores the signed bearer reset token in `OutboxEvent.payload`. In development it is returned as `dev_reset_token`; production returns null but the outbox still retains the secret. Use a one-time hashed token and protected delivery path; redact/expire queued secrets.
6. **Fabricated contractual terms.** `backend/app/modules/trades/service.py:get_or_create_term_snapshot` invents quantity/price/grade/location/delivery/net defaults for missing transaction terms, then persists them. This can turn missing data into apparently agreed legal/financial terms. Block snapshot creation unless source terms exist; do not use defaults for contracts.
7. **False proximity.** Registration and matching/map code maps missing or unknown district coordinates to city coordinates (often Pune/Nashik) and labels distances as if real. Avoid creating/using distance unless coordinates are supplied or verified; preserve uncertainty.
8. **Monetary arithmetic uses binary floats.** `offers/router.py`, `transactions/router.py`, `trades/service.py` and FPO summaries convert `NUMERIC` columns to `float` for totals/fees/net amounts. Use Decimal through the authoritative calculation path and test rounding/unit invariants.

## Other confirmed security/readiness gaps

- Refresh tokens retain session ID on refresh (`auth/service.py:refresh_tokens`) and have no reuse detection/family rotation. Logout revokes tokens and session audit record, but blacklist falls back to per-process memory when Redis is down; this is unsafe for multi-worker production.
- Production config validation (`core/config.py`) checks environment, JWT default and localhost database only. It does not require Redis, secure cookies, provider configuration, S3 encryption/scanning, trusted proxy allowlist, or external secret manager. Backend Docker command trusts forwarded headers from `*`.
- `/api/v1/health` always reports `status=ok`; `/health/detailed` does not inspect worker health and hardcodes `worker=HEALTHY`. Runtime probe observed Redis down and overall degraded, but worker still healthy. Detailed health is not availability/readiness separation.
- `backend/app/modules/metrics/router.py` exposes Prometheus metrics without a role dependency; no network policy was validated.
- Public/market read endpoints and list filters have no verified abuse-specific search rate limits. Auth route limits exist; rate limit uses in-memory fallback when Redis is unavailable.
- Dispute status mutation accepts any uppercase status; no transition validator is evident. Evidence record JSON endpoint accepts caller-supplied S3 key/hash; upload validates owner and declared type/size, but content sniffing/malware scanning was not evidenced.
- Registration checks uniqueness before insert but no tested concurrent duplicate handling/DB race path noted. Password reset is email-only although email is optional for accounts.
- Frontend `Field` in `frontend/src/components/Experience.jsx` sets `autoComplete="off"` globally. Session profile remains in localStorage, and logout clears it; shared-device session-expiry/display behavior needs manual validation.
- Frontend legal routes are generic placeholder sections; real localized policy texts and a privacy-processing/retention inventory are absent.
- Vite fallback wildcard renders `InfoPage` for unknown paths; it does not set HTTP 404 or log route misses.
- `vercel.json` and production response headers need hardening evidence; CSP/HSTS/frame policy absent from repository deployment config inspected.

## Provider inventory

| Provider/capability | Code/config state | Production status |
|---|---|---|
| Agmarknet/data.gov.in | `prices/sync_service.py`; `AGMARKNET_API_KEY` / `MANDI_API_KEY` optional | EXTERNAL DEPENDENCY; no credential/source health observed in runtime |
| PostgreSQL/PostGIS | Compose image `postgis/postgis:15-3.4`; SQLAlchemy models/migrations | EXTERNAL DEPENDENCY; local daemon unavailable, SQLite fallback active |
| Redis | rate limit/token blacklist/outbox ecosystem; Compose service | EXTERNAL DEPENDENCY; runtime probe DOWN |
| Celery worker | app tasks/outbox code and Compose worker command | EXTERNAL DEPENDENCY; no worker running; health falsely reports healthy |
| S3-compatible object store | optional endpoint/bucket/access/secret config | EXTERNAL DEPENDENCY; not configured/verified |
| SMS | Fast2SMS, Twilio, SMSGate implementations/config | EXTERNAL DEPENDENCY; disabled/unconfigured; demo simulation tests are not delivery evidence |
| Payments/escrow | transaction/payment sandbox state only | EXTERNAL DEPENDENCY; real payment/escrow is regulated and not activated |
| Maps/geocoding | OSM raster tile URL and APMC importer geocoder | EXTERNAL DEPENDENCY; no controlled geocoding provider, provenance registry or verified locations |
| Monitoring/error reporting | OTel/Prometheus instrumentation | PARTIAL; no exporter/Sentry/alerting/SLO evidence |

## Scan results

- `npm audit --omit=dev`: 0 reported advisories across 75 production dependencies; registry access succeeded.
- `pip-audit -r requirements.txt`: could not resolve package environment under Python 3.14 because pinned `psycopg[binary]==3.2.5` has no wheel candidate for this interpreter; no vulnerability result can be claimed.
- `python -m pip check`: global interpreter has unrelated conflicts (`grpcio-status` vs protobuf, `gtts` vs click, OTLP common vs opentelemetry-proto). CI uses Python 3.13; local audit used global Python 3.14, so use a clean Python 3.13 environment for a representative dependency audit.
- Secret-pattern scan was not completed due PowerShell quoting/parser error; no positive/negative secret-scan conclusion is made. Do not print or copy secret values into baseline artifacts.
