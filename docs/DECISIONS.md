# Architecture Decisions

This is an append-only decision log. Revisit a decision by adding a superseding entry; do not rewrite accepted history.

## ADR-001 — KrishiLink Packet 01 architecture and domain contracts

- **Date:** 2026-09-17
- **Status:** Accepted for the current modular-monolith phase
- **Scope:** Bounded contexts, lifecycle contracts, API/ID conventions, outbox, provider boundaries, rendering, offline conflict handling, and tenant isolation.
- **Evidence:** `docs/work/00-result.md`, `docs/work/00a-result.md`, `docs/work/01-architecture-and-domain-contracts.md`.

### Decisions

1. Keep FastAPI + SQLAlchemy + PostgreSQL/PostGIS and React + Vite as the current deployment stack. Use module boundaries and explicit ownership inside the modular monolith; do not introduce service decomposition or a rendering framework migration in this packet.
2. A trade has one canonical transition graph in `backend/app/core/domain_contracts.py`. Legacy transaction and Trade Room endpoints remain compatible adapters to that graph. Privileged roles may bypass party-role checks where authorized, never lifecycle validity.
3. A grievance has a closed transition graph; invalid and terminal-state rewrites fail with HTTP 409. `OPEN -> RESOLVED` remains allowed for current admin workflows.
4. Keep UUID database primary keys and existing `KL-*` public references. New public projections should prefer opaque public references; no bulk identifier migration is justified. Keep existing UUID paths as compatibility contracts until a separately versioned API change.
5. Continue the transactional database outbox. Domain mutation and event insertion share a DB transaction. Treat Redis publication and provider delivery as at-least-once; consumers deduplicate by immutable outbox event ID. Retry with bounded exponential backoff and route exhaustion to observable dead-letter/manual review.
6. External provider adapters return normalized accepted/pending/succeeded/failed outcomes and provider references. Persist an attempt before/with asynchronous dispatch, verify callbacks and replay windows, and never report production success for a mock or merely queued request.
7. Keep client-rendered React/Vite. Reconsider SSR only after a measured SEO, initial-render or performance requirement cannot be met within this stack at the Packet 00 baselines.
8. Offline support is draft-first. Cache only explicitly stale-labeled read data; allow local drafts for reversible entry. Never queue payments, offer acceptance, trade transitions, verification or other consequential writes for silent replay. Future sync must use server versions and surface conflicts for user resolution.
9. Use logical tenant boundaries at the account/FPO organization level with server-side object authorization. FPO membership gates FPO-owned data. The current single-tenant database has no `tenant_id`; do not claim database-level isolation. Add explicit tenant keys and isolation tests before onboarding multiple independent institutions or white-label customers.

### Consequences

- Existing workflow endpoints can coexist during migration, but must share the same domain graph and regression tests.
- Storage booking, verification cases, distinct payment attempts, and notification delivery attempts remain unimplemented bounded contexts; their contracts are specified without creating premature schema or endpoints.
- No database migration is required for this decision set.

## ADR-002 — Frontend foundation and design-system baseline

- **Date:** 2026-09-17
- **Status:** Accepted for the current React/Vite application
- **Scope:** Frontend style ownership, reusable interaction primitives, accessibility defaults, and CI gates.
- **Evidence:** `docs/work/02-result.md`.

### Decisions

1. Retain React + Vite and the existing routed application. Establish one authored CSS foundation (`tokens.css` and `app.css`) with shared color, type, spacing, shape, elevation, motion and layout tokens. Remove the unused Tailwind plugin and duplicate/unreferenced styling systems.
2. Use typed reusable controls and patterns for buttons, fields, cards, status, notices, skeletons, and truthful loading/error/empty/stale/offline states. Keep existing business screens and route behavior; migrate only their styling hooks and shared patterns where needed.
3. Make focus visibility, semantic labels, described validation errors, keyboard recovery, reduced motion, and 48px primary actions shared defaults. Continue translating user-facing copy through the existing English/Hindi/Marathi system; avoid default autocomplete suppression.
4. Keep ErrorBoundary recovery local and truthful. DataState must not convert a failed API request into fabricated content.
5. Keep route splitting and establish gzip budgets for initial assets. Enforce six matching static response headers and baseline CSP directives in Nginx and Vercel configuration. Revisit CSP source policy when production API and tile origins are fixed.
6. Type-check the new shared component foundation without converting the existing JavaScript application wholesale. Storybook is not introduced; maintain component usage and accessibility guidance alongside the components.

### Consequences

- Existing product routes, API contracts, translations, and backend code remain in place.
- Static configuration checks do not prove headers or CSP behavior at a live Nginx/Vercel edge; runtime verification remains deployment-dependent.
- Devanagari rendering uses system font stacks until approved, redistributable font files are available.

## ADR-003 — Trusted geography, outlet provenance and crop registry

- **Date:** 2026-09-17
- **Status:** Accepted for Packet 03
- **Scope:** Administrative geography, market outlets, source licensing/provenance, coordinates, crop aliases and ingestion.
- **Evidence:** `docs/work/03-plan.md` and `docs/work/03-result.md`.

### Decisions

1. Extend the existing `markets` entity as the canonical outlet record so price-observation references remain stable. Keep existing rows and coordinates, but mark legacy rows `needs_review`; absent provenance is represented as unknown rather than inferred.
2. Store state, district and subdistrict as optional structured references alongside legacy free text. Add no geography rows until an authoritative, versioned source is available; exact resolution must not silently guess from a city or district label.
3. Record data-source license status and per-outlet source identity, coordinate source/confidence, source confidence, review state and normalized name. Public outlet discovery is limited to active, reviewed records meeting the coordinate and source confidence thresholds; administrative publication requires consistent LGD mappings and approved source terms.
4. Imports are strict, deterministic and review-first. Do not fuzzy-merge records or geocode missing coordinates. No volume target overrides source quality. Reject unsupported encodings, unknown/unapproved licensing and invalid coordinates with row-level evidence.
5. Keep one canonical crop registry with multilingual labels, aliases, supported units and active/tradable status. Preserve unknown ingested commodities as inactive, non-tradable records rather than dropping observations or exposing invented crops.
6. Do not import the repository `List_Of_APMC.csv`: it is undecodable as UTF-8 and has no verified publisher/license record. Population depends on a lawful authoritative source snapshot.

### Consequences

- A verified registry may initially be small or empty. Counts must report evidence-backed verified coverage, never an aspirational target.
- PostGIS behavior and the migration still require a provisioned PostgreSQL/PostGIS verification run before production rollout.

## ADR-004 — Official reported market-price ingestion

- **Date:** 2026-09-17
- **Status:** Accepted for Packet 04; live activation awaits provider and infrastructure configuration
- **Scope:** data.gov.in/AGMARKNET ingestion, price units and provenance, worker schedule, freshness, cache and market-price API.
- **Evidence:** `docs/work/04-plan.md` and `docs/work/04-result.md`.

### Decisions

1. Treat the source as daily **reported** wholesale prices. Public surfaces always display `price_date`, retain a distinct `fetched_at`, and never claim that a same-day record is a real-time quote.
2. Keep the API credential in server-only `SecretStr` configuration. No Vite-prefixed credential is supported; the frontend build scans its output for configured credential material.
3. Store money as `Decimal`/`NUMERIC`, preserve source unit text, and publish only normalized `INR/quintal` or `INR/number` values. An operator must record crop or crop+variety unit conventions when a source row omits its unit. Unknown or unsupported units are retained as low-quality quarantined observations and excluded from public price results.
4. Give observations a database-unique semantic identity over source adapter, resolved crop and market, variety, grade and report date. Corrected source rows update the same observation; genuine variety/grade distinctions remain separate. Preserve legacy rows during migration and do not infer their units.
5. Resolve market labels against unique existing identities; otherwise retain them as inactive review candidates without coordinates. Retain unknown crops and varieties as inactive candidates. Price provenance must not create verified outlet or crop claims.
6. Run national ingestion at 06:00, 13:00 and 18:00 Asia/Kolkata through Celery Beat. Admin/operator requests enqueue work; crop+district requests use the same worker path. A Redis owner-token lock prevents overlapping runs, and the 15-minute source/scope floors remain in force even for a force request.
7. Cache only database-authoritative query responses for 15 minutes. Cache identity includes filters and pagination; successful ingestion advances the source generation. Redis read failure bypasses cache, while inability to coordinate a write prevents starting ingestion.
8. Remove unreachable random/sample price adapters. The separate demo seeder remains available only in development with `DEMO_MODE=true`.

### Consequences

- No production price result is shown until its price unit is established. This is deliberate because AGMARKNET's official manual allows Rs/quintal or Rs/number according to commodity variety.
- The official source credential, PostgreSQL/PostGIS, and Redis must be provisioned before live ingestion and migration behavior can be verified. No real price rows were fetched in this packet.
- The migration is additive and preserves legacy observations. Its downgrade refuses to collapse rows if legitimate variety/grade identities now share a legacy uniqueness key; use a database snapshot/forward repair in that case.

## ADR-005 — Phone identity, sessions, consent and onboarding

- **Date:** 2026-09-17
- **Status:** Accepted for Packet 05; production activation gated on legal and provider readiness
- **Scope:** Phone identity, OTP, password compatibility, browser sessions, onboarding, verification dimensions, consent, privacy requests and GPS.
- **Evidence:** `docs/work/05-plan.md`, `docs/work/05-result.md`, `docs/compliance-matrix.md` and `docs/security/threat-model.md`.

### Decisions

1. Support Indian mobile numbers only for this launch scope. Normalize to E.164 and preserve the legacy phone field. Backfill only unambiguous identities; keep collisions separate and flag them for human review.
2. Store OTP challenge codes as keyed digests and challenge phone keys as keyed digests. Codes are one-use, time-limited and attempt-limited. OTP request responses remain generic; only development with an explicit setting may return a code. Production delivery and phone/IP abuse limits fail closed if their external providers are unavailable.
3. Keep compatibility password login. Password is optional on OTP-first new accounts, with a ten-character minimum when set/reset. Preserve old seeded accounts without treating their prior short password as a new registration rule.
4. Persist session families and one-way refresh-token digests. Rotate on every refresh; reuse revokes the family. A legacy token can enter managed-session storage once, but only if it is unrevoked and matches the current credential version. Password reset increments that version and revokes persisted sessions.
5. Browser refresh secrets stay in HttpOnly cookies. Require strict SameSite, Secure in production, an allowed Origin and a double-submit CSRF token for refresh/logout. Keep access tokens in memory and limit browser-persisted profile fields.
6. Keep the legacy `is_verified` flag for compatibility but do not promote it into phone, email, business, GST, bank, identity or organization evidence. Unconfigured verification providers report `UNAVAILABLE`.
7. Record Terms and Privacy Notice acknowledgements by exact version; keep marketing opt-in separate and off by default. Preserve acceptance and withdrawal timestamps. Record explicit GPS opt-in against the notice version and withdraw it when the user clears stored coordinates. Do not persist consent IP addresses.
8. Privacy-request endpoints record owner-scoped intake only; they do not claim automated access, correction or erasure. Production policy pages remain clearly draft and production registration stays paused until counsel and the organization approve the text and launch decisions.
9. Keep buyer/FPO records owner-scoped under the current single-owner schema. Do not infer organization membership from role or profile existence. Add membership only in a later, separately modeled authorization packet.

### Consequences

- Production activation depends on approved terms/privacy notices, SMS and email providers, Redis, PostgreSQL/PostGIS migration rehearsal, staff authentication decisions and an operating privacy-request/retention process.
- Exact statutory commencement mapping, data purposes, retention, children's-data handling, responsible legal entity and grievance channels require counsel and organization approval. See the official-source-based but non-legal compliance matrix in `docs/compliance-matrix.md`.
- No business/GST/bank verification, production SMS delivery, recovery email, privacy-request fulfillment or multi-user organization authorization is claimed by Packet 05.

## ADR-006 — FPO intake and pool ledger closure

- **Date:** 2026-09-18
- **Status:** Accepted for Packet 08
- **Scope:** FPO roster, receipt corrections, pooled quantity, marketplace publication, partial trades, and member allocation evidence.
- **Evidence:** `docs/work/08-plan.md` and `docs/work/08-result.md`.

### Decisions

1. Keep the persisted ledger chain `member → intake receipt → pool contribution → pool → marketplace lot → offer/trade → member trade allocation`. Generic FPO lot creation/editing cannot bypass or silently mutate pool-backed marketplace terms. A legacy FPO lot without pool provenance must fail closed when accepted.
2. Treat intake and contribution evidence as immutable once used downstream. Correct an unpooled receipt by voiding it and appending a linked corrected receipt with actor, reason, timestamp and audit before/after values. Do not correct a contributed receipt in place.
3. Derive pool totals from persisted contributions. An intake may contribute to multiple pools, but total contributions cannot exceed its valid canonical quantity. Withdrawal closes the published lot/offers and marks the linked pool withdrawn while preserving the ledger.
4. Allocate accepted partial trades against each member contribution's unsold balance using Decimal canonical quantity. Round quantity shares down first, then distribute the residual in stable contribution order without exceeding any balance. Compute monetary allocations separately in Decimal currency precision; the last deterministic allocation receives the exact gross residual. Allocations are projected until genuine settlement evidence exists.
5. CSV roster import is owner-scoped, preview-first, bounded, strict UTF-8, row-validated and idempotent. Import never creates a platform User, login, or implicit FPO membership link. Missing geography remains unknown.
6. Buyer discovery exposes appropriate FPO seller identity and lot facts only. Intake, member, contribution and projected allocation details remain in the owner-scoped FPO trace.

### Consequences

- The existing single-owner FPO profile remains the authorization boundary; multi-user FPO staff membership is deferred.
- SQLite tests establish deterministic contract behavior only. PostgreSQL/PostGIS migration and concurrency rehearsal are required before production activation.
- Payment movement and settlement remain outside this packet; projected member gross allocations must not be presented as paid or net proceeds.

## ADR-007 — Public-route rendering and discovery truth

- **Date:** 2026-09-18
- **Status:** Accepted for Packet 09
- **Scope:** Public-route rendering, canonical crop/outlet pages, public buyer projection, sitemap and language metadata.
- **Evidence:** `docs/work/09-plan.md` and `docs/work/09-result.md`.

### Decisions

1. Retain React + Vite and add a build-time server-rendered public-route subset. Public pages contain route-specific HTML before JavaScript runs; React hydrates the same markup and refreshes API-backed data. Authenticated surfaces remain client-rendered.
2. Build crop/outlet pages only from the canonical crop and reviewed outlet APIs. A build without the public API produces no dynamic registry pages and never fills gaps with sample data.
3. Configure the absolute origin through `PUBLIC_SITE_URL`. Omit canonical/social/sitemap URLs if it is unset rather than publishing an invented origin. Do not emit `hreflang` until locale routes have distinct stable URLs.
4. Treat official market rates as non-contractual reported observations. Do not represent them with `Product`/`Offer` structured data. Emit structured data only for facts present in the rendered document.
5. Public buyer listings use business-verified organization-level fields only. Public market maps contain reviewed outlets only; private buyer/FPO/storage coordinates require an authorized workflow.
6. Legal pages stay visibly marked draft and out of the public sitemap until reviewed. Support contact values come only from explicit public deployment configuration.

### Consequences

- Search indexing of dynamic crop/outlet pages requires deployment builds to reach the public API and configure the canonical site origin. Static local builds without those dependencies remain truthful but have fewer indexable pages.
- Localized copy is available in the existing language switcher, but search indexing of each language waits for stable locale-prefixed or locale-domain URLs.
- Public profile and outlet projection changes must preserve privacy and provenance tests.

## ADR-008 — Trade operations evidence and one canonical timeline

- **Date:** 2026-09-18
- **Status:** Accepted for Packet 10; provider activation remains external
- **Scope:** Trade Room operations, payment reports, quality/weighment evidence, logistics statements, storage requests and trade-linked grievances.
- **Evidence:** `docs/work/10-plan.md` and `docs/work/10-result.md`.

### Decisions

1. Keep `Transaction` plus immutable `TradeTermSnapshot` as the trade aggregate/contract and `TradeEvent` as the only participant-visible operational timeline. Trade Room/list reads do not backfill snapshots, create timeline entries or manufacture public references. Missing legacy terms remain visibly unavailable; operations requiring agreed quantity/price fail closed.
2. A buyer-entered payment reference creates a participant-reported `Payment` and timeline event only. Seller acknowledgement is a second attributed statement. Neither changes the trade to provider-confirmed/paid, and unproven legacy payment rows stay explicitly unknown. `PAYMENT_CONFIRMED` is not reachable from participant or legacy transition routes until a real provider boundary is implemented.
3. Quality claims, weighment and dispatch/receipt updates are attributed participant statements. Weighment net is server-calculated with `Decimal`; it never mutates the accepted contract. Uploaded evidence records server-computed SHA-256, size, MIME signature, actor, timestamp, filename and classification. Participant submission is not an assay or proof of the event depicted.
4. Storage discovery exposes reviewed identity only; capacity, price and present availability remain unconfirmed without an operator/provider freshness contract. A trade-linked storage request remains `REQUESTED`, idempotent and non-reserving until facility confirmation exists.
5. A trade grievance must be opened by a participant or authorized operator. Linked grievance opening/status/evidence events, audit rows and outbox events share the existing trade timeline; no second transaction or timeline is introduced.
6. Trade operations mutation endpoints use authenticated participant checks, row-lock the canonical transaction, and store their event, audit/outbox side effects and idempotency response in the same database transaction. PostgreSQL lock behavior still requires a PostgreSQL rehearsal.

### Consequences

- No payment rail, assay/lab service, carrier, verified weighbridge or storage operator is connected. The application records only attributed statements and pending requests; it cannot claim money moved, quality passed, delivery independently confirmed or storage reserved.
- Existing payments/evidence/storage rows are migrated to `UNKNOWN_LEGACY`; no historical row is promoted to provider-verified evidence.
- PostgreSQL/PostGIS migration execution, row-lock races, and S3-compatible upload/read/delete behavior remain external verification dependencies. SQLite and a mocked object store prove local contracts only.

## ADR-009 — Evidence gates for Packet 11 intelligence

- **Date:** 2026-09-18
- **Status:** Accepted; forecasting remains disabled pending real-series evaluation
- **Scope:** Forecast eligibility, sale-window decisions, channel comparison, Trust Ledger facts, demand signals, and reported-price alerts.
- **Evidence:** `docs/work/11-data-audit.md`, `docs/work/11-model-card.md`.

### Decisions

1. The only production-eligible price series is the Packet 04 official observation path with active `agmarknet-data-gov-v1` source/registry, canonical crop and market, non-null normalized unit, quality other than `LOW`, and preserved source/report/fetch lineage. DemoPriceAdapter SQLite rows and unreferenced JSON exports are never training, benchmark, public-statistic, or alert inputs.
   Descriptive movement requires seven distinct HIGH/MEDIUM-quality report dates, one product/market/unit/source dimension, and a latest report no older than seven days. Direction labels use the explicit configurable `INTELLIGENCE_DESCRIPTIVE_MOVE_THRESHOLD_PCT` (default 1.5%) endpoint-to-endpoint threshold; the API returns the sample dates, count, unit, source and threshold. This is descriptive only.
2. There is no active/candidate trained model until a provenance-complete dataset is audited. Forecast API, sale-window, and demand API return structured abstention. A future segment is forecast-eligible only with at least 365 distinct reported dates spanning 18 months, no gap over 14 days in its latest 90-day window, a latest report no older than 3 days, consistent crop/market/variety/grade/unit/source versions, and at least 30 chronological rolling-origin outcomes. These are launch gates, not claims that any segment qualifies.
3. A future candidate must be evaluated chronologically against last-observation and rolling-median baselines. Promotion requires at least 10% lower MAE than the stronger baseline on at least 70% of otherwise eligible segments, report-date freshness, no detected leakage, and an empirical nominal-80% interval coverage between 75% and 85% over at least 50 valid outcomes per segment. Failure leaves the model shadow/unavailable. These conservative gates require review after real pilot evidence; they are not tuned to maximize coverage.
4. Trust Ledger has no composite score, stars, rankings, or payment-timing rate. Its eligible denominator is canonical `COMPLETED` transactions with a matching immutable positive-quantity/positive-price term snapshot and distinct buyer/seller. Dispute count is all dispute records linked to that denominator; no fault is inferred. Payment timing is unavailable unless a future provider-verified settlement evidence contract is added. Identity verification remains an independent fact. Fewer than five eligible trades is labelled limited history, not low trust.
5. Channel comparison is side-by-side evidence. It may show an actual pending offer and an exact-dimension, fresh official observation in INR/quintal. Unknown freight, commission, storage, or transport remains null; no net value or winning channel is calculated. User-entered assumptions are not persisted or represented as verified cost evidence.
6. Price alerts are deterministic threshold rules over future official reports for an exact canonical crop/market/variety/grade/unit. Creation is rate-limited and accepts the established scoped `Idempotency-Key` convention. An alert created now does not replay earlier observations. An eligible report can trigger once; an observation on the opposite side of the threshold re-arms the rule. Trigger receipts are unique by rule and observation; notification plus outbox is one transaction. Alerts say “reported price”, include market/report date/source, and make no sale-price promise.
7. Existing public `/accuracy` remains an insufficient-evidence statement. No public accuracy or platform uplift metrics are published until fixed-method outcome matching and minimum evaluation samples exist.
8. Forecast, alert, and Trust Ledger switches are independent backend settings. Forecast switch defaults off. Training/model promotion is not exposed to request handlers or ordinary users.

### Consequences

- The local audit qualifies zero forecast segments. Abstention is therefore expected and correct; no ML library, trained artifact, fabricated performance value, or weather/arrival dataset is added.
- Requirements and supply lack a stable common geographic denominator, so no demand ratio is calculated.
- SQLite verifies deterministic alert semantics only. PostgreSQL row locks, migration execution, and Celery/outbox production operation require infrastructure-backed rehearsal.
# ADR-013 — Least-privilege operational tooling

Packet 13 adds explicit server-side staff permission groups, session-bound ten-minute step-up grants for high-risk actions, scoped support context, evidence-backed versioned fraud review cases, and notification-only manual outbox retry. Support is not impersonation and fraud signals are not convictions. Staff UI remains English-first; farmer/customer-facing copy continues to use the existing localization architecture.

# ADR-014 — Government and enterprise readiness boundaries

- **Date:** 2026-09-19
- **Status:** Accepted for Packet 14
- **Scope:** procurement evidence, institutional deployment, portability, backup/DR and readiness wording.
- **Evidence:** `docs/readiness/README.md`, `docs/readiness/government-readiness-matrix.md`, `docs/readiness/deployment-architecture.md`.

### Decisions

1. Readiness artifacts distinguish implemented, tested locally, externally verified and certified. No GIGW/STQC/CERT-In/DPDP/ISO or production-resilience claim is inferred from code or automated tests.
2. The current application has account/FPO logical ownership boundaries but no database-level institutional tenant model and no `tenant_id`. Dedicated institutional deployment with separate database, secrets, object storage, Redis and environment is the supported isolation strategy until a separately approved tenant architecture exists.
3. The FPO export is an owner-scoped JSON manifest with row counts/checksum plus bounded one-domain CSV. It excludes secrets and unrelated staff data and uses formula-injection protection. It is a portability capability, not legal archival certification.
4. Backup frequency, RPO/RTO and DR topology are deployment targets until a live PostgreSQL/object-storage restore drill measures them. SQLite is never presented as PostgreSQL recovery evidence.

### Consequences

- Procurement review can trace evidence without mistaking a readiness pack for certification.
- Shared multi-institution SaaS, SSO/SCIM, VAPT, manual accessibility assessment, provider contracts and live recovery remain explicit gaps or external dependencies.
