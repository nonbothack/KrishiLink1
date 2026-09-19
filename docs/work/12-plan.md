# Packet 12 plan — Offline, multilingual voice and reach

## Scope and repository evidence

Packet 12 will add a carefully bounded installable web shell, truthful public price caching, farmer-scoped offline listing drafts, and small accessibility/reach improvements on top of the existing React/Vite frontend and FastAPI APIs. Existing lot creation uses the canonical crop API, server quote, `Idempotency-Key`, and backend validation. Existing local form drafts are keyed by the authenticated user ID. In-app notifications use the existing notification/outbox model. No web push, WhatsApp, IVR, browser speech or offline queue provider is configured today.

## Safety decisions

1. The service worker will cache only the static application shell/assets and explicitly public GET resources. It will never intercept POST/PUT/PATCH/DELETE requests or hold authentication/session data, API mutations, user-specific data, signed URLs, or uploaded evidence.
2. Public price snapshots and canonical crop catalogue snapshots may be cached after successful API responses. Offline price views must preserve the source report date/source/unit and show when the snapshot was cached; cached price context must never silently become a contractual asking price.
3. Only a farmer may place a reviewed, whitelisted lot-create payload into IndexedDB. Records contain the owner ID, schema version, payload, idempotency key, creation time and explicit queue state. They are bounded and never silently evicted. The queue has no generic HTTP request shape.
4. Queue processing is user-initiated from the foreground after connectivity and authentication checks. The current authenticated user ID and farmer role must match each record. A retry reuses the same key. Validation/conflict/auth uncertainty becomes `NEEDS_REVIEW`; it is not automatically rewritten or retried in the background. Background Sync will not execute writes.
5. Offer acceptance/counter/decline, trades, payments, FPO mutations, verification, notifications and other consequential actions are never queued or replayed. Remote messages will not authorize or execute such actions.
6. Native browser speech is an opt-in convenience only. Dictation may populate a draft field but never publishes a listing or triggers a financial/state transition. Text-to-speech is user-triggered and must identify browser/device availability rather than imply a KrishiLink voice provider.
7. Simple mode is a per-user convenience preference and cannot change authorization or conceal financial terms. English, Hindi and Marathi copy will use the established translation catalog.
8. SMS `DEMO` results, if retained for isolated tests, must be distinguishable from real provider acceptance. Push, WhatsApp and IVR remain unavailable until real providers and credentials are configured; no UI or API will claim they are ready or delivered.

## Planned implementation

- Add a minimal manifest, icons derived from existing KrishiLink artwork, an explicit GET-only service worker, safe registration/update behavior, and an offline route/shell fallback.
- Add a bounded IndexedDB module for public snapshots and typed farmer lot-queue entries, including owner isolation and testable schema/allowlist guards.
- Extend the existing Sell flow to permit a clearly labelled offline review/queue path only after an explicit confirmation; retain server authority for final quantity/unit/price validation and settlement of the same idempotency key.
- Add a farmer queue panel with state, explicit sync, retry/review and clear behavior; add isolation checks to auth/account transitions without silently discarding queued work.
- Add simple-mode preference and opt-in browser speech read/dictation helpers with full EN/HI/MR labels and user confirmation.
- Report non-configured push/WhatsApp/IVR/production voice delivery honestly. Do not add mock provider success paths or remote consequential actions.
- Add unit tests for queue ownership/allowlists/bounds/retry states, service-worker method restrictions, language coverage, voice confirmation boundaries and provider status truth; add deterministic browser coverage for offline queue and account isolation.

## Verification

Run the Packet 12 prescribed full backend/frontend lint, test, build, E2E, bundle, security-header and secret scans, plus compile, formatting/type checks where local tools exist, and `git diff --check`. Verify PostgreSQL-specific behavior only if infrastructure exists. Review the four target viewports and English/Hindi/Marathi. Do not claim SMS/push/WhatsApp/IVR or browser voice delivery is production-verified without configured real providers.

## Non-goals

No Packet 13 work, generic background write replay, offline offer/trade/payment/FPO/admin actions, remote action by SMS/voice, full offline synchronization, fabricated provider delivery, or changes to the established domain architecture.
