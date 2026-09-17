# KRISHILINK — PRODUCT & ARCHITECTURAL DECISIONS (ADR SUMMARY)

**Last Updated:** 1 September 2026  
**Status:** Living Architectural Record  

---

## 1. ADR-001: Preservation of FastAPI Core vs Legacy Flask
- **Context:** The repository contained remnants of a legacy Flask application (`backend/flask_app_legacy.py`, `backend/routes/`, `backend/services/`) alongside the production FastAPI backend (`backend/app/`).
- **Decision:** FastAPI with synchronous route handlers delegated to worker threadpools (`def route_handler(db: Session = Depends(get_db))`) is the sole production backend. Legacy Flask files are verified to have 0 runtime or CI dependencies and are slated for clean removal in Phase 0.5.
- **Consequences:** Cleaner repository hygiene, lower Docker image footprint, and zero routing ambiguity.

---

## 2. ADR-002: Provider-Neutral Payment Abstraction vs Internal Custodial Wallet
- **Context:** Previous prototype UI contained claims of "100% Escrow Security" without an active banking or RBI-compliant payment aggregator license.
- **Decision:** KrishiLink will NOT implement an internal custodial wallet or represent database state as escrow. All payment flows will use an explicit `PaymentAdapter` boundary. Until a live payment aggregator (e.g. Razorpay Route, Cashfree, e-NAM e-Payment) is configured, the system will explicitly label payment states as `SANDBOX / SIMULATED PAYMENT`.
- **Consequences:** Regulatory compliance with RBI Payment Aggregator directions, honest user communication, and clean separation of trade obligation from money movement.

---

## 3. ADR-003: Operational Truth & Evidence Integrity
- **Context:** Database transitions (e.g. `IN_TRANSIT`, `DELIVERED`, `VERIFIED`) can easily be marked complete in software without real-world physical reality.
- **Decision:** Every operational transition in logistics, quality, and delivery must distinguish between:
  1. Application/Database State
  2. Externally Verified Provider State
  3. Operator-Confirmed State
  4. User-Submitted Evidence with SHA-256 Checksums
- **Consequences:** Objective proof for disputes, elimination of synthetic statuses, and auditability for institutional buyers and FPOs.

---

## 4. ADR-004: Scoped Idempotency Keys
- **Context:** The original idempotency check stored raw `Idempotency-Key` headers globally without user scoping, creating potential cross-user response collisions.
- **Decision:** Idempotency keys must be composite: `(user_id, endpoint_path, key_value)`.
- **Consequences:** Multi-tenant security isolation and reliable mutation retries.

---

## 5. ADR-005: Demand-Driven Procurement alongside Supply Publishing
- **Context:** Early prototype focused almost exclusively on farmers posting crop lots.
- **Decision:** Introduce a first-class Demand Procurement Workspace where institutional buyers create structured requirements (quantity range, target price, quality parameters, geography, delivery window) and the platform assembles matching supply across multiple farmers and FPOs.
- **Consequences:** Real-world B2B procurement capability, increased trade completion rate, and aggregate demand satisfaction.
