# Work Packet 10 — Trade Operations plan

**Branch:** `abdulrehman`  
**Scope:** Packet 10 only. No commit or push.  
**Baseline:** Packet 09 reports 183 backend tests and 21 frontend unit tests passing. The current working tree contains the preceding packets' uncommitted work; preserve it.

## Repository evidence

- `Transaction` and `TradeTermSnapshot` in `backend/app/models.py` are the canonical trade and accepted-terms records. Transaction creation already writes a terms snapshot, initial `TradeEvent`, audit row, and transactional outbox event.
- `TradeEvent` is the existing Trade Room timeline. `get_trade_room()` currently mutates state on GET: it may create a public ID, derive a terms snapshot from the mutable lot/offer, and synthesize an initial timeline event. These reads can make unsupported facts look like accepted evidence.
- `backend/app/modules/trades/service.py` currently labels buyer-initiated payment as “sandbox payment confirmed,” says a completed trade is “settled,” and derives payment/logistics summaries from transaction status. The same module states no funds have moved, so these fields contradict each other.
- `Payment`, `Delivery`, `StorageFacility`, `Dispute`, and `Evidence` tables exist, but payment-provider settlement, operational delivery evidence, storage bookings, and a quality provenance chain are not implemented. `backend/app/modules/storage/router.py` only lists active facilities. The generic storage listing currently does not show provenance/freshness and accepts no bookings.
- The dispute API allows a caller to attach an arbitrary transaction UUID without proving trade participation. Status changes are audited but are not written into the Trade Room timeline. An evidence-attachment endpoint accepts a client-supplied S3 key and hash. Upload trusts the supplied content type and reads the entire body before checking size.
- Demo storage facilities are inserted only by the guarded development `DEMO_MODE` seed. The list response does not label demo records as synthetic.
- `frontend/src/pages/TradeRoomPage.jsx` already renders one trade timeline and clearly says payment is unavailable/no funds moved. The backend response conflicts with this truthful UI. There is no quality, weighment, logistics, or storage request UI in the Trade Room.
- `backend/tests/test_trade_room.py` currently encodes sandbox payment confirmation and trade status transitions that imply delivery/completion. Packet 10 must replace those assertions with truth-preserving contracts.
- Packet 09 verification baseline is recorded in `docs/work/09-result.md`. Local SQLite does not establish PostgreSQL row-lock behavior; PostgreSQL/PostGIS and object storage are unavailable for runtime rehearsal.

## Architecture decisions for this packet

1. Preserve one canonical `Transaction`, immutable `TradeTermSnapshot`, and append-only `TradeEvent` stream. Operational actions add typed, provenance-labelled events to this existing timeline; they do not create parallel trades or timelines.
2. Treat participant statements as participant-reported evidence. Payment references never change the trade to provider-confirmed/paid. Quality claims/photos are participant-submitted; no assay is verified without an actual configured provider or reviewer decision. Dispatch/receipt statements stay attributed to their participant. Weighment net is calculated server-side with `Decimal`; discrepancy does not mutate contractual quantity, price, or payout.
3. Make Trade Room/list GET read-only. They must not invent or backfill terms, public references, or initial events. A trade without an accepted-terms snapshot shows terms and amount as unavailable, retains the safe support path, and rejects operations that depend on agreed money/quantity; it is identified as a legacy data-repair item.
4. Keep storage facilities as discovery facts only when explicitly verified, expose a development-demo marker, and implement a trade-linked **request** as pending confirmation. Do not decrement capacity, assert availability, or claim a booking until an authorized facility operator/provider confirms it. No provider exists in this repository.
5. Attach transaction grievances only after participant authorization. Status/evidence actions append events to the same TradeEvent timeline and use existing audit/outbox mechanisms. Evidence bytes are hashed on upload and stored with uploader, classification, timestamp, size and MIME provenance; client-provided object keys/hashes are not accepted as evidence.
6. Do not introduce a broad support role, payment movement, escrow, freight pricing, automated assay, or fabricated provider integration in Packet 10.

## Planned implementation

- Add an additive migration for event provenance/structured metadata, payment-report provenance/idempotency, immutable evidence classification/file metadata, and trade-linked storage request records if the inspected APIs require persisted request identity.
- Add participant-authorized, idempotent Trade Room endpoints for payment reference reporting/acknowledgement, quality assertions, Decimal weighment, attributed logistics/delivery assertions, storage requests, and transaction grievance linking. Keep provider-confirmed state unavailable.
- Harden the existing dispute/evidence paths and add canonical timeline entries for dispute status and evidence actions.
- Remove misleading payment/delivery/settlement labels and summaries. Add concise Trade Room controls and truthful states using the existing English/Hindi/Marathi translation architecture and design primitives.
- Add tests for participant/object authorization, idempotency, immutable accepted terms, payment truth, evidence provenance/size/type, Decimal weighment, storage pending semantics, dispute timeline, and FPO trade trace compatibility.
- Update Packet 10 result, Packet 10 ADR, and progress tracker with evidence and external verification limits.

## Verification strategy and limits

Run the Packet 09 backend and frontend checks from the attachment plus focused tests. Review migration SQL and Alembic graph; compile Python; lint/build frontend; browser tests at available configured sizes. Run static security-header, provider-key and bundle checks, and `git diff --check`. If no PostgreSQL/PostGIS, S3-compatible object store, or browser runtime is available, record each as externally unverified; never infer those guarantees from SQLite.

## Risks and explicit deferrals

- Existing historical transactions with no immutable snapshot cannot be safely reconstructed from mutable lots/offers; they will require a reviewed data-repair procedure.
- No configured payment, assay, logistics, or storage confirmation provider exists. Packet 10 can record participant statements and pending requests only.
- A participant-supplied file is evidence of what was submitted, not proof that the depicted quality, location, time, or event is true.
- PostgreSQL row locks, PostGIS migration execution, and object-store access-control behavior need infrastructure-backed rehearsal before production activation.
- Provider integration, settlement/payment movement, legal terms, quality lab operations, storage operator workflow, freight quotes, and Packet 11 intelligence remain deferred.
