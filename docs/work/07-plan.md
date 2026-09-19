# Work Packet 07 — Buyer Core Pilot Plan

## Verified starting point

Packet 06 leaves a secure farmer journey with canonical lot units, offer acceptance locks, Trade Room records and outbox notifications. Buyer-facing work is incomplete: `BuyerRequirement` is a legacy, unused matcher input; the buyer dashboard directly browses published lots and creates an offer without requirement linkage, owner-scoped requirement APIs, procurement progress or buyer-focused records. Existing matching is farmer-to-buyer oriented and includes opaque scores, so it is not an appropriate buyer discovery API.

The existing offer API already owner-scopes buyer offers, preserves counter history and protects farmer acceptance with lot/reservation locks. It does not link offers to demand or reserve buyer requirement capacity. The existing lots projection has no farmer contact data, but buyer discovery needs an explicitly privacy-safe authenticated projection rather than a reuse of owner lot details.

## Decisions

- Add a compact `requirements` bounded context. Requirements are account-owned because Packet 05 has no safe buyer-organization membership model. No teams, approver flows or shared procurement accounts are introduced.
- Additive schema stores requested original unit/quantity, canonical quintals, committed canonical quantity and explicit lifecycle. `remaining = requested - committed` is calculated by the server; only accepted offers linked at creation increment committed.
- Requirement-linked offer creation locks both the published lot and the active requirement. Farmer acceptance locks the linked requirement before allocation and rejects an overfill. This extends the established offer workflow instead of creating a parallel negotiation system.
- Buyer discovery returns only published/partially allocated lots and a privacy-safe seller label/type, broad location and factual lot fields. It omits phone, email, exact GPS, profile fields and private buyer data. It uses descriptive compatibility statements, not existing opaque match scores.
- Buyer offer review uses server-returned Decimal/canonical amounts. It may link an offer to an active requirement; it cannot invent freight, payment terms or fees. Landed cost exposes only known persisted transaction components.
- Keep the canonical Trade Room and notification/outbox architecture. Do not add provider-backed payment, logistics, quality chain, trust scores, maps, bulk assembly or Packet 08 features.

## Intended files and risk

- Backend: `BuyerRequirement`/`Offer` model fields, additive Alembic revision, new requirements router/service, registered API router, buyer-safe lot discovery and offer acceptance/creation changes.
- Frontend: buyer dashboard plus requirements/discovery route, buyer navigation, API helpers, translated copy and targeted browser coverage.
- Tests: owner isolation, privacy projection, unit/quantity validation, idempotency, expired/foreign offer behavior and requirement-overfill/concurrent-path protection.

Migration will be additive. Existing requirements are retained as legacy active filters with no committed amount; downgrade drops only new Packet 07 columns/tables and refuses no destructive data rewrite. PostgreSQL/PostGIS is required for a real migration and lock-concurrency rehearsal.
