# Packet 00 — Architecture, API and database map

## Runtime architecture

```text
Browser (React 19 / Vite 8 / React Router 7)
  ├─ frontend/src/pages/ and layouts
  ├─ frontend/src/services/api.js → frontend/src/lib/http.js
  └─ /api proxy (Vite) → FastAPI /api/v1
       ├─ auth, users, crops, markets, prices
       ├─ lots, FPO, matching, offers, reservations
       ├─ transactions, trades, storage, disputes
       ├─ notifications, admin, health, metrics
       ├─ SQLAlchemy models → PostgreSQL/PostGIS (intended)
       ├─ Redis rate limits/token revocation (fallback in dev)
       ├─ Celery worker → outbox/SMS provider tasks
       └─ optional S3-compatible storage
```

Source: `frontend/src/App.jsx`, `frontend/src/services/api.js`, `backend/app/main.py`, `backend/app/modules/**/router.py`, `backend/app/core/database.py`, `backend/app/workers/celery_app.py`. The active FastAPI application is `backend/app/main.py`; Flask under `backend/routes`, `backend/services`, and `flask_app_legacy.py` is a duplicate legacy implementation and is not mounted by FastAPI.

## API surface

OpenAPI: `/api/v1/openapi.json`, OpenAPI 3.1.0, 70 operations observed at runtime, title `KrishiLink API`, version `2.0.0`. Route groups are mounted in `backend/app/main.py`; health is `/api/v1/health`. Runtime contract uses `{success,data,message,request_id}` on typical responses, but validation and HTTP errors are FastAPI error bodies, so envelope consistency is incomplete. Query pagination is page/limit for most listed resources; cursor pagination is absent.

Frontend wrapper `frontend/src/services/api.js` maps prices, crops, lots, matches, offers, transactions, trades, markets, storage, buyers, disputes, notifications and FPO. `frontend/src/App.jsx` mounts public, role-scoped and shared authenticated routes. `/offers`, `/transactions`, `/trades/:id`, `/grievances` are inside authentication but lack client role declarations; backend action checks therefore remain critical. There is no route contract crawler.

## Bounded contexts and current model groups

`backend/app/models.py` declares 32 ORM entities. Relationships inferred from foreign keys (not an exported ERD):

```text
User ─ FarmerProfile / BuyerProfile / FPOProfile ─ FPOMember
User ─ Lot ─ LotAllocation ─ Reservation
User + Lot + BuyerRequirement ─ Match ─ Offer
Offer + Lot + User ─ Transaction ─ TradeTermSnapshot / TradeEvent
Transaction ─ TransactionItem / Payment / Delivery / Dispute
Dispute + Lot + Transaction + User ─ Evidence
User ─ Notification; domain mutations ─ OutboxEvent / AuditLog
Crop ─ CropVariety / PriceObservation ─ Market / PriceSource / IngestionRun
StorageFacility (no booking mutation flow)
SystemConfiguration / MatchRuleSet / IdempotencyKey
```

Data types include UUID identifiers, `NUMERIC` fields for database money/quantity, JSONB/ARRAY, and `GEOGRAPHY(POINT,4326)` models. Application routes frequently coerce decimals to Python float, which loses exact decimal arithmetic at the service/API boundary. No canonical product quantity unit contract is enforced in database. `Database` compatibility functions stub `ST_DWithin` in SQLite as always true, `ST_Distance` as 0, and spatial casts as passthrough; SQLite geo tests therefore do not validate PostGIS distance correctness.

## Migrations and schema risk

Alembic reports one head: `790546cf29fe`, a merge of trade aggregates `7a8b9c0d1e2f` and FPO members `a1f9e42c5b78`, following `6442a44b1f27`, `0111b944a435`, `35063b74a70b`. Merge migration is a no-op. Initial schema uses PostGIS Geography, PostgreSQL ARRAY/JSONB and GIST indexes. No live PostgreSQL/PostGIS service was available; migration upgrade against an isolated SQLite file fails at first migration because `alembic/env.py` imports `app.core.database`, whose module eagerly calls `Base.metadata.create_all()` before Alembic creates the same tables. Production upgrade/downgrade remains unverified. Migration history has two heads only resolved by the merge migration; downgrade behavior with populated data was not tested.

## Data and provider lineage

Active official price path: `prices/sync_service.py` fetches data.gov.in Agmarknet, parses actual arrival dates and low/modal/high values, hashes raw payloads, stores source URL/id/parser/normalization version/retrieved time, and active router only serializes the current parser version. Without API key, the sync returns `unavailable`; no fabricated price fallback was observed in that active route. Legacy `prices/mandi_api.py` still fabricates fallback output and must not be reconnected without removal/quarantine. APMC importer has cached/geocoded seed locations but no documented provenance confidence/verification status for each row. SMS provider configuration is optional; payments are sandbox only; S3 is optional; Redis required for multi-worker revocation/rate limiting correctness.
