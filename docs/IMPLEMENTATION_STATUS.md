# KRISHILINK — IMPLEMENTATION STATUS TRACKER

**Last Updated:** 1 September 2026  
**Current Phase:** Phase 0 (Audit Complete) → Entering Phase 0.5 (Foundation Hardening)  
**Active Git Branch:** `feature/production-rebuild-2.0`  
**Test Status:** 73 passing tests (`backend/tests/`)  

---

## 📌 Status Summary Table

| Phase | Description | Status | Verification & Artifacts |
| :--- | :--- | :--- | :--- |
| **Phase 0** | **Comprehensive System Audit** | ✅ **COMPLETE** | `docs/KRISHILINK_IMPLEMENTATION_AUDIT.md` |
| **Phase 0.5** | **Foundation Hardening & Security Fixes** | ⏳ **PLANNED / READY** | Auth refresh rate limit, logout invalidation, frontend token renewal & revalidation, scoped idempotency, proxy rate limiting, dead code cleanup. |
| **Phase 1** | **Trade Aggregate & Unified Trade Room** | ⏳ **PLANNED** | Models `Trade`, `TradeTermSnapshot`, `TradeEvent`; `TradeService`; `TradeRoomPage.jsx`. |
| **Phase 2** | **Buyer Demand Procurement Workspace** | ⏳ **PLANNED** | `BuyerRequirement` CRUD, procurement dashboard, supply gap analysis. |
| **Phase 3** | **Supply Assembly & Demand-Side Matching** | ⏳ **PLANNED** | Multi-lot assembly for institutional orders, explainable match scoring. |
| **Phase 4** | **Trade-Scoped Conversation System** | ⏳ **PLANNED** | Models `Conversation`, `Message`, `MessageAttachment`; in-trade chat. |
| **Phase 5** | **Provider-Neutral Payment Adapter** | ⏳ **PLANNED** | Sandbox/mock adapter, webhook idempotency, truthful status reporting. |
| **Phase 6** | **Operational Logistics & Milestone Proof** | ⏳ **PLANNED** | `TransportRequest`, `TransportAssignment`, `LogisticsCheckpoint`, proof of pickup/delivery. |
| **Phase 7** | **Commodity Quality Inspection Workflow** | ⏳ **PLANNED** | Commodity-specific quality schemas, inspection request/report lifecycle. |
| **Phase 8** | **FPO Aggregation & Member Traceability** | ⏳ **PLANNED** | Member lot allocation, contribution register, FPO supply assembly. |
| **Phase 9** | **Operator Control Tower** | ⏳ **PLANNED** | Operational exception queues for payment, QC, logistics, and dispute triage. |
| **Phase 10** | **Permanent Trade Passport & Observable Trust** | ⏳ **PLANNED** | Authoritative digital trade record generator, observable reliability metrics. |

---

## 🔍 Verified Capability Ledger

| Capability | Backend Model | API Route | Frontend UI | Status |
| :--- | :--- | :--- | :--- | :--- |
| User Auth & Roles (Farmer, Buyer, FPO, Admin) | `User`, `FarmerProfile`, `BuyerProfile`, `FPOProfile` | `/api/v1/auth/*` | `LoginPage`, `RegisterPage` | ✅ Active (needs Phase 0.5 session hardening) |
| Mandi Price Data & Provenance | `Market`, `PriceSource`, `PriceObservation`, `IngestionRun` | `/api/v1/prices/*` | `PricesPage`, `MapPage` | ✅ Active (Real data with provenance) |
| Produce Lot Publishing | `Lot`, `LotAllocation` | `/api/v1/lots/*` | `SellPage`, `FarmerDashboard` | ✅ Active |
| Explainable Matching (Lot → Buyer) | `Match`, `MatchRuleSet` | `/api/v1/matching/*` | `MatchesPage` | ✅ Active (Lot-to-Buyer; Demand-side planned in Phase 3) |
| Offers & Counter-Offers | `Offer` | `/api/v1/offers/*` | `OffersPage` | ✅ Active |
| Transaction Lifecycle (FSM) | `Transaction`, `Reservation` | `/api/v1/transactions/*` | `TransactionsPage` | ⚠️ Partial (Flat cards; Unified Trade Room in Phase 1) |
| Buyer Demand Procurement | `BuyerRequirement` | `/api/v1/matching/` (partial) | `BuyerDashboard` | ⚠️ Partial (Model exists; Buyer UI only browses lots) |
| Disputes & Grievances | `Dispute`, `Evidence` | `/api/v1/disputes/*` | `GrievancesPage` | ✅ Active (S3 evidence upload with IDOR protection) |
| Transactional Outbox & Notifications | `OutboxEvent`, `Notification` | `/api/v1/notifications/*` | `DashboardLayout` bell | ✅ Active |
| Trade-Scoped Messaging | None | None | None | ❌ Not Implemented (Phase 4) |
| Logistics Transport Checkpoints | `Delivery` (Flat) | None | None | ❌ Not Implemented (Phase 6) |
| Quality Inspection Reports | `Lot.grade` (A/B/C) | None | None | ❌ Not Implemented (Phase 7) |
| Digital Trade Passport | None | None | None | ❌ Not Implemented (Phase 10) |
