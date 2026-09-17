# KRISHILINK — MASTER IMPLEMENTATION AUDIT (PHASE 0 BASELINE)

**Document Version:** 3.0.0  
**Audit Date:** 1 September 2026  
**Auditor:** Principal Engineer & Systems Architect (Antigravity)  
**Status:** Frozen Baseline for Phase 0  

---

## 1. Executive Summary & Audit Mandate

This document establishes the verified baseline reality of the **KrishiLink** repository prior to executing subsequent development phases under the **KrishiLink Master Product Build Specification v3**.

The core objective is to ensure KrishiLink operates as a **truthful, demand-driven agricultural trade execution platform** that orchestrates procurement, negotiation, quality verification, logistics coordination, transactional milestones, and settlement without falsifying real-world guarantees or relying on synthetic mocks.

---

## 2. Verified Baseline Metrics & Quality Gates

| Quality Gate | Command | Result | Verified Details |
| :--- | :--- | :--- | :--- |
| **Backend Pytest** | `python -m pytest -v` (in `backend/`) | ✅ **73 Passed, 0 Failed, 0 Skipped** (7.12s) | 12 test suites covering health, auth, lots, offers, matching, FSM, earnings, pagination, and multi-role E2E journeys. |
| **Backend Static Typecheck** | `python -m mypy app` (in `backend/`) | ✅ **0 Errors in 58 source files** | Strict typing enforced across all FastAPI app modules and core services. |
| **Backend Ruff Linter** | `python -m ruff check app` (in `backend/`) | ⚠️ **4 Fixable Formatting Issues** | Import sorting (I001) and missing trailing newlines (W292) in `app/modules/prices/import_mandi.py` and `app/modules/prices/mandi_api.py`. |
| **Frontend Production Build** | `npm run build` (in `frontend/`) | ✅ **0 Errors** (866ms bundle) | Vite v8.2.2 + Rolldown, HTML 0.55 kB, CSS 60.00 kB, JS ~1.0 MB total. |
| **Frontend Oxlint** | `npm run lint` (in `frontend/`) | ⚠️ **7 Warnings, 0 Errors** | `set-state-in-effect` and `only-export-components` warnings in `useAuth.jsx`, `useLanguage.jsx`, `OffersPage.jsx`, `GrievancesPage.jsx`, `DashboardLayout.jsx`, `MatchesPage.jsx`. |
| **Database Migrations** | `alembic -c alembic.ini upgrade head` | ✅ **3 Migrations Applied** | `35063b74a70b` (init), `0111b944a435` (domain core tables), `6442a44b1f27` (missing indexes). Dual SQLite / PostgreSQL+PostGIS compatibility. |

---

## 3. Architecture & Stack Audit

### 3.1 Active Production Stack (To Preserve)
- **Backend Core**: FastAPI (sync handlers + threadpool execution for SQLAlchemy DB sessions).
- **ORM & DB**: SQLAlchemy 2.0 Declarative Models, PostgreSQL 15 + PostGIS (`GEOGRAPHY(POINT, 4326)`) with SQLite dual-compatibility in tests and local development.
- **Cache & Throttling**: Redis 7 sliding-window rate limiter with per-node in-memory fallback.
- **Async Workers**: Celery 5.4 + Redis broker + Transactional Outbox table (`outbox_events`).
- **Object Storage**: S3-compatible adapter (`boto3`) with MIME/size validation and SHA-256 file hashing.
- **Observability**: OpenTelemetry tracing middleware, correlation IDs (`X-Request-ID`), structured logging, and Prometheus metrics.
- **Frontend SPA**: React 19 + Vite 8 + TailwindCSS + Lucide Icons + React-Leaflet + Recharts.

### 3.2 Dead / Legacy Artifacts (Flagged for Isolated Cleanup)
| Item / Path | Classification | Verification Status | Cleanup Recommendation |
| :--- | :--- | :--- | :--- |
| `backend/flask_app_legacy.py` | Legacy Flask App | Verified 0 imports from `backend/app` or `backend/tests`. | Archive / remove in Phase 0.5 hygiene cleanup. |
| `backend/app.py` | Legacy Flask Entrypoint | Duplicate of legacy flask app. | Archive / remove in Phase 0.5. |
| `backend/config.py` | Legacy Flask Config | References dead Supabase/Flask env vars. | Remove in Phase 0.5. |
| `backend/routes/` | Legacy Flask Routes | 100% superseded by `backend/app/modules/`. | Remove in Phase 0.5. |
| `backend/services/` | Legacy Flask Services | 100% superseded by `backend/app/modules/`. | Remove in Phase 0.5. |
| `backend/requirements.txt` | Dependency list | Contains `flask==3.0.3`, `flask-cors==4.0.1`, `gunicorn==22.0.0`. | Remove unused Flask deps in Phase 0.5. |
| `frontend/src/lib/apiClient.js` | Dead Frontend Client | 0 imports across `frontend/src`. Uses dead `VITE_API_V1_BASE_URL`. | Remove in Phase 0.5. |
| `database/schema_legacy_supabase.sql` | Legacy Supabase SQL | Kept for legacy reference only; not used by Alembic. | Move to legacy archive / clean up. |
| `frontend/.env.example` | Config Example | Contains dead `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`. | Clean up in Phase 0.5. |
| Port Inconsistencies | Config Defaults | `docker-compose.yml` maps `8001:8000`; `.env.example` files list `8000`, `8001`, `5000`. | Normalize to consistent 8000/8001 standard. |

---

## 4. Verified Security & Session Findings

| Issue ID | Category | Finding | Impact | Required Remediation |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Auth Rate Limiting | `POST /api/v1/auth/refresh` lacks `@rate_limit` decorator and `request: Request` parameter. | Brute-force / token flooding vector on refresh endpoint. | Add `@rate_limit(max_requests=30, window_seconds=60, key_prefix="rl_ref")`. |
| **SEC-02** | Token Invalidation | `POST /api/v1/auth/logout` is a no-op that only returns a message without server-side revocation. | Stolen JWT tokens remain valid until expiration. | Implement server-side token revocation / blacklist in Redis. |
| **SEC-03** | Frontend Logout | `useAuth.jsx` `logout()` only clears `localStorage` and never calls the backend `/auth/logout`. | Server never knows user logged out. | Trigger `POST /auth/logout` prior to clearing client state. |
| **SEC-04** | Refresh Lifecycle | Refresh tokens stored in `localStorage` are never used by `services/api.js` to refresh expired access tokens on 401. | User abruptly encounters failed requests upon access token expiry (15 min). | Implement automatic interceptor renewal with queued retry. |
| **SEC-05** | Auth State Revalidation | `useAuth.jsx` restores user from `localStorage` on boot and trusts role/identity without calling `GET /auth/me`. | Deactivated or modified users can access stale client-side UI states. | Revalidate session with `GET /api/v1/auth/me` on startup. |
| **SEC-06** | Idempotency Key Scope | `backend/app/core/idempotency.py` checks `db.get(IdempotencyKey, key)` using raw header string without user scoping. | Cross-user cache collision or response body disclosure if two users submit identical key strings. | Scope idempotency keys to `(user_id, endpoint_path, key)`. |
| **SEC-07** | Proxy Rate Limiting | `rate_limit.py` uses `request.client.host` directly without inspecting `X-Forwarded-For` / `X-Real-IP`. | All clients behind reverse proxy share one throttled IP bucket. | Add proxy-header extraction when trusted proxy headers are present. |
| **SEC-08** | In-Memory Fallback Leak | `_in_memory_buckets` is an unbounded `defaultdict(list)` in memory. | Memory growth under high unique IP/path traffic when Redis is down. | Add periodic eviction or bounded sliding bucket eviction. |
| **SEC-09** | Production Docs Exposure | `backend/app/main.py` hardcodes `docs_url="/docs"`, `redoc_url="/redoc"`, `openapi_url="/api/v1/openapi.json"` regardless of `ENV=production`. | Unintended API schema exposure in hardened production deployments. | Gate `/docs` and `/redoc` behind `env != "production"` or admin authorization. |
| **SEC-10** | Password Reset Delivery | `POST /auth/forgot-password` emits an Outbox event and returns `dev_reset_token` in development, but lacks production email/SMS webhook. | Safe in dev, but requires provider configuration for live delivery. | Formalize provider-ready notification channel in Outbox processor. |

---

## 5. Database & Domain Model Audit

### 5.1 Status Constraint Inconsistency
Database check constraints currently allow mixed casing (both uppercase modern statuses and lowercase legacy statuses):
- `lots.status`: `('DRAFT','PUBLISHED','RESERVED','PARTIALLY_ALLOCATED','SOLD','FULFILLED','CANCELLED','EXPIRED','active','matched','sold','expired','cancelled')`
- `offers.status`: `('PENDING','COUNTERED','ACCEPTED','REJECTED','EXPIRED','CANCELLED','pending','accepted','rejected','expired','completed')`
- `transactions.status`: `('CREATED','PAYMENT_PENDING','PAYMENT_CONFIRMED','PROCESSING','READY_FOR_DISPATCH','IN_TRANSIT','DELIVERED','COMPLETED','DISPUTED','CANCELLED','REFUNDED','offer_accepted','payment_pending','payment_received','completed')`
- `disputes.status`: `('OPEN','UNDER_REVIEW','RESOLVED','REJECTED','ESCALATED','open','under_review','resolved','closed')`

**Remediation Plan**: Normalize all statuses to UPPERCASE via safe migration and data update, then tighten `CheckConstraint` definitions.

### 5.2 Missing Core Domain Entities (Required for Spec v3)
1. **`Trade` & `TradeTermSnapshot` & `TradeEvent`**: Wrap and evolve existing `Transaction` into an immutable commercial trade agreement with full event sourcing and next-action determination.
2. **`Conversation` & `Message`**: Scoped communication container bound to Trade / Offer with role-based participant authorization and attachment support.
3. **`TransportRequest`, `TransportAssignment`, `LogisticsCheckpoint`**: Operational transport lifecycle replacing flat `Delivery` row with pickup/delivery proof and milestone tracking.
4. **`QualityInspection`, `QualityMeasurement`**: Commodity-specific multi-parameter inspection (moisture, foreign matter, grain size, defect rate) with declared vs measured vs verified state.
5. **`SupplyPlan`, `SupplyPlanItem`**: Multi-lot aggregation for institutional buyer requirements.
6. **`Document`**: Versioned metadata for trade agreements, invoices, weighment slips, inspection certificates, and proof of delivery.

---

## 6. Integration Truth Classification Ledger

| Capability / Integration | Declared Classification | Verified Reality | Next Action Required |
| :--- | :--- | :--- | :--- |
| **Market Data (Prices & Mandis)** | **REAL / OPERATOR-ASSISTED** | Live data ingestion from data.gov.in / APMC mandi JSON feeds with source provenance (`raw_payload_hash`, `source_url`, `price_date`). | Maintain data freshness indicators; never invent missing prices. |
| **Geospatial & Distance** | **REAL** | PostGIS `ST_Distance` on `GEOGRAPHY(POINT, 4326)` with Haversine fallback. | Enhance demand-side spatial matching for buyer radius queries. |
| **Object Storage (Evidence & S3)** | **REAL / PROVIDER-READY** | `boto3` S3 adapter with SHA-256 checksums and MIME validation; local filesystem fallback. | Enforce presigned download URLs for sensitive trade documents. |
| **Transactional Outbox & Notifications** | **REAL** | `outbox_events` table + `NotificationService` with row locking (`skip_locked=True`). | Connect outbox events to trade milestone notifications. |
| **Payments & Escrow** | **SANDBOX / MOCK** | `Payment` model and transaction states exist, but **NO real banking/aggregator integration**. UI falsely claimed "100% Escrow Security". | Explicitly label as `SANDBOX / SIMULATED PAYMENT` in UI until regulated partner adapter is integrated. |
| **Logistics & Tracking** | **OPERATOR-ASSISTED / MOCK** | `Delivery` table exists, but no real GPS telemetry or transporter dispatch. | Remove fake live GPS claims; build truthful milestone and checkpoint proof workflow. |
| **Quality Verification** | **OPERATOR-ASSISTED** | Simple A/B/C grading. No lab integration. | Build commodity-specific parameter checklist with inspector-uploaded evidence. |
| **Buyer Demand Procurement** | **PARTIAL / NOT EXPOSED IN UI** | `BuyerRequirement` model exists in DB, but `BuyerDashboard.jsx` only browses farmer lots. | Build full Demand Procurement Workspace: create requirement, view matches, supply plan. |
| **Trade Room** | **PARTIAL / FRAGMENTED** | `TransactionsPage.jsx` shows basic stage cards. Missing unified Trade Room. | Build unified Trade Room component with commercial terms, timeline, next actions, and documents. |
| **Trade-Scoped Chat** | **NOT IMPLEMENTED** | No messaging model or endpoints. | Implement `Conversation` and `Message` modules. |
| **Trade Passport** | **NOT IMPLEMENTED** | No unified immutable passport generator. | Build audit-backed Trade Passport summary view and export. |

---

## 7. Master Phased Implementation Roadmap

1. **Phase 0.5 — Foundation Hardening & Security Remediation**
   - Fix `/auth/refresh` rate limiting (`SEC-01`).
   - Implement server-side logout token invalidation (`SEC-02`, `SEC-03`).
   - Implement automatic refresh token rotation & retry on 401 in frontend (`SEC-04`).
   - Implement frontend session revalidation via `GET /auth/me` on startup (`SEC-05`).
   - Scope idempotency keys to `(user_id, endpoint_path, key)` (`SEC-06`).
   - Implement proxy-aware IP rate limiting (`SEC-07`) and in-memory bucket eviction (`SEC-08`).
   - Gate production `/docs` and `/redoc` behind environment check (`SEC-09`).
   - Fix Ruff formatting errors in `backend/app/modules/prices/`.
   - Clean up dead files (`lib/apiClient.js`, Flask remnants, Supabase env defaults) without breaking active systems.

2. **Phase 1 — Trade Aggregate & Unified Trade Room**
   - Data models: `Trade`, `TradeTermSnapshot`, `TradeEvent`.
   - Backend service: `TradeService` (FSM transitions, next action calculation, financial breakdown).
   - Frontend: Unified `TradeRoomPage.jsx` answering WHAT, WHO, MONEY, LOGISTICS, QUALITY, PAYMENT, DOCUMENTS, TIMELINE, and NEXT ACTION.

3. **Phase 2 — Buyer Demand Procurement Workspace**
   - Complete CRUD for `BuyerRequirement` (quantity, target price, quality specs, delivery window, radius).
   - Demand dashboard with supply gap analysis and matching lots.

4. **Phase 3 — Supply Assembly & Demand-Side Matching**
   - Demand matching algorithm with hard constraint filters and explainable ranking.
   - Sourcing plan for large orders across multiple farmers/FPOs.

5. **Phase 4 — Trade-Scoped Conversation System**
   - Domain models: `Conversation`, `Message`, `MessageAttachment`.
   - Trade/offer context chat with system event markers and authorization controls.

6. **Phase 5 — Provider-Neutral Payment Adapter & Truthful States**
   - Adapter architecture separating obligation, payment intent, provider status, and settlement.
   - Explicit UI labeling: `SANDBOX / SIMULATED PAYMENT`.

7. **Phase 6 — Operational Logistics & Milestone Proof**
   - Models: `TransportRequest`, `TransportAssignment`, `LogisticsCheckpoint`.
   - Proof-of-pickup and proof-of-delivery upload with SHA-256 verification.

8. **Phase 7 — Commodity Quality Inspection Workflow**
   - Configurable commodity schemas (moisture, impurities, grade).
   - Inspection request, assignment, measured parameter capture, and report generation.

9. **Phase 8 — FPO Aggregation & Member Traceability**
   - Member contribution register, lot aggregation, and trade allocation tracking.

10. **Phase 9 — Operator Control Tower**
    - Exception management console (payment pending, logistics delay, QC overdue, dispute escalation).

11. **Phase 10 — Permanent Trade Passport & Observable Reputation**
    - Authoritative digital trade passport summary view and exportable report.
    - Observable participant performance metrics (completed trades, on-time delivery %, dispute %).

---

## 8. Phase 0 Audit Approval Gate

This Phase 0 Audit serves as the immutable baseline record. No major product redesign or destructive rewrite is permitted. All future phases will incrementally build upon the verified FastAPI + React architecture following strict CI, Ruff, Mypy, and Pytest verification.
