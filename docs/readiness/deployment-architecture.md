# Deployment architecture and tenancy truth

## Current logical topology

```text
Browser / PWA
  -> TLS reverse proxy or CDN
  -> React/Vite static asset (Nginx)
  -> FastAPI /api/v1
  -> PostgreSQL + PostGIS
  -> Redis (rate limits/cache/broker)
  -> Celery worker + beat
  -> private object storage
  -> configured SMS, price, push and future trade providers
```

Trust boundaries are browser↔edge, edge↔API, API↔database/cache, worker↔broker, API/worker↔object storage and provider callbacks. Provider credentials remain server-side.

## Deployment profiles

| Profile | Supported position |
|---|---|
| KrishiLink-operated pilot | Supported as a single logical application with configured infrastructure; provider and legal gates remain. |
| Dedicated institutional deployment | Recommended for an institution today: separate database, secrets, object storage, Redis and environment. |
| Shared multi-institution SaaS | Not implemented. No `tenant_id`, tenant-scoped provider configuration, storage or isolation test suite exists. |

Development, test/CI, staging/UAT and production must use separate databases, storage, secrets and providers. Production data must never seed development by default. Data residency is a deployment choice, not a claim of this repository.

## Future tenant gap

A separately approved design would need tenant identity, tenant-scoped authorization/provider config/audit/storage, migration strategy, billing/configuration, cross-tenant tests and operational support boundaries. Packet 14 intentionally does not add it.

## Data ownership and exit boundary

KrishiLink system metadata and operational audit structure are application-owned; customer/FPO member, intake, pool, lot and trade records are exported only to the authorized owner; public-source observations retain their source/licence conditions; provider data remains subject to the provider contract. This is a deployment/contract boundary, not a legal ownership opinion.
