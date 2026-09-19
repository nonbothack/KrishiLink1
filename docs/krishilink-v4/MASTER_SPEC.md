# KrishiLink 4.0 — Multi-Stakeholder Production & Procurement-Grade Master Specification

## Execution brief for Astra 6

> **Revision note (4.0):** This version preserves the 3.1 product blueprint and adds a neutral multi-role audit across engineering, QA, operations, security, data/ML, farmer/buyer/FPO workflows, government procurement, investment diligence and judging/demo readiness. It also adds capability tiers, anti-fraud controls, SLOs, DR/BCP, data governance, government-readiness requirements, measurable business outcomes, and a modular Astra 6 execution pack designed to prevent context overload, hallucination, scope loops and uncontrolled rewrites.

**Document status:** authoritative. Where this document and any earlier document, README, or code comment disagree, this document wins. **Constraints:** none on time, tokens, compute, or scope. The only constraint is that every delivered surface must be professional, production-grade and deployable. **Audience of the product:** a 45-year-old onion farmer in Lasalgaon with a ₹7,000 Android phone, 7th-standard education, intermittent 3G — *and simultaneously* a procurement head at a food-processing company, an FPO CEO managing 800 members, a bank partner, and a regulator. **Audience of this document:** an autonomous coding agent with full repository access.

---

# PART 0 — HOW TO EXECUTE THIS DOCUMENT

## 0.1 Execution rules

1. **Work in the order given.** Part 20 contains the numbered task sequence. Parts 1–19 are the specification those tasks implement. Read Parts 1–19 fully before starting Task 1.
2. **Never delete a working capability to satisfy a simplification instruction.** The current `abdulrehman` branch made exactly that mistake (Part 1.3). Correctness and beauty are not in tension; deliver both.
3. **Every prompt in Part 20 is complete when its Acceptance Criteria pass — not when the code compiles.**
4. **Write readable code.** Part 1.3 documents a severe regression where entire pages were compressed onto single 3,000-character lines. Enforce Prettier at 100 columns, one statement per line, no minified-style authoring. A file that a human cannot review is not production-grade regardless of whether it runs.
5. **No fabricated production claims or production-facing data.** Never present invented company names, identities, transaction IDs, certifications, user counts, prices, verification outcomes or statistics as real. Deterministic synthetic fixtures are REQUIRED for unit/integration/E2E tests and MAY be used in an isolated demo sandbox, but they must be clearly labelled synthetic, use reserved test identifiers, be technically prevented from entering production, and never power public metrics or screenshots presented as real outcomes.
6. **No secrets in the frontend.** The mandi API key lives in backend environment configuration only. It is never bundled, never sent to the browser, never committed. Any instruction elsewhere to "hardcode the key" in frontend code is superseded by this line.
7. **Every user-facing string is a translation key** in English, Hindi and Marathi at minimum. No bare JSX string literals.
8. **Mobile-first, 360px.** Design and verify at 360×640 before any other viewport.
9. **Ship tests with features**, not after.
10. **Document decisions** in `docs/DECISIONS.md` as an append-only ADR log.
11. **Architecture before redesign.** Complete Phase 0 before changing public-page architecture. Preserve the current stack by default; migrate only when the Phase 0 benchmark demonstrates that the existing stack cannot meet SSR/SEO/performance requirements without disproportionate complexity. Never rebuild the frontend merely because another framework is fashionable.
12. **Checkpoint every phase.** Each phase ends with tests, an architecture/status note, and a clean git checkpoint. Do not modify multiple major subsystems and defer validation until the end.
13. **External services are capability interfaces, not assumptions.** GST verification, bank verification, payments, WhatsApp, IVR, SMS, weather, maps/geocoding and credit must sit behind provider interfaces. If credentials or commercial approval are unavailable, implement the real interface, honest pending/manual state, and test adapter — never fake a successful production verification.
14. **Progressive disclosure is mandatory on farmer surfaces.** The first viewport answers the farmer's most urgent question and shows at most one primary action plus urgent exceptions. Secondary intelligence remains one tap or one scroll away.

## 0.2 The two non-negotiable product laws

**LAW 1 — Minimum input, maximum output.** A farmer should never type something the system can determine. Location comes from GPS or from their profile. Crop comes from their history. Price comes from the latest trustworthy reported source available for that location/crop, with its source and reported date visible. Unit defaults to quintal. The farmer's job is to confirm, not to enter. Target: **a returning farmer can list a lot in 3 taps and 0 typed characters.**

**LAW 2 — Nothing on screen without a reason and a route.** Every element either answers a question the user has, or moves them toward an action. Decoration that does neither is deleted. Every link resolves. Every filter filters. Every button does its thing.

**LAW 3 — Reveal complexity only when it becomes useful.** Farmer surfaces use progressive disclosure. The first viewport must never resemble a trading terminal. Show the one most relevant price, one recommendation and urgent actions first; advanced comparison, charts, logistics and methodology remain immediately reachable but do not compete for attention.

---

# PART 1 — WHERE THE CODE STANDS TODAY

You are inheriting two branches. Understand both before writing a line.

## 1.1 What the `abdulrehman` branch got right — preserve all of this

This branch is a serious engineering correction and its **logic layer is the foundation you build on.** Do not revert any of it.

| **AreaWhat was fixed**    |                                                                                                                                                                                                                                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Auth hydration**        | `useAuth` now initialises from `readSession()` synchronously; `ProtectedRoute` gates on `loading` and renders `DataState`. Refresh no longer logs the user out.                                                                                                                                   |
| **Role enforcement**      | `ProtectedRoute` takes `roles={[...]}` and every role-scoped route passes it. Farmer can no longer open `/buyer/dashboard`.                                                                                                                                                                       |
| **Token refresh**         | `lib/http.js` implements a single-flight refresh (`refreshPending`) with retry-once semantics, `AbortController` timeouts, typed `ApiError`, and a `session-expired` event. Access token is in memory, not `localStorage`.                                                                        |
| **Silent demo fallback**  | Eliminated. `data/demoData.js` and `data/liveMandiData.js` are gone. Failures now surface through `DataState`.                                                                                                                                                                                    |
| **The DOM translator**    | `utils/universalTranslator.js` deleted. No more `MutationObserver` fighting React, no more `"Seller" → "विक्री कराer"` corruption.                                                                                                                                                                |
| **Language scope**        | Reduced from 7 broken languages to 3 (`en`/`mr`/`hi`) with a single `copy.js` dictionary of 143 reviewed keys. Correct call.                                                                                                                                                                      |
| **Query-param contracts** | `RateLookup` reads and writes `crop`/`district`/`market`/`state`/`page` via `useSearchParams`. `SellPage` consumes `crop`/`quantity`/`price`/`unit`/`district`. `RegisterPage` reads `?role=`. `safeNext()` validates redirect targets against an allowlist — the open-redirect vector is closed. |
| **Unit safety**           | `lib/produce.js` `canonicalLot()` / `convertUnit()` convert between quintal/kg/tonne and store canonically. The 100× pricing error is structurally impossible. Unit-tested.                                                                                                                       |
| **Routing hygiene**       | Scroll-to-top plus hash-scroll on navigation, skip link, `<main id="main" tabIndex={-1}>`, real `/help` `/terms` `/privacy` `/about`, lazy-loaded routes, `ErrorBoundary` with `resetKey={location.pathname}`.                                                                                    |
| **Forms**                 | `<Field>` auto-wires `useId()` → `htmlFor`/`id`/`aria-describedby`/`aria-invalid`. Register is 2-step with `sessionStorage` draft, `/^[6-9]\d{9}$/` phone validation, `normalizePhone()` handling `+91`/`0`/spaces, 8-char password minimum, explicit consent checkbox.                           |
| **Idempotency**           | `createLot` and `createOffer` send `crypto.randomUUID()` idempotency keys.                                                                                                                                                                                                                        |
| **Honesty**               | Hackathon branding, fake UTRs, fake NABL numbers, SHA-256 badges, real company names and "10,000+" all removed. `referenceOnly` disclaimer added to price output.                                                                                                                                 |
| **Testing**               | Vitest unit tests (`produce.test.js`, `session.test.js`), Playwright E2E (`e2e/critical-journeys.spec.js`), `@axe-core/playwright`.                                                                                                                                                               |
| **Assets**                | `harvest-480.webp` / `harvest-800.webp` with `srcSet`, `sizes`, explicit `width`/`height`, `fetchPriority="high"`.                                                                                                                                                                                |

**Verdict:** the correctness work is done and it is good. Build on it.

## 1.2 What the backend already has that the frontend never exposes

This is the single biggest source of latent value in the repository. The backend is far ahead of the UI.

| **Backend capabilityLocationFrontend exposure today**                                                                                                                       |                                                                     |                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Market proximity search with **PostGIS** **`ST_DWithin`** + Haversine fallback, `near_lat`/`near_lng`/`radius_km`                                                           | `modules/markets/router.py`                                         | **None.** `MapPage` calls `/api/v1/markets?limit=500` with no location at all.                             |
| **Official government mandi-price API** integration (data.gov.in resource `9ef84268-d588-465a-a308-a864a43d0070`), key resolution from `settings.agmarknet_api_key` / `mandi_api_key` | `modules/prices/mandi_api.py`, `sync_service.py`, `import_mandi.py` | Partially — `RateLookup` calls `getLivePrices` but shows 3 cards with no trend, no comparison, no history. |
| **APMC importer** for the 482-row `List_Of_APMC.csv`                                                                                                                        | `modules/markets/import_apmc.py`                                    | None.                                                                                                      |
| **Storage facilities** with proximity search                                                                                                                                | `modules/storage/`                                                  | **None.** Zero UI.                                                                                         |
| **Reservations** (storage booking)                                                                                                                                          | `modules/reservations/`                                             | **None.**                                                                                                  |
| **Disputes / grievances**                                                                                                                                                   | `modules/disputes/`                                                 | Stub page only.                                                                                            |
| **Trades + trade room** with aggregates                                                                                                                                     | `modules/trades/`, `TradeRoomPage.jsx` (521 lines)                  | Exists but unreachable from any dashboard navigation.                                                      |
| **Matching engine**                                                                                                                                                         | `modules/matching/`                                                 | Thin 8-line `MatchesPage`.                                                                                 |
| **Metrics**                                                                                                                                                                 | `modules/metrics/`                                                  | None.                                                                                                      |
| **Notifications** incl. `sms_service.py` (Fast2SMS)                                                                                                                         | `modules/notifications/`                                            | None.                                                                                                      |
| **Admin module**                                                                                                                                                            | `modules/admin/`                                                    | No admin UI exists.                                                                                        |

**Implication:** a large share of Part 20's work is *surfacing capability that already exists server-side*, not building from zero.

## 1.3 What the `abdulrehman` branch broke — you must repair all of this

The branch traded the entire product surface for correctness. That trade was unnecessary and must be reversed **without losing 1.1.**

### R1 — The product was deleted, not simplified

| **FileBeforeAfter**   |              |              |
| --------------------- | ------------ | ------------ |
| `LandingPage.jsx`     | 1,050 lines  | **14 lines** |
| `FarmerDashboard.jsx` | \~400 lines  | **10 lines** |
| `PricesPage.jsx`      | \~300 lines  | **4 lines**  |
| `MapPage.jsx`         | rich map     | **14 lines** |
| `Footer.jsx`          | full sitemap | **4 lines**  |

Deleted wholesale: `components/ui/` (Toast, Skeleton, EmptyState, Stepper, MoneyBreakdown, FileUploader, PageLoader, MobileBottomNav, MobileBottomAction, OfflineBanner), `components/visual/`, `components/map/`, `components/Badges.jsx`, `components/States.jsx`, `utils/cropImages.js`.

The home page is now five plain sections. There is no price trend, no calculator, no journey explanation, no imagery beyond one hero photo, no social proof, no FAQ, no comparison, no sale-window guidance. **A farmer landing on this page learns almost nothing and feels nothing.**

### R2 — Code was authored in minified style

`LandingPage.jsx` is 14 lines because entire sections are single lines exceeding 3,000 characters. `RegisterPage.jsx` is 15 lines for a two-step form with role selection, draft persistence and validation. This is unreviewable, un-diffable, and un-maintainable. **Severity: blocks production.** Fix in Task 1.1.

### R3 — Two competing design systems ship simultaneously

`main.jsx` imports **both** `index.css` (375 lines, Tailwind v4 `@theme` + `.btn-primary`/`.card`/`.input` component layer, the *old* system) **and** `styles/experience.css` (28 dense lines, plain CSS custom properties `--forest`/`--paper`/`--sage`, the *new* system). They define different greens, different buttons, different radii. `index.css` is now almost entirely dead weight shipped to every user.

### R4 — `Field` sets `autoComplete="off"` as its default

```jsx
<Tag id={id} ... autoComplete="off" {...props}>

```

The spread rescues fields that pass `autoComplete` explicitly, but any field that forgets gets **autofill actively disabled** — the opposite of the requirement. Invert the default.

### R5 — `/terms` and `/privacy` are placeholders behind a "policy status" notice

`InfoPage` renders 3–4 generic paragraphs for legal pages. DPDP Act 2023 and consumer law require real, complete, language-localised policies before collecting personal data. Currently the registration form collects name, phone, email, location and district behind a consent checkbox that links to pages with no substantive terms.

### R6 — The 404 is a fallthrough, not a route

`<Route path="*" element={<InfoPage/>}/>` — `InfoPage` then infers "not found" from an unmatched pathname. It works, but it renders inside `PublicLayout` with no status signalling and no logging.

### R7 — Unscoped protected routes remain

`/offers`, `/transactions`, `/trades/:id`, `/grievances` carry no `roles` prop. Any authenticated user reaches them. Combined with the backend's own authorisation this may be acceptable — but it is undocumented and unverified.

### R8 — `index.html` is bare

No `meta description`, no `theme-color`, no canonical, no manifest, no `og:image`, no `noscript`, title is `KrishiLink`. For a product whose acquisition channel is a farmer searching "कांदा भाव आज", this is a dead channel.

### R9 — Location is still free text

`RegisterPage` step 2 is three free-text inputs: State, District, Location. `SellPage` repeats it. The backend's geocoding is still the 3-city dictionary — **every user outside Nashik/Pune/Mumbai is silently assigned Pune coordinates**, which corrupts every proximity query in `markets/router.py`.

### R10 — No location detection anywhere

No `navigator.geolocation` call exists in the codebase. The user's explicit requirement — "just after logging in it should fetch the location of user, mark only the very close by mandis and the prices" — is entirely unimplemented.

### R11 — `MapPage` does not use proximity

Fetches up to 500 markets globally, filters client-side by a text `search` box, centres the map on `located[0]` — an arbitrary market. Plain `CircleMarker`s, no clustering, no distance, no prices on the map, no storage facilities, no directions.

### R12 — Dashboards are lists, not intelligence

`FarmerDashboard` = 4 quick links + a list of the farmer's own lots. No prices, no trend, no sale-window guidance, no nearby-mandi comparison, no offer summary, no payment status, no weather, no arrivals. It answers "what did I list" and nothing the farmer actually wants to know.

### R13 — `CROPS` hardcoded again

`lib/produce.js` exports a 9-item array while `SellPage` and `FPODashboard` fetch `getCrops()` from the API. Two sources of truth for the same list.

### R14 — No offline capability, no PWA, no SMS/IVR/WhatsApp, no voice, no price alerts, no admin UI, no storage UI, no logistics UI.

---

# PART 2 — PROBLEM STATEMENT → CAPABILITY MAP

Every clause of the problem statement maps to a named capability. Nothing in the product exists that is not traceable to this table; nothing in this table is left unbuilt.

| **#Problem clauseCapabilityPrimary surfaceStatus today** |                                                                              |                                                                                                                                        |                                |              |
| -------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------ |
| P1                                                       | "limited visibility of current and expected prices across nearby markets"    | **Nearby Mandi Price Board** — GPS-anchored, ranked by distance, latest official/reported price + 90-day history                                                 | Home, Prices, Farmer Dashboard | Partial      |
| P2                                                       | "…and expected prices"                                                       | **Price Forecast & Sale-Window Advisor** — 7/14/30-day range with confidence, hold-vs-sell expected value including storage cost       | Farmer Dashboard, Crop Detail  | **Missing**  |
| P3                                                       | "processors, institutional buyers and digital trading channels"              | **Buyer Directory & Demand Board** — verified buyers, standing requirements, channel comparison (mandi vs direct vs processor vs eNAM) | Buyers, Matches                | **Missing**  |
| P4                                                       | "Information on quality specifications"                                      | **Quality Spec Library** — per crop per buyer: moisture, size, foreign matter, grade definitions with photographs                      | Sell flow, Buyer requirement   | **Missing**  |
| P5                                                       | "demand"                                                                     | **Demand Signals** — arrivals vs demand by mandi, buyer requirement volumes, glut/scarcity indicator                                   | Prices, Dashboard              | **Missing**  |
| P6                                                       | "logistics"                                                                  | **Logistics Marketplace** — transporter quotes, freight calculator, tracking, ePoD                                                     | Trade Room                     | **Missing**  |
| P7                                                       | "storage"                                                                    | **Storage Finder & Booking** — cold stores and warehouses by distance, capacity, rate, WDRA status                                     | Storage                        | Backend only |
| P8                                                       | "payment reliability and buyer credentials"                                  | **Trust Ledger** — verification tier, on-time payment rate, dispute rate, trade count, days-to-pay                                     | Everywhere a buyer appears     | **Missing**  |
| P9                                                       | "fragmented"                                                                 | **Single farmer home surface** answering all of the above in one scroll                                                                | Farmer Dashboard               | **Missing**  |
| P10                                                      | "sell immediately after harvest because of liquidity or storage constraints" | **Liquidity Bridge (partner-enabled)** — eligibility/referral or advance/credit only through a legally authorised lending/finance partner; no KrishiLink balance-sheet lending unless separately licensed and approved                                   | Dashboard, Trade Room          | **Missing**  |
| P11                                                      | "weak bargaining power"                                                      | **Competitive Offer Board + negotiation** — multiple simultaneous offers, counter-offer, reserve price, aggregation                    | Offers, Trade Room             | Partial      |
| P12                                                      | "Buyers may struggle to aggregate consistent volumes"                        | **Aggregation Engine** — FPO pooling, multi-lot assembly against one requirement, split fulfilment                                     | FPO, Buyer                     | Partial      |
| P13                                                      | "and verify quality"                                                         | **Quality Assurance Chain** — photo evidence, self-declared grade, optional third-party assay, dispute-linked grading                  | Sell, Trade Room               | **Missing**  |
| P14                                                      | "lot creation"                                                               | **Lot Builder** — 3-tap, pre-filled, draft-persisted                                                                                   | Sell                           | Partial      |
| P15                                                      | "quality grading"                                                            | Same as P13                                                                                                                            | Sell                           | **Missing**  |
| P16                                                      | "digital offers"                                                             | **Offer engine** with expiry, counter, accept, audit                                                                                   | Offers                         | Partial      |
| P17                                                      | "logistics coordination"                                                     | Same as P6                                                                                                                             | Trade Room                     | **Missing**  |
| P18                                                      | "payment tracking"                                                           | **Payment Timeline** — agreed → dispatched → delivered → invoiced → paid, with UTR from the real payment rail                          | Trade Room, Transactions       | Partial      |
| P19                                                      | "dispute or grievance processes"                                             | **Grievance System** — structured filing, evidence, SLA clock, adjudication, published statistics                                      | Grievances                     | Stub         |
| P20                                                      | "improved farmer price realisation"                                          | **Realisation Report** — what you got vs mandi benchmark, per trade and cumulative                                                     | Dashboard, Reports             | **Missing**  |
| P21                                                      | "reduced information asymmetry"                                              | Sum of P1–P8                                                                                                                           | —                              | —            |
| P22                                                      | "lower transaction cost"                                                     | **Cost Transparency** — full fee breakdown before commitment                                                                           | Everywhere money appears       | **Missing**  |
| P23                                                      | "stronger FPO aggregation"                                                   | **FPO Operating System** — members, intake ledger, pooling, member payout reconciliation                                               | FPO Dashboard                  | Partial      |
| P24                                                      | "reduced post-harvest loss"                                                  | **Storage + sale-window + spoilage clock**                                                                                             | Dashboard                      | **Missing**  |
| P25                                                      | "more reliable buyer sourcing"                                               | **Supply Planner** for buyers — forward requirements, supplier reliability, repeat-supplier book                                       | Buyer Dashboard                | **Missing**  |
| P26                                                      | "transparent transaction records"                                            | **Trade Record** — immutable timeline, downloadable PDF for both sides, tax-ready                                                      | Trade Room                     | Partial      |

**Fourteen of twenty-six core capabilities are entirely missing.** This is the scope.

---

# PART 3 — COMPETITIVE POSITION AND USPs

## 3.1 The field

| **CompetitorWhat they do well — copy thisWhere they leave a gap — exploit this** |                                                                                                                                                                                                                                                                     |                                                                                                                                                                      |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **eNAM** (government, 1,000+ mandis, \~1.68 crore registered farmers)            | Official APMC integration; same-day weighment and lifting; assaying facility; RTGS/NEFT/UPI settlement directly to the farmer's account; 8 languages                                                                                                                | Largely **intra-mandi**; you must physically reach a networked APMC; the interface is government-grade, not consumer-grade; no forecasting; no logistics; no storage |
| **DeHaat** (\~1.4M farmers, 12 states)                                           | **Full lifecycle**: inputs + advisory + credit + market linkage; **voice calls in regional languages**; crop reminders; weather; local mandi rates — proof that voice and advisory drive rural retention                                                            | Input-sales-led economics; market linkage is a secondary motion; concentrated in 12 states                                                                           |
| **Ninjacart**                                                                    | Largest B2B fresh-produce supply chain; genuine end-to-end traceability; operational excellence in fulfilment                                                                                                                                                       | Buyer-side product; the farmer is a supplier, not a customer; little price-discovery tooling for the farmer                                                          |
| **AgriBazaar**                                                                   | **Live bidding / buy-offers the moment a lot is listed** — multiple buyers bid, producing an authentic price signal; commodity price dashboards with current + historical data; 100+ commodities; integrated payments (AgriPay); satellite acreage/yield estimation | Trader-weighted; smallholder UX is not the design centre                                                                                                             |
| **Bijak**                                                                        | **Counterparty rating system built from real transaction data** — the single best trust primitive in the category; payment/credit guarantee; mandi rates from 625+ mandis; supply-chain financing; deliberately simple multilingual app                             | Serves traders/loaders/commission agents more than farmers; does not remove the intermediary                                                                         |
| **Krishify / AgroStar / Kisan Network**                                          | Community, advisory, input commerce                                                                                                                                                                                                                                 | Not price-discovery-first                                                                                                                                            |

## 3.2 What everybody does that we must therefore do (table stakes)

1. Live mandi rates from a large mandi set, in-language, free, no login.
2. Multilingual with real regional-language support.
3. Simple lot listing with photos.
4. Buyer offers visible to the farmer.
5. Digital payment with a traceable reference.
6. Counterparty rating.
7. Weather.
8. An Android app or an installable PWA.

## 3.3 The seven USPs — what makes KrishiLink the one they choose

> These are the product. Every design decision in Parts 5–15 serves one of them.

### USP 1 — "Should I sell today?" answered with a number, not a table

Nobody in the Indian market gives a smallholder a **decision**. They give price tables. KrishiLink computes, for this farmer's crop, grade, quantity and district:

> **Hold 9 more days.** Expected ₹2,610–₹2,780/qtl around 26 Sep (65% confidence). Selling today: **₹4,90,000.** Holding 9 days: **₹5,12,000 − ₹8,200 storage − 1.8% spoilage ≈ ₹5,01,000.** **Difference: +₹11,000.** Storage available 14 km away. [Book storage] [Sell today anyway]

Always a range, always a confidence, always the cost of waiting, always backtested accuracy published on `/accuracy`. This is the headline feature and the reason a farmer opens the app on a day they are not selling.

### USP 2 — The most complete verified map of places you can sell — official and non-APMC channels

Competitors index APMC mandis. KrishiLink aims to index **every outlet it can substantiate with a traceable source or verified partner record**: APMC principal yards and sub-yards, private/licensed mandis, eNAM-networked markets, FPO collection centres, processor gate-buying points, cold stores and WDRA warehouses, government procurement centres (MSP/PACS/NAFED/FCI), village haats/weekly bazaars, and registered private traders. Each with distance, today's rate for *your* crop, arrival volume, typical payment lag and travel time. **Treat this as an internal differentiation target, not a public claim unless independently substantiated.**

### USP 3 — Channel comparison: the same 200 quintals, priced five ways

One screen showing, for this exact lot: nearest APMC, best APMC within 60 km, eNAM, direct processor offer, FPO pooled sale, MSP procurement centre — each with gross, freight, commission, weighment loss, payment lag and **net in hand**. Ranked by net. This is what "price discovery" actually means to a farmer and nobody renders it.

### USP 4 — The Trust Ledger, farmer-side

Bijak proved counterparty rating works — for traders. KrishiLink points it at buyers, for farmers, in farmer language: **"Pays in 3 days, on time 47 of 49 times, 0 disputes, buys onion every week."** Every buyer, everywhere they appear. Earned entirely from platform transaction history, never self-declared.

### USP 5 — Three taps, zero typing

Every competitor's listing flow is a form. KrishiLink's is a confirmation. Crop from your history, quantity from last time (adjustable with a stepper), price from the latest reported trustworthy rate, location from GPS/profile, grade from a photo-assisted workflow. **Tap → tap → tap → published.** This is the concrete expression of Law 1 and it is the single biggest adoption lever for a low-literacy audience.

### USP 6 — Works when the network doesn't

Full offline: cached prices with visible age, offline lot creation with background sync, SMS fallback for price queries and offer acceptance, IVR line with a language menu, WhatsApp bot for alerts and one-tap accept. DeHaat proved voice works. Nobody has combined it with a real marketplace.

### USP 7 — Radical transparency about ourselves

Published on the site, permanently: our fee, who pays it, our dispute resolution rate, our median days-to-payment, our forecast accuracy versus outcome, and aggregated realisation data — what farmers on KrishiLink actually got versus the APMC benchmark, by crop and district. If we are good, this is unbeatable marketing. If we are not, we learn before our users do.

## 3.4 Positioning statement

> **KrishiLink brings nearby mandis, verified buyers, selling channels and price intelligence into one place — helping a farmer understand what their crop may be worth, where they can sell it and what action makes sense next, in their own language.**

Tagline candidates (test with farmers, do not pick internally):

- *"Know your price. Choose your buyer."* / *"तुमचा भाव जाणा. तुमचा खरेदीदार निवडा."*
- *"Sell when it pays."* / *"फायदा होईल तेव्हा विका."*

---

# PART 4 — INFORMATION ARCHITECTURE

## 4.1 Complete route table

Every route below must exist, render, be reachable from navigation, and be covered by the route-contract test (Task 18.2).

### Public — no authentication

| **RoutePurposeNotes**                                                       |                                             |                                                                         |
| --------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| `/`                                                                         | Home                                        | Part 6                                                                  |
| `/prices`                                                                   | Price explorer                              | Crop × district × market, history, comparison                           |
| `/prices/:crop`                                                             | Crop detail                                 | Trend, forecast, mandi comparison, arrivals, spec                       |
| `/mandis`                                                                   | **Mandi & outlet directory**                | List + filters; replaces the thin `/map`                                |
| `/mandis/:slug`                                                             | **Single outlet page**                      | Rates, arrivals, timings, contact, payment lag, directions, SEO landing |
| `/map`                                                                      | Full-screen map                             | All outlet types, clustering, filters                                   |
| `/buyers`                                                                   | Buyer directory                             | Verified buyers + standing requirements (public, contact gated)         |
| `/storage`                                                                  | Storage finder                              | Cold stores + warehouses by distance                                    |
| `/calculator`                                                               | Net realisation calculator                  | Channel comparison, editable assumptions                                |
| `/how-it-works`                                                             | The journey                                 | Scroll narrative, Part 6.6                                              |
| `/help`                                                                     | Help centre                                 | Task-based guides, audio, call/WhatsApp                                 |
| `/help/:slug`                                                               | Individual guide                            |                                                                         |
| `/about`                                                                    | About + registered entity                   |                                                                         |
| `/contact`                                                                  | Contact + grievance officer                 |                                                                         |
| `/terms`                                                                    | Terms of use                                | Full legal, 3 languages                                                 |
| `/privacy`                                                                  | Privacy policy                              | DPDP-compliant, 3 languages                                             |
| `/refunds-and-cancellations`                                                | Refund/cancellation policy                  | Required for payments                                                   |
| `/grievance-policy`                                                         | Grievance redressal policy                  | Statutory                                                               |
| `/accuracy`                                                                 | **Forecast accuracy & platform statistics** | USP 7                                                                   |
| `/security`                                                                 | Security & data handling                    | Institutional audience                                                  |
| `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-otp` | Auth                                        |                                                                         |
| `/404`                                                                      | Not found                                   | Real route, real page                                                   |

### Farmer — `roles={['farmer']}` (FPO where noted)

`/farmer/dashboard` · `/farmer/crops` (my crops & plots) · `/sell` (lot builder) · `/lots` · `/lots/:id` · `/matches` · `/offers` · `/offers/:id` · `/trades/:id` (trade room) · `/transactions` · `/storage/bookings` · `/alerts` (price alerts) · `/reports` (realisation report) · `/profile` · `/settings`

### Buyer — `roles={['buyer']}`

`/buyer/dashboard` · `/buyer/discover` · `/buyer/requirements` · `/buyer/requirements/new` · `/buyer/requirements/:id` · `/buyer/offers` · `/buyer/suppliers` · `/buyer/trades/:id` · `/buyer/logistics` · `/buyer/reports`

### FPO — `roles={['fpo']}`

`/fpo/dashboard` · `/fpo/members` · `/fpo/members/:id` · `/fpo/intake` (procurement ledger) · `/fpo/pooling` · `/fpo/lots` · `/fpo/payouts` · `/fpo/compliance` · `/fpo/reports`

### Shared authenticated

`/notifications` · `/grievances` · `/grievances/new` · `/grievances/:id` · `/account`

### Admin — `roles={['admin']}`

`/admin` · `/admin/verification` · `/admin/disputes` · `/admin/markets` · `/admin/prices` · `/admin/users` · `/admin/audit`

## 4.2 Navigation rules

- **Public header:** Brand · Prices · Mandis · Buyers · How it works · Help · [Language] · [Log in] · [Register]
- **Mobile public header:** Brand · [Language] · [☰] — the menu contains everything plus a prominent "Check today's price" primary action.
- **Authenticated:** role sidebar on desktop, bottom tab bar on mobile (max 5 tabs: Home · Prices · Sell/Buy · Offers · More).
- **Footer:** full sitemap in four columns + legal row + grievance officer + entity details. Public footer links only to public routes.
- **Breadcrumbs** on every page two or more levels deep.
- **Every list page** supports deep-linkable filters via query params.

---

# PART 5 — DESIGN SYSTEM

Build this **first** (Task 2.1) as `src/styles/tokens.css` + a Storybook. Delete `index.css` and `experience.css` after migration.

## 5.1 Design principles

1. **Calm, not corporate.** Warm paper backgrounds, deep field greens, generous whitespace. The screen should feel like daylight, not a trading terminal.
2. **Numbers are the hero.** Prices, quantities and totals get the largest type on any screen. A farmer scanning a price screen should find the number before they find the label.
3. **One primary action per screen.** Everything else is secondary or tertiary.
4. **Photographic, not illustrative.** Real crops, real mandis, real people. Illustration only for abstract concepts.
5. **Density earns its place.** Farmer surfaces are spacious; buyer and FPO surfaces may be denser because that audience wants density.
6. **Motion explains, never decorates.**

## 5.2 Tokens — complete specification

```css
:root {
  /* ---- Brand ---- */
  --brand-900:#0F2E1E; --brand-800:#163A27; --brand-700:#1D4A31;
  --brand-600:#244B38; /* primary */
  --brand-500:#2F6349; --brand-400:#4B8163; --brand-300:#7FA98F;
  --brand-200:#B7CDBF; --brand-100:#DCE8E0; --brand-50:#EEF3EA;

  /* ---- Harvest accent (gold) — CTAs, highlights, price emphasis ---- */
  --harvest-700:#8A6212; --harvest-600:#B28225; --harvest-500:#D4A017;
  --harvest-400:#E8BC4A; --harvest-100:#FBF0D5;

  /* ---- Earth (secondary data series, crop chips) ---- */
  --earth-600:#8C5A3B; --earth-400:#B99678; --earth-100:#F3E9E1;

  /* ---- Surfaces ---- */
  --paper:#FAF9F4; --surface:#FFFFFF; --surface-sunken:#F1F3EC;
  --surface-raised:#FFFFFF; --overlay:rgba(15,46,30,.55);

  /* ---- Text ---- */
  --text:#1B2A20; --text-muted:#5A6B5D; --text-subtle:#7C8A7F;
  --text-inverse:#F4F7F1;

  /* ---- Lines ---- */
  --line:#DCE2D6; --line-strong:#BFCAB9; --focus:#B28225;

  /* ---- Semantic ---- */
  --up:#1F7A4D; --up-bg:#E7F4EC;
  --down:#B3261E; --down-bg:#FCECEA;
  --flat:#6B7A6E; --flat-bg:#F0F2EE;
  --warn:#9A6A00; --warn-bg:#FFF6E0;
  --info:#1D4E89; --info-bg:#E8F0F9;

  /* ---- Type scale (16px base, 1.25 ratio) ---- */
  --font-sans:'Inter var',Inter,system-ui,'Segoe UI',sans-serif;
  --font-devanagari:'Noto Sans Devanagari',var(--font-sans);
  --font-numeric:'Inter var',ui-monospace,monospace; /* tabular-nums */
  --t-xs:12px; --t-sm:14px; --t-base:16px; --t-lg:18px; --t-xl:22px;
  --t-2xl:28px; --t-3xl:34px; --t-4xl:44px; --t-5xl:56px; --t-6xl:68px;
  --lh-tight:1.15; --lh-snug:1.35; --lh-normal:1.6; --lh-relaxed:1.8;

  /* ---- Spacing (4px grid) ---- */
  --s-1:4px; --s-2:8px; --s-3:12px; --s-4:16px; --s-5:20px; --s-6:24px;
  --s-8:32px; --s-10:40px; --s-12:48px; --s-16:64px; --s-20:80px; --s-24:96px;

  /* ---- Radius ---- */
  --r-sm:8px; --r-md:12px; --r-lg:18px; --r-xl:24px; --r-full:999px;

  /* ---- Elevation ---- */
  --e-1:0 1px 2px rgba(20,40,28,.06);
  --e-2:0 4px 12px rgba(20,40,28,.08);
  --e-3:0 12px 32px rgba(20,40,28,.12);

  /* ---- Motion ---- */
  --d-fast:120ms; --d-base:200ms; --d-slow:360ms;
  --ease:cubic-bezier(.2,.7,.3,1);

  /* ---- Layout ---- */
  --container:1200px; --container-narrow:680px; --container-wide:1440px;
  --header-h:72px; --bottomnav-h:64px;
  --tap-min:48px; /* enforced everywhere */
}
@media (prefers-reduced-motion:reduce){
  :root{--d-fast:1ms;--d-base:1ms;--d-slow:1ms}
  *,*::before,*::after{animation-duration:1ms!important;animation-iteration-count:1!important;transition-duration:1ms!important;scroll-behavior:auto!important}
}

```

**Hard rules:**

- Minimum body text **16px**; minimum any text **12px**; never below.
- Every interactive target **≥48×48px** with ≥8px separation.
- Every text/background pair **≥4.5:1**; UI boundaries ≥3:1. CI-checked.
- All monetary and quantity figures use `font-variant-numeric: tabular-nums`.
- No raw hex outside this file. Enforced by lint rule.

## 5.3 Component library — build every one, document every one in Storybook

**Primitives:** Button (primary/secondary/tertiary/danger/ghost × sm/md/lg × loading/disabled/icon-only/full-width), IconButton, Link, Badge, Chip, Avatar, Divider, Card, Panel, Sheet, Modal, Drawer, Tooltip, Popover, Tabs (WAI-ARIA), Accordion, Breadcrumb, Pagination, Progress, Spinner, Skeleton, Toast, Banner, Callout.

**Form:** Field wrapper, TextInput, NumberInput, CurrencyInput (₹ adornment, Indian grouping, tabular), QuantityStepper (large ± targets — primary quantity control for farmers), PhoneInput (fixed +91, numeric keypad, OTP-aware), OtpInput (6-box, paste, Web OTP API), Select, SearchableSelect, CascadingLocationPicker, DatePicker, RadioGroup, RadioCardGroup (image cards for crop/grade), CheckboxField, ConsentGroup, FileUploader (camera-first, client-side compression, progress, retry), VoiceInput, Slider, Switch, FormError, FieldHint, ReviewList.

**Data display:** StatCard, PriceCard, PriceTicker (pausable), TrendSparkline, PriceChart (recharts, accessible table fallback), ComparisonTable, DistanceBadge, FreshnessBadge (`Live` / `Today` / `11 Sep` / `Stale`), TrustScore, VerificationBadge (names what was verified), StatusPill, Timeline, MoneyBreakdown, EmptyState, ErrorState, DataState.

**Domain:** CropPicker (photo grid), GradePicker (photo-based), MandiCard, MandiMap, OutletTypeLegend, LotCard, OfferCard, OfferComparison, BuyerCard, StorageCard, TransporterQuoteCard, SaleWindowAdvisor, ChannelComparison, RealisationCard, DisputeCard, MemberRow, IntakeRow.

**Layout:** PublicLayout, DashboardLayout, Sidebar, BottomNav, PageHeading, Section, Grid, Stack, Container, StickyActionBar.

## 5.4 Typography and language

- Latin: **Inter var**, self-hosted, subset, `font-display: swap`.
- Devanagari: **Noto Sans Devanagari**, self-hosted, subset to the actual glyph set used.
- Preload only the weights actually used (400, 550, 650).
- Devanagari needs \~8% more line-height than Latin at the same size — set per-language line-height tokens.
- Never let a language switch cause layout shift: reserve space with `font-size-adjust` and test all three languages in visual regression.

---

# PART 6 — THE HOME PAGE, DESIGNED FROM SCRATCH

## 6.1 What the home page is for

Three jobs, in priority order:

1. **Answer "what is my crop worth today, near me" within 5 seconds and zero navigation.** This is the acquisition loop. A farmer who gets a real answer for free comes back tomorrow.
2. **Make the journey from harvest to money legible and believable** — this is where the scroll narrative lives.
3. **Convert into the right role's onboarding** without the farmer, buyer and FPO paths ever blurring.

Everything else is subordinate.

## 6.2 Section-by-section specification

> Order is deliberate. Do not reorder without farmer testing.

### S1 — Header (sticky, 72px)

Part 7.1.

### S2 — Hero (above the fold, 360px-first)

- **Eyebrow:** `FROM YOUR FARM. ON YOUR TERMS.` (existing `heroTag` key — keep, it tests well).
- **H1:** ≤8 words, two lines, second line in `--brand-400`. Test 5 variants with farmers.
- **Subhead:** ≤20 words, one concrete benefit.
- **Primary CTA:** `Check today's price` → opens the inline Rate Lookup (S3) by scroll + focus, **not** a page navigation. Secondary: `List my crop` → `/sell` (or `/register?role=farmer&next=/sell`).
- **Trust line:** `No account needed to check prices` with a shield icon. True today; keep it true.
- **Hero media:** the responsive WebP set already in the branch, extended to AVIF + 3 widths (480/800/1440), `fetchpriority="high"`, `<link rel="preload">`, explicit dimensions, ≤120 KB at the largest breakpoint. Keep the asymmetric `border-radius:100px 16px 16px 16px` treatment — it is distinctive and cheap.
- **On mobile:** image *below* the copy and CTAs. The fold must contain H1 + subhead + both CTAs.
- **Live proof chip** overlaying the image: today's top mover, real, from the API — `Onion · Lasalgaon · ₹2,450 ↑ 3.1% · 16 Sep`. If the API is down, the chip does not render (no placeholder).

### S3 — Rate Lookup (the product's front door) — `id="rates"`

This replaces the old decorative marquee and is the most important block on the page.

**Behaviour:**

- On mount, request geolocation **non-blockingly** with a friendly inline prompt (`Show prices near me` button — never an unprompted browser permission dialog on load). On grant, resolve to district via `/api/v1/geo/reverse` and set it.
- On deny or unavailable, fall back to: last used (localStorage `krishilink_price_choice`, already implemented) → IP-derived district → `Nashik` with a visible "change district" affordance.
- **Crop selector:** horizontally scrollable photo chips (12 most-traded first, then search). Remembers last choice.
- **District selector:** `CascadingLocationPicker` (State → District), searchable.
- **Result:** for the chosen crop, the **5 nearest outlets ranked by distance**, each showing: name, type badge (APMC / private / eNAM / processor / FPO / procurement centre), **distance in km**, modal price in `--t-3xl` tabular numerals, min–max range, arrival volume, `FreshnessBadge`, and 7-day sparkline.
- **Below the list:** three actions — `See all mandis near me` → `/mandis?crop=X&near=me`; `Compare all channels` → `/calculator?crop=X`; `Sell at this rate` → `/sell?crop=X&price=Y&market=Z&unit=quintal`.
- **Four states** mandatory (Part 5.3 `DataState`): skeleton matching final dimensions, empty with nearest-alternative suggestion, error with retry, success.
- **Disclaimer:** keep `referenceOnly`. Add the source and fetch time: `Source: Government of India (Agmarknet) · updated 06:15 today`.

**This block is also** **`/prices`** **in expanded form.** One component, two densities — the existing `RateLookup compact` pattern is correct; extend it.

### S4 — "Should I sell today?" teaser (USP 1)

- Two-column: left, a plain-language explanation; right, a **data-backed worked example** for the crop selected in S3.
- Shows: today's net, projected window, expected difference, confidence, and a `See my recommendation` CTA → `/prices/:crop#advisor` (public) or the farmer dashboard advisor (authenticated).
- Always renders the confidence band and a link to `/accuracy`. Never a bare point estimate.

### S5 — The Journey (scroll narrative) — `id="how-it-works"`

Part 6.6. This is the emotional centre of the page.

### S6 — Channel comparison strip (USP 3)

A single horizontally-scrollable comparison for the selected crop and a default 100 qtl: *Nearest APMC · Best APMC in 60 km · eNAM · Direct buyer · FPO pooled · MSP centre*, each with **net in hand** as the hero number and the deductions listed beneath. `Open full calculator` → `/calculator`.

### S7 — "Selling options near you" (USP 2)

- A real, interactive, **lazily-mounted** map preview centred on the user's district showing all substantiated outlet types with a legend, source/confidence treatment, plus a database-derived count: *"1,240 outlets mapped across Maharashtra — 38 within 50 km of you."* The count must be computed from the database, never hardcoded.
- CTA → `/map`.

### S8 — Trust: who you are selling to (USP 4)

- Three or four real, anonymised-where-necessary buyer cards showing the `TrustScore` primitive: verification tier, on-time payment %, median days to pay, trades completed, dispute rate.
- If there is not yet enough transaction history to compute these, **this section does not render.** Do not fabricate. Replace with the "How we protect you" block until real data exists.

### S9 — Three audiences

Three cards — Farmer (green), Buyer (slate/blue), FPO (earth) — each with: one benefit headline, three concrete capabilities, one CTA to its own `/register?role=…`. Colour-code consistently with the registration forms so the user never wonders whether they are on the right form.

### S10 — Social proof

Real farmer stories with consent: name, village, crop, what happened, verifiable outcome. Photo and, ideally, a 20-second in-language video with captions. **If no real stories exist yet, render nothing here.**

### S11 — Radical transparency (USP 7)

A compact stats strip pulled from the current metrics API: median days to payment, dispute resolution rate, forecast accuracy, average realisation vs benchmark. Every figure links to `/accuracy` for methodology. This is the section that makes an institutional reader trust the product.

### S12 — FAQ

8–10 accordion items answering the questions farmers actually ask: *Who pays you? · When do I get my money? · What if the buyer says the quality is bad? · What if I don't have an email? · Do I need a smartphone? · Is my land record needed? · Can I sell without a bank account? · What if the truck doesn't come?* Use `FAQPage` structured data.

### S13 — Final CTA + language reassurance

Primary CTA by role, plus: *"Works in Marathi and Hindi. Call us and we will do it for you: 1800-XXX-XXXX."* with a `tel:` link.

### S14 — Footer

Part 7.2.

### Persistent — mobile sticky action bar

Bottom bar on mobile only: primary action changes with scroll depth — `Check today's price` above S3, `Sell at this rate` after a crop is selected, `Register free` past S9. 56px, never covers content (add matching `padding-bottom` to the page).

## 6.3 What must NOT appear on the home page

Infinite decorative marquees · particle canvases · 3D tilt cards · fake dashboards · fabricated transactions · invented certifications · cryptographic vocabulary · "cockpit", "assaying", "non-custodial", "provenance", "institutional" on farmer-facing copy · any number that is not sourced · any CTA that dead-ends at a bare login screen · autoplaying audio · more than one animation in a viewport at a time.

## 6.4 Home page performance budget (hard gates)

| **MetricBudget**                                  |                                                           |
| ------------------------------------------------- | --------------------------------------------------------- |
| LCP (Slow 3G, 4× CPU throttle, mid-range Android) | **< 2.5 s**                                               |
| INP                                               | **< 200 ms**                                              |
| CLS                                               | **< 0.1**                                                 |
| Initial JS (gzip)                                 | **< 150 KB**                                              |
| Above-the-fold image weight                       | **< 200 KB**                                              |
| Total page weight on first visit                  | **< 900 KB** including the scroll sequence's first frames |
| Fonts                                             | < 90 KB total, subset, preloaded                          |

## 6.5 Home page SEO

`index.html` and per-route meta must include: unique `<title>` and `<meta name="description">` per route; `og:` and `twitter:` cards with a generated image; `theme-color`; canonical; `hreflang` for `en`/`hi`/`mr`; `manifest.webmanifest`; `<noscript>` fallback stating the price-check phone number.

Structured data: `Organization`, `WebSite` + `SearchAction`, `FAQPage` on S12, `BreadcrumbList`, and **`Product`****/****`Offer`****-style markup on** **`/prices/:crop`** **and** **`/mandis/:slug`** — these are the pages that will rank for "कांदा भाव आज लासलगाव" and they are the cheapest acquisition channel available.

Generate `/mandis/:slug` and `/prices/:crop` as **statically pre-rendered or SSR pages** (Part 16.4). Client-only rendering forfeits this channel entirely.

## 6.6 The scroll narrative — full technical specification

> The user will supply a video. This section specifies exactly how to turn it into a production-grade scroll-driven sequence without destroying the performance budget.

### 6.6.1 What it shows

Six chapters of one farmer's real journey, each with a caption in the active language and a `Learn more` link:

| **#ChapterCaption (en)Links to** |                                 |                                                     |                           |
| -------------------------------- | ------------------------------- | --------------------------------------------------- | ------------------------- |
| 1                                | Harvest in the field            | "Your crop is ready."                               | —                         |
| 2                                | Checking the price on the phone | "See what it's worth — in every nearby mandi."      | `/prices`                 |
| 3                                | Listing the lot                 | "Put it up for sale in three taps."                 | `/sell`                   |
| 4                                | Offers arriving                 | "Buyers send you their price. You choose."          | `/offers`                 |
| 5                                | Weighing and loading            | "Weighed in front of you. Recorded for both sides." | `/how-it-works#weighment` |
| 6                                | Bank SMS on the phone           | "Money in your account."                            | `/how-it-works#payment`   |

### 6.6.2 Asset pipeline (build-time, scripted — `scripts/build-sequence.mjs`)

1. Source video: ≥1080p, locked-off or slow camera motion, **no cuts inside a chapter**, \~24 s total.
2. Extract at **12 fps** → \~288 frames. (24/30 fps is imperceptibly better here and doubles weight. 12 fps is the tested floor for smooth scroll-scrub.)
3. Produce **three ladders**: 640w, 1080w, 1600w.
4. Encode each frame as **AVIF q≈45** with **WebP fallback**. Target **≤18 KB/frame at 1080w**, ≤9 KB at 640w.
5. Emit a manifest `public/sequence/manifest.json`: `{fps, count, widths, chapters:[{frame, key, captionKey, href}], poster}`.
6. **Budget gate in CI:** total sequence at the width the device will actually load must be **≤ 2.2 MB**; fail the build otherwise.

### 6.6.3 Runtime

- Render into a `<canvas>` inside a `position:sticky` viewport-height stage, with a tall scroll spacer (`height: 600vh`).
- Choose the ladder from `window.devicePixelRatio`, viewport width and `navigator.connection.effectiveType`.
- **Progressive load:** decode chapter keyframes first (6 images), render the nearest keyframe immediately so the section is never blank, then stream the in-between frames in scroll direction with a small look-ahead window. Use `createImageBitmap` off the main thread.
- Drive from a single `IntersectionObserver` + `requestAnimationFrame`; never one listener per frame. Unmount and free bitmaps when the section leaves the viewport by more than 1.5 screens.
- Captions are real DOM (`aria-live="polite"` on chapter change), not painted into the canvas — they must be selectable, translatable and screen-reader accessible.
- Progress indicator: 6 dots, clickable, keyboard-operable, each jumping to that chapter's scroll offset.

### 6.6.4 Mandatory fallbacks — all three required

| **ConditionBehaviour**                                               |                                                                                                                                             |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `prefers-reduced-motion: reduce`                                     | Render the **6 keyframes as a static vertical story** — image + caption + link, stacked. No canvas, no scroll hijack, no sequence download. |
| `navigator.connection.saveData` or `effectiveType` in `2g`/`slow-2g` | Same static story at 640w.                                                                                                                  |
| Canvas/JS failure, or no support                                     | Same static story (server-rendered by default; the canvas *enhances* it).                                                                   |

**Author the static story first and the canvas as the enhancement**, not the reverse. This guarantees the section works for everyone and is SEO-indexable.

### 6.6.5 Accessibility

- The stage is `role="img"` with an `aria-label` describing the whole journey.
- The scroll spacer never traps the keyboard; `Tab` moves past the section normally.
- All six captions and links exist in the DOM at all times (visually hidden when not active) so screen readers and crawlers get the full narrative.
- Never hijack scroll velocity; the page must still scroll at native speed.

---

# PART 7 — HEADER, FOOTER, LEGAL

## 7.1 Header specification

**Desktop (≥1024px), 72px sticky,** **`backdrop-filter: blur(8px)`****,** **`--paper`** **at 96% opacity, 1px bottom line:** `[Skip link] [Brand + tagline] | Prices Mandis Buyers How it works Help | [Language ▾] [Log in] [Register →]`

- Brand: existing mark is good (rounded square + Sprout + `Krishi**Link**` + `GROW. CONNECT. THRIVE.` microtype). Keep it; raise the microtype from 8px to 10px — 8px is below the legibility floor.
- Active nav state uses `NavLink` `.active` with a 2px underline in `--brand-600`, not colour alone.
- Language picker: `SearchableSelect`-lite, min 48px, `aria-label`, shows native names (English / मराठी / हिंदी), persists to profile when logged in, to `localStorage` otherwise.
- Authenticated: replace the auth buttons with `[Notifications •] [Avatar ▾]` menu (Dashboard, Profile, Settings, Help, Log out).

**Mobile (<1024px), 64px:** `[Brand] ......... [Language] [☰]`

- Menu is a full-height `Sheet` from the right, focus-trapped, `Escape` closes, focus returns to the toggle, `aria-expanded` correct.
- First item in the sheet is a large primary action: **`Check today's price`**.
- Include a `tel:` call-support row at the bottom of the sheet.

**Rules:** exactly one top bar (the ticker is a page section, not chrome). No sticky element may consume more than 15% of a 640px-tall viewport.

## 7.2 Footer specification

Four columns + legal row.

| **ColumnContents** |                                                                                                    |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| **Product**        | Market prices · Mandi directory · Map · Buyers · Storage · Calculator · Price alerts               |
| **Learn**          | How it works · Help centre · Guides · Forecast accuracy · Blog                                     |
| **Company**        | About · Contact · Careers · Press · Partner with us                                                |
| **Support**        | Call 1800-XXX-XXXX (staffed hours) · WhatsApp · Raise a grievance · Grievance officer name + email |

**Legal row:** `© {year} {Registered Entity Name Pvt Ltd} · CIN: {…} · Registered office: {full address}` then `Terms · Privacy · Refunds & Cancellations · Grievance Policy · Security`.

**Rules:**

- Public footer links only to public routes. No `/sell`, `/matches`, `/transactions` in the public footer — they bounce logged-out users into a redirect trap.
- `#how-it-works` uses `<Link to="/#how-it-works">`, never a bare `<a href="#…">`.
- Language switcher repeated in the footer.
- Include the support phone number as a `tel:` link — this audience calls.
- No hackathon, ministry, or any attribution that implies endorsement.

## 7.3 Legal pages — real content, three languages

These are **blocking for launch**, not polish.

### `/privacy` — must reflect the DPDP Act 2023 + final DPDP Rules 2025 and their commencement schedule

Identity of the Data Fiduciary · exhaustive list of personal data collected (name, mobile, email, location/GPS, district, land details, transaction records, device identifiers, photographs) · **purpose for each category** · lawful purpose/consent basis as applicable · itemised consent and how to withdraw it · sharing (payment partner, SMS gateway, logistics partner, analytics, error reporting — each named by category) · cross-border-transfer position · retention/erasure policy per category · security measures · rights and grievance mechanisms available under the DPDP framework as they become applicable · **business contact details for the person responsible for privacy questions, and DPO details where the organisation is legally required to appoint a DPO (including if designated a Significant Data Fiduciary)** · children's data policy · cookie/local-storage disclosure · change-notification process. Maintain a `docs/compliance-matrix.md` that maps each DPDP Act/Rules obligation to its legal commencement date and implementation status; do not represent a future-effective obligation as already mandatory or omit an obligation merely because its commencement is deferred.

### `/terms`

Nature of service (facilitator vs principal — state it unambiguously) · eligibility · account and verification · **listing rules and prohibited produce** · **the fee schedule in numbers, matching the home page exactly** · offer formation and when a contract arises · quality specification and rejection handling · weighment authority · delivery and risk transfer · payment terms and timelines · cancellation · **limitation of liability** · indemnity · suspension and termination · IP · governing law and jurisdiction · dispute resolution ladder · force majeure · e-commerce rules compliance (Consumer Protection (E-Commerce) Rules 2020: display of seller details, grievance officer, no unfair trade practices).

### `/refunds-and-cancellations`, `/grievance-policy`

Statutory. Grievance policy must name the officer, give a contact address, and state the **acknowledgement (48 h) and resolution (30 day) SLAs**.

### Implementation

- Store as structured MDX/JSON per language with a `version` and `effective_date`.
- Record consent against the version accepted, in the database, with timestamp — Task 8.6.
- Render a version history and a diff for material changes.
- Legal review before launch. Mark the task blocked until signed off.
- Compliance baseline as of this specification: MeitY notified the final Digital Personal Data Protection Rules, 2025 in November 2025 with staggered commencement. Re-check the official MeitY/Gazette text immediately before production launch and update `docs/compliance-matrix.md`; do not rely on this product specification as legal advice.

---

# PART 8 — AUTH, ONBOARDING AND THE DATABASE

## 8.1 Target flows

### Farmer registration — OTP-first, 4 screens, \~45 seconds

1. **Role** — three large photo cards. Pre-selected from `?role=`.
2. **Mobile** — `+91` fixed prefix, numeric keypad, `/^[6-9]\d{9}$/`. → **Send OTP**.
3. **OTP** — 6-box input, Web OTP API autofill, 30 s resend timer, 3 attempts then cooldown. On success the account exists and `is_verified_phone = true`.
4. **Location + name** — `Use my location` (GPS → reverse geocode → prefilled State/District/Taluka, editable) or cascading manual picker. Name. Optional: primary crops (photo multi-select), landholding band.
5. **Consent** — separate unticked checkboxes: Terms, Privacy, and (separately) marketing. Version-stamped.

**Password is optional for farmers.** OTP is the login. Offer "set a password" later in settings. This removes the single largest lockout cause in the audience.

### Buyer registration

Company name · GSTIN (format + checksum validated, then verification through a configured `BusinessVerificationProvider`; use official/authorised lookup where legally and commercially available, otherwise route to manual review) · contact person · business email (verified by link) · mobile (OTP) · procurement categories · monthly volume band · delivery locations · bank account for settlement (verified through a configured `BankVerificationProvider`, e.g. penny-drop where the chosen provider supports it). Blue theme throughout. Verification is a **queue**, not instant — show clear pending state and what is unlocked meanwhile.

### FPO registration

FPO registration number · CBBO / promoting institution · member count · districts of operation · authorised signatory (name + OTP) · bank account. Earth theme.

### Login

Single identifier field, phone-first with `+91`, `normalizeIdentifier()` already handles email vs phone. Two paths: **`Get OTP`** (primary) and `Use password` (secondary). `Forgot password?` wired to the existing `/auth/forgot-password`. Contextual reason banner when arriving from a redirect (`intentNotice` key already exists).

## 8.2 Backend auth work required

| **TaskDetail**                            |                                                                                                                                                                                                                        |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **OTP service**                           | `POST /auth/otp/request` and `/auth/otp/verify`. 6-digit, 5-minute TTL, hashed at rest, 3 attempts, per-number and per-IP rate limits, 30 s resend cooldown, delivery via the existing `notifications/sms_service.py`. |
| **Phone normalisation server-side**       | `normalize_phone()` applied on write and on lookup. Migration to canonicalise existing rows.                                                                                                                           |
| **`is_verified`** **must mean something** | Set `is_verified_phone`, `is_verified_email`, `is_verified_gst`, `is_verified_bank` independently, each only when its configured provider or documented manual-review workflow passes, each with a timestamp, verification method/provider and an audit row. The UI badge names *which* check passed.   |
| **Consent records**                       | `consent_records(user_id, policy_type, policy_version, accepted_at, ip, user_agent, withdrawn_at)`.                                                                                                                    |
| **Refresh-token rotation**                | Rotate on every refresh, store a hash, detect reuse → revoke the family. httpOnly + Secure + SameSite=Strict cookie.                                                                                                   |
| **Server-side logout**                    | Already called by `useAuth.logout()`; ensure it revokes the family.                                                                                                                                                    |
| **Rate limiting + lockout**               | On `/login`, `/register`, `/otp/request`, `/forgot-password`. Exponential backoff. `rate_limit.py` exists — extend it.                                                                                                 |
| **Password policy**                       | ≥10 chars, checked against a common-password list, `zxcvbn`-style strength meter in the UI.                                                                                                                            |

## 8.3 Database — schema additions

Beyond the existing models, add (with Alembic migrations and indexes):

```
-- Geography (the missing foundation)
states(id, lgd_code, name, name_hi, name_mr, iso_code)
districts(id, state_id, lgd_code, name, name_hi, name_mr, centroid geography(Point,4326))
talukas(id, district_id, lgd_code, name, name_hi, name_mr, centroid)
villages(id, taluka_id, lgd_code, name, pincode, centroid)          -- optional depth

-- Outlets: substantiated places/channels where a farmer may be able to sell (USP 2)
outlets(
  id, slug UNIQUE, name, name_hi, name_mr,
  type ENUM('apmc_principal','apmc_sub','private_mandi','enam','processor',
            'fpo_centre','warehouse','cold_store','procurement_centre',
            'haat','trader','collection_centre'),
  state_id, district_id, taluka_id,
  address, latitude, longitude, location_geog geography(Point,4326),
  apmc_code, enam_code, wdra_reg_no, licence_no,
  operating_days, operating_hours, market_day,
  contact_phone, contact_email, website,
  commodities_traded TEXT[], typical_payment_lag_days,
  commission_rate_pct, source ENUM('apmc_csv','agmarknet','enam','osm','manual','partner'),
  source_ref, source_confidence NUMERIC(3,2), verification_method, verified_at, verified_by, last_source_checked_at, is_active,
  created_at, updated_at
)
CREATE INDEX ON outlets USING GIST (location_geog);
CREATE INDEX ON outlets (district_id, type, is_active);

-- Prices
price_observations(id, outlet_id, crop_id, variety, grade, min_price, modal_price,
                   max_price, unit, arrival_qty, arrival_unit, price_date,
                   source, source_ref, fetched_at, UNIQUE(outlet_id,crop_id,variety,grade,price_date))
price_forecasts(id, crop_id, district_id, horizon_days, predicted_low, predicted_modal,
                predicted_high, confidence, model_version, generated_at)
forecast_outcomes(id, forecast_id, actual_modal, error_pct, evaluated_at)   -- powers /accuracy
price_alerts(id, user_id, crop_id, district_id, direction, threshold_price,
             channel ENUM('push','sms','whatsapp'), is_active, last_fired_at)

-- Crops (single source of truth, replaces lib/produce.js CROPS)
crops(id, slug, name, name_hi, name_mr, aliases TEXT[], category,
      default_unit, valid_units TEXT[], image_url, is_tradable,
      agmarknet_name, typical_price_min, typical_price_max)
crop_varieties(id, crop_id, name, name_hi, name_mr, agmarknet_name)
quality_specs(id, crop_id, grade, moisture_max, foreign_matter_max,
              size_min_mm, size_max_mm, damage_max_pct, description, reference_image_url)

-- Trust (USP 4)
trust_scores(user_id, trades_completed, on_time_payment_rate, median_days_to_pay,
             dispute_rate, rejection_rate, avg_counterparty_rating,
             computed_at, sample_size)

-- Logistics & storage
transporters(id, name, phone, vehicle_types TEXT[], service_districts INT[],
             rate_per_km, capacity_tonnes, is_verified, trust_score)
freight_quotes(id, trade_id, transporter_id, amount, eta_hours, status)
storage_bookings(id, user_id, outlet_id, crop_id, quantity, unit,
                 from_date, to_date, rate_per_qtl_per_month, status)

-- Governance
consent_records(...)          -- see 8.2
audit_log(id, actor_id, action, entity_type, entity_id, before JSONB, after JSONB,
          ip, user_agent, created_at)
notification_log(id, user_id, channel, template, payload JSONB, status,
                 provider_ref, sent_at, delivered_at, failed_reason)

```

**Data integrity rules:** money as `NUMERIC(14,2)`, never float. Quantity as `NUMERIC(14,3)` canonical in quintals. Every table gets `created_at`/`updated_at`. Every state transition writes an `audit_log` row. Soft-delete via `deleted_at` on user-owned entities.

## 8.4 Location intelligence — the piece that unlocks everything

**Delete the 3-city dictionary in** **`auth/service.py`** **in Task 6.1.** Replace with:

- `GET /api/v1/geo/reverse?lat=&lng=` → `{state, district, taluka, village?, confidence}` resolved against `districts`/`talukas` polygons or nearest-centroid.
- `GET /api/v1/geo/states`, `/districts?state_id=`, `/talukas?district_id=` for the cascading picker.
- `GET /api/v1/outlets/nearby?lat=&lng=&radius_km=&type=&crop_id=` → outlets sorted by distance with today's price for the crop joined in. Uses the PostGIS `ST_DWithin` path already written in `markets/router.py` — extend it, don't rewrite it.
- Frontend `useLocation()` hook: permission-aware, caches the resolved district for 24 h, exposes `{status: 'idle'|'prompting'|'granted'|'denied'|'unavailable', coords, district, setDistrict}`. Never blocks render. Never triggers the browser prompt without an explicit user gesture.
- Post-login behaviour (the explicit requirement): on first authenticated render, if the profile has no coordinates, show a **single dismissible card** — *"Show mandis near you?"* → one tap → GPS → reverse geocode → save to profile → the entire dashboard re-anchors. If dismissed or denied, fall back to the profile district and show a `Set your location` affordance in the header.

## 8.5 Mandi/outlet dataset — how to build it properly

> The instruction was to "scrape the internet and hardcode all mandi locations." **Do not hardcode coordinates in frontend source.** Build a seeded, versioned, auditable dataset in the database. Same outcome, production-grade.

Build `backend/scripts/seed_outlets.py` as an idempotent, re-runnable pipeline:

| **LayerSourceYields** |                                                                                                                                 |                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1                     | `List_Of_APMC.csv` (482 rows, already in repo) — via the existing `markets/import_apmc.py`                                      | APMC principal + sub yards                                                      |
| 2                     | **Agmarknet / data.gov.in** market master from the same resource already integrated                                             | Market names + district + state for every market that reports prices nationally |
| 3                     | **eNAM** networked mandi list                                                                                                   | `enam_code`, confirms eNAM capability                                           |
| 4                     | **LGD (Local Government Directory)**                                                                                            | Authoritative state/district/taluka codes and names in English + Hindi          |
| 5                     | **OpenStreetMap Overpass** — start with high-signal marketplace/market-yard/procurement tags and named agricultural-market features; generic `building=warehouse` / `landuse=farmyard` records are enrichment candidates only, never proof that produce can be sold there | Coordinates/enrichment candidates for missing markets and possible haats; all low-confidence candidates require corroboration before being labelled a selling outlet         |
| 6                     | **WDRA registered warehouses**                                                                                                  | Cold stores and warehouses with registration numbers                            |
| 7                     | **State agriculture department market lists** (per-state, scripted per state)                                                   | Private/licensed mandis                                                         |
| 8                     | Manual/partner entry via `/admin/markets`                                                                                       | Processor gate points, FPO centres, trader shops                                |

**Geocoding:** for any outlet without coordinates, geocode `name + taluka + district + state` against a licensed geocoder or Nominatim (respect usage policy, cache aggressively), then **flag** **`verified_at = NULL`** **until reviewed**. Never show an unverified coordinate on the map without a visual "approximate location" marker.

**Quality gates before an outlet goes live:** has coordinates within India's bounding box; has state + district resolved to LGD codes; name deduplicated (fuzzy match ≥0.92 against existing); type assigned; and has evidence that the location actually functions as the claimed agricultural selling/procurement/storage channel. Assign `source_confidence` from documented rules. Government/regulated registries may auto-publish at high confidence; OSM-only or web-scraped candidates remain `unverified`/`approximate` until corroborated by a second source, partner record, admin review or field verification. Never turn a generic warehouse/farmyard/business POI into a farmer selling option based only on a map tag. Everything else lands in an admin review queue.

**Target coverage for launch:** 100% of Agmarknet-reporting markets nationally (\~3,000+), 100% of the 482 APMC rows, all eNAM mandis, and ≥80% coordinate coverage. Publish the coverage number on `/about` — and update it from the database, never by hand.

## 8.6 Live prices — correct architecture

```
data.gov.in  →  [backend scheduler]  →  price_observations  →  Redis cache  →  API  →  UI
   (api-key, server-side only)         (normalised, dated)     (15 min TTL)

```

- Key from `settings.agmarknet_api_key` / `mandi_api_key` (already implemented in `mandi_api.py`). **Never in the frontend bundle. Never in git. Never in a** **`VITE_*`** **variable** — every `VITE_*` variable is public.
- Scheduler: full national sync 3×/day (06:00, 13:00, 18:00 IST) + on-demand refresh for a crop/district pair with a 15-minute floor.
- Every observation stores `fetched_at` and `price_date` separately. **The UI always shows** **`price_date`**, never `fetched_at`, as "reported on".
- `FreshnessBadge` states: `Live` (price\_date = today) · `Yesterday` · `{date}` (≤7 days, amber) · `Stale — rates may have changed` (>7 days, warn styling, and the number is de-emphasised).
- Never label bundled or cached data "live". Never fall back to sample data. If the sync fails, the API returns the last real observation **with its real date**, and the UI says so.
- Rate-limit and back off against data.gov.in; alert on sync failure; expose sync health on `/admin/prices` and in `/api/v1/health`.

---

# PART 9 — FARMER EXPERIENCE (the core redesign)

> Governed by **Law 1: minimum input, maximum output.** Measure every screen against it.

## 9.1 `/farmer/dashboard` — what a farmer sees the moment they log in

The current dashboard is four links and a list of the farmer's own lots. Replace it with a progressively disclosed answer to *"what should I do today?"*. **First viewport rule:** show Block 1, the farmer's single most relevant price/recommendation from Blocks 2–3, and any urgent item from Block 4. Do not show all nine blocks competing above the fold. Blocks 5–9 appear below or behind clear `See more`/contextual expansion when relevant. Keep the information hierarchy below:

### Block 1 — Greeting + location anchor

`{Greeting}, {name}` · `📍 {Taluka}, {District}` with a one-tap change. If no location is set, this block becomes the **"Show mandis near you?"** card (Part 8.4).

### Block 2 — **Today's price for my crops** (the reason they opened the app)

For each crop in the farmer's profile (or each crop they have an active lot in):

- Big modal price, tabular numerals, `--t-4xl`.
- Change vs yesterday with arrow + sign + colour (never colour alone).
- Nearest outlet name + distance; a second line showing the **best price within 60 km** and how much more it is.
- 7-day sparkline.
- `FreshnessBadge`.
- Actions: `Sell here` · `Compare all` · `Set alert`.

If the farmer has no crops set: a photo crop-picker — *"Which crops do you grow?"* — 3 taps, saves to profile, never asked again.

### Block 3 — **Should I sell today?** (USP 1, the differentiator)

Per crop with an active lot or a stated harvest:

```
Onion · Grade B · 200 quintals · Nashik

Sell today            ₹4,90,000   (₹2,450 × 200)
Hold to ~26 Sep       ₹5,12,000   (₹2,560 × 200, 65% confidence, range ₹2,410–₹2,780)
  − storage 9 days      −₹8,200   Sahyadri Cold Store, 14 km
  − expected spoilage   −₹2,800   1.8% at this grade
  ────────────────────────────
  Net if you hold       ₹5,01,000

→ Holding looks better by about ₹11,000.
   [ Book storage ]  [ Sell today anyway ]  [ How we calculate this ]

```

Rules: always a range, always a confidence, always the cost of waiting, always a link to `/accuracy`. If confidence <50%, the recommendation becomes *"Too uncertain to advise — here is the data"* and shows the chart instead. **Never a bare point estimate. Never a guarantee.**

**Forecast safety and model-governance requirements:**

- Use time-respecting walk-forward/backtesting only; no random train/test split that leaks future observations.
- Validate separately by crop, market/district and season; publish sample size, MAE/MAPE (or a more suitable robust error metric), interval coverage and calibration.
- Require minimum data sufficiency before generating advice. Sparse/new markets inherit only from an explicitly documented hierarchical model and display lower confidence.
- Detect stale upstream data, structural breaks, extreme volatility and out-of-distribution conditions; these trigger **abstention**, not a confident recommendation.
- Keep model/version, feature snapshot, generated timestamp and input-data cutoff with every forecast so decisions are reproducible.
- Monitor drift and forecast-outcome calibration in production. Disable or downgrade a crop/region automatically when quality thresholds fail.
- Weather, arrival volumes, storage/spoilage assumptions and transaction costs must be sourced, versioned or explicitly user-editable assumptions — never hidden constants.
- The product is decision support, not a guaranteed price promise. Copy must explain uncertainty in farmer language without shifting responsibility through legalistic text.

### Block 4 — **Action queue** (what needs you)

A single prioritised list, not tabs: new offers awaiting response (with expiry countdown) · a trade awaiting weighment confirmation · a payment overdue · an incomplete listing draft · an unverified bank account. Each row: what happened, what it's worth, one primary action. Empty state is a genuine achievement state, not "no data".

### Block 5 — **My listings**

Card per lot: crop photo, quantity, asking price, status pill, **offer count with best offer value**, days live, views. Actions: view offers · edit · lower price (with the latest reported rate shown alongside) · withdraw.

### Block 6 — **Money**

This month received · pending · average days to payment · **realisation vs mandi benchmark** (USP 7, per-farmer): *"Your last 6 sales averaged ₹2,512/qtl. Lasalgaon APMC averaged ₹2,390 over the same period. +5.1%."* Link to `/reports`.

### Block 7 — **Nearby**

Compact map preview: outlets within 50 km with today's rate for the farmer's primary crop, plus storage with available capacity. `Open map`.

### Block 8 — **Weather + advisory**

7-day forecast for the farmer's location with harvest-relevant framing (*"Rain expected Thursday — consider harvesting before Wednesday evening"*), and rain alerts against any scheduled pickup.

### Block 9 — Help strip

`Call us · WhatsApp · Watch how it works` — always present, always reachable.

**Mobile layout:** the same blocks, single column, in the same order. Bottom nav: Home · Prices · Sell · Offers · More.

## 9.2 `/sell` — the 3-tap lot builder

**Returning farmer target: 3 taps, 0 typed characters.**

| **StepDefault sourceFarmer action** |                                                          |                                                   |
| ----------------------------------- | -------------------------------------------------------- | ------------------------------------------------- |
| Crop                                | Last listed crop / profile crops                         | Tap a photo chip                                  |
| Quantity                            | Last listing's quantity                                  | `QuantityStepper` ± (±10 qtl, long-press for ±50) |
| Price                               | **Latest available official modal rate for their nearest outlet**, pre-filled | Accept, or nudge ±                                |
| Unit                                | `quintal`                                                | — (change is a secondary control)                 |
| Grade                               | Last used                                                | Tap a **photo** card                              |
| Location                            | Profile / GPS                                            | —                                                 |
| Photos                              | Camera                                                   | Optional but strongly prompted                    |

Then a **review screen** with everything in large type, a continuously updated gross total, an editable row per field, and one `Publish` button.

**Retain from the current branch:** `canonicalLot` unit conversion, localStorage draft per user, `crypto.randomUUID()` idempotency key, the review step, `prefilled` notice when arriving with query params.

**Add:**

- **Price sanity check** — if the asking price deviates >40% from the latest reported modal rate for that crop/district, show a confirmation step (*"This is much higher than today's rate of ₹2,450. Is that right?"*), never a silent accept.
- **Live "what you'd get" panel** — gross, minus estimated freight to the nearest outlet, minus platform fee, = **estimated net**, updating as they type.
- **Reserve price** (optional) — "don't show me offers below ₹X".
- **Available-from date** and an expiry for the listing.
- **Photo upload**: camera-first, client-side compression to ≤200 KB, progress, retry, offline queue.
- **Voice input** on every field (Part 15.2).
- After publish: *"Your lot is live. We've told 14 buyers who buy onion in Nashik."* — a real number from the notification fan-out, and then the matches screen.

## 9.3 `/offers` — comparison, not a list

- Offers grouped by lot, sorted by **net to farmer**, not gross.
- Each card: buyer name + `TrustScore` + verification badges · price/unit · quantity (full or partial) · **net after freight and fees** · payment terms (`Pays in 3 days`) · pickup date · expiry countdown · quality conditions.
- A **comparison table** across offers on the same lot with the best value in each column highlighted.
- Actions: Accept · Counter (with a suggested counter based on the latest reported benchmark and offer history) · Decline (with a reason, feeding the matching engine) · Message.
- Accepting shows a full pre-commitment breakdown and requires explicit confirmation. Nothing about the money is revealed after acceptance that wasn't shown before it.

## 9.4 `/trades/:id` — the trade room

Keep and extend the existing 521-line implementation. Required timeline stages, each with evidence and both-party visibility: **Agreed → Quality check → Weighment → Dispatched → In transit (with tracking) → Delivered → Invoiced → Paid.** Each stage: timestamp, actor, photos/documents, and a "raise an issue" affordance. Downloadable PDF trade record for both sides, tax-ready. Make it reachable from the dashboard, offers, and transactions — currently it is orphaned.

## 9.5 `/prices` and `/prices/:crop`

- `/prices`: the expanded `RateLookup` — crop × district × market × date range, sortable table + map toggle, CSV export, deep-linkable filters.
- `/prices/:crop`: hero number for the user's district · 90-day chart with range selector · **forecast band overlay** · mandi comparison table sorted by distance with net-after-freight · arrivals volume chart (supply signal) · seasonality (this month across 5 years) · quality spec for the crop · buyer demand for it · `Set alert` · `Sell at this rate`. **This is the SEO landing page** — server-render it.

## 9.6 `/alerts` — price alerts

`Tell me when onion crosses ₹2,600 in Nashik` → SMS / WhatsApp / push. Manage, snooze, delete. This is the highest-retention feature in the product and costs one form.

---

# PART 10 — BUYER EXPERIENCE

## 10.1 `/buyer/dashboard`

1. **Supply pipeline** — requirements vs committed vs delivered vs gap, this week and this month.
2. **Matching lots right now** — ranked by fit (crop, grade, quantity, distance, seller trust), each with landed cost (price + freight) computed to the buyer's delivery point.
3. **Price intelligence** — what the buyer paid vs market average by crop and week; procurement cost trend.
4. **Active trades** by stage with anything blocked surfaced first.
5. **Supplier book** — repeat suppliers with reliability, rejection rate, average days from offer to delivery.
6. **Arrivals forecast** — expected regional supply for their crops over the next 14 days, from the arrivals data.

## 10.2 `/buyer/requirements`

Structured, reusable standing requirements: crop, variety, grade with an explicit **quality specification** (moisture, size, foreign matter, damage tolerance — from `quality_specs`), quantity, frequency, delivery location, price ceiling, payment terms, valid-until. Publishing a requirement notifies matching farmers and FPOs. **This is the demand signal that makes P5 and P25 work.**

## 10.3 `/buyer/discover`

Lot search with filters: crop, grade, quantity range, distance from a delivery point, seller type (farmer/FPO), seller trust score, availability date. Map view. Saved searches with alerts. Bulk offer to multiple lots. Multi-lot assembly against one requirement with a combined landed-cost calculation.

## 10.4 Buyer obligations

Every buyer surface shows their own trust metrics prominently — on-time payment rate, dispute rate, rejection rate. Making the buyer's reputation visible *to the buyer* is what makes it improve.

---

# PART 11 — FPO EXPERIENCE

Keep the existing member/pooling implementation and build it into a real operating system.

1. **`/fpo/members`** — roster with crop, expected harvest, ready quantity, KYC status, bank verification, share capital. Bulk import from CSV. Member-facing SMS.
2. **`/fpo/intake`** — the procurement ledger. Per member per delivery: gross weight, tare, net, moisture, grade, rate, amount payable, advance paid, balance. Printable receipt for the member in their language. **This is the FPO's daily operational need and nobody serves it well.**
3. **`/fpo/pooling`** — select members → validate same crop+grade (already implemented) → preview combined lot → reserve price → publish. Show per-member contribution and projected payout before publishing.
4. **`/fpo/payouts`** — after a trade settles, split proceeds by contribution, minus the FPO's declared service charge, with an individual statement per member and a bulk payout file.
5. **`/fpo/compliance`** — member register, board meeting log, annual return reminders, CBBO reporting export.
6. **`/fpo/reports`** — aggregate realisation vs benchmark, member-wise performance, commodity mix, season comparison.

---


## 11.7 External-provider architecture (cross-cutting)

Anything that depends on a regulated, commercial or credentialed third party must be implemented behind a narrow domain interface with explicit capability detection:

- `BusinessVerificationProvider` — GST/business checks or manual-review fallback.
- `BankVerificationProvider` — account verification/penny-drop where supported.
- `PaymentProvider` — payment intent/collection/settlement/reference/webhook reconciliation.
- `MessagingProvider` — SMS/WhatsApp/push delivery and delivery receipts.
- `VoiceProvider` — TTS/IVR/voice callback where enabled.
- `WeatherProvider` — forecast/advisory source with timestamps and provenance.
- `GeocodingProvider` — licensed geocoder/Nominatim-compliant adapter with caching and rate limits.
- `FinancePartnerProvider` — referral/eligibility/status only; no credit approval or fund movement is fabricated by KrishiLink.

Every provider interface must support `available`, `degraded`, `manual_review` and `unconfigured` states. Production UI must never show a successful verification, payment, WhatsApp delivery, bank check or financing approval from a mock/test adapter. Test adapters are allowed only in tests/local demo environments and must be visibly isolated.

---
# PART 12 — LOGISTICS, STORAGE, QUALITY, PAYMENT

## 12.1 Logistics (P6, P17)

Freight estimator (distance × vehicle class × current diesel index) shown **before** any commitment. Transporter marketplace: verified transporters bid on confirmed trades; farmer/buyer picks on price + ETA + trust. Live tracking (driver app or SMS check-ins). Digital proof of delivery: photo + signature + geostamp. Return-load matching to cut cost.

## 12.2 Storage (P7, P24)

Surface the existing `storage` and `reservations` modules: find by distance/capacity/rate/type/WDRA status; availability calendar; booking with a deposit; cost calculator integrated into the sale-window advisor (Block 3 above); WDRA-linked warehouse receipt where available, which in turn unlocks pledge finance.

## 12.2A Liquidity bridge — partner integration, not assumed platform lending

The problem statement requires solving liquidity pressure, but this does **not** imply KrishiLink should lend money itself. For the core build, implement: eligibility/referral hooks, storage-linked finance discovery where a regulated partner supports it, consented data sharing, application-status tracking, disclosures and a clear handoff to the authorised partner. Keep underwriting, sanction, KFS/loan documentation, disbursal and collections with the regulated entity unless KrishiLink later obtains the necessary legal structure and approvals.

**Launch rule:** if no regulated finance partner is configured, show `Finance options coming through approved partners` or omit the action. Do not simulate credit limits, approvals, interest rates or disbursals. Liquidity Bridge is not a blocker for the core market-intelligence/transaction MVP unless a real partner contract and API are available.

## 12.3 Quality (P4, P13, P15)

`quality_specs` per crop per grade with **reference photographs** — a farmer grades by looking, not by reading. Photo capture at listing, at pickup, at delivery. Optional third-party assay booking with the result attached to the lot. Rejection handling: a rejection must cite the spec clause and attach evidence, and automatically opens a dispute if contested.

## 12.4 Payment (P18, P22)

Decide and document **one** model in `docs/payments.md`: who holds funds, under what licence, what triggers release, what happens on partial rejection. If funds are held pending delivery, that engages the RBI Payment Aggregator framework — either hold the authorisation or route through a licensed partner, and say so in plain language.

Requirements regardless of model: the full fee breakdown shown before every commitment; the payment timeline visible to both parties; the real payment reference (UTR/RRN) from the actual rail — **never a generated string**; automated reminders on overdue payments; and the on-time rate feeding the trust score.

---

# PART 13 — GRIEVANCES AND DISPUTES (P19)

Structured filing (category, trade reference, description, evidence upload, desired outcome) · auto-acknowledgement with a ticket ID within 48 hours · SLA clock visible to the user · escalation ladder (support → adjudicator → grievance officer) · neutral adjudication with both parties' evidence · partial-settlement support · outcome recorded against both parties' trust scores · **published aggregate statistics on** **`/accuracy`** (volume, median resolution time, outcomes split). Publishing adverse statistics is the trust signal (USP 7).

---

# PART 14 — NOTIFICATIONS AND LOW-BANDWIDTH CHANNELS (USP 6)

| **ChannelScope**   |                                                                                                                                                                                                             |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **In-app**         | Notification centre, read/unread, deep links.                                                                                                                                                               |
| **Push**           | PWA push for offers, price alerts, payment events.                                                                                                                                                          |
| **SMS**            | Via existing `sms_service.py`. OTP, offer received, offer expiring, payment sent, price alert. **Inbound commands**: `RATE ONION NASHIK`, `STATUS`, `ACCEPT <id>`.                                          |
| **WhatsApp**       | Business API. Daily price digest for the farmer's crops, offer cards with inline Accept/Counter/Decline, settlement receipts, support. For many users this becomes the primary interface — design for that. |
| **IVR**            | Toll-free line, language menu, keypad-driven price check and offer acceptance. Reaches feature-phone users, who are a real and currently excluded market.                                                   |
| **Voice callback** | DeHaat's proven pattern: an automated in-language voice call for high-value events (a new offer above the reserve price).                                                                                   |

Every channel respects per-channel consent, quiet hours (no SMS 21:00–07:00 except OTP), and writes to `notification_log` with delivery status.

---

# PART 15 — ACCESSIBILITY, I18N, LOW-LITERACY

## 15.1 Accessibility — WCAG 2.2 AA, verified

Every input `htmlFor`+`id` (`Field` already does this — keep it, but **invert the** **`autoComplete="off"`** **default to require an explicit value**). Every icon-only control `aria-label`. Full keyboard operability, visible focus, `Escape` closes overlays, focus returns to trigger. Skip link (already present). `role="alert"` on errors (already present in `Notice`). WAI-ARIA Tabs pattern. Charts get an accessible data-table fallback. `prefers-reduced-motion` honoured globally plus an in-app toggle. 200% font scaling without layout break. **48px minimum targets.** axe-core in CI across every route — the branch already wires `@axe-core/playwright`; extend coverage to all routes and make it blocking.

## 15.2 Language and literacy

Three complete languages at launch (en/hi/mr), CI-gated at 100% coverage per locale — no silent English fallback. Native review by a speaker **from the target region** (agricultural vocabulary is regional). Expansion path one language at a time: te, kn, ta, bn, gu, pa, or.

Localise more than page copy: error messages, validation text, empty states, toasts, SMS/WhatsApp templates, PDF documents, and API-returned market and crop names (via a server-side mapping table).

**Low-literacy mode:**

- `Listen` button on every screen — TTS via Bhashini / AI4Bharat Indic voices (the browser's default Marathi voice is not acceptable).
- Voice input on fields where speech materially reduces effort (crop/location search, free-text notes, grievance descriptions and other text entry). Do not add microphone controls to simple steppers, toggles, dates or one-tap choices where voice would increase clutter.
- Photo-first selection for crop and grade.
- Numbers and images over words wherever possible.
- A `Simple mode` toggle reducing the farmer app to four actions: **See price · Sell crop · My offers · My money.**
- Guided first-run tour with audio narration.
- Test with genuinely low-literacy users. This is the only validation that counts.

---

# PART 16 — PERFORMANCE, PWA, RENDERING

## 16.1 Budgets (CI-enforced, fail the build)

Initial JS ≤150 KB gzip · total first-load ≤400 KB excluding the scroll sequence · any image in `public/` ≤150 KB · LCP <2.5 s and INP <200 ms and CLS <0.1 on Slow-3G + 4× CPU throttle · fonts ≤90 KB.

## 16.2 Techniques

Route-level code splitting (already done — keep it) · lazy-mount `recharts` and `leaflet` at point of use · AVIF/WebP with `srcset` at 5 widths · `loading="lazy" decoding="async"` below fold · blurhash placeholders · CDN with format negotiation · preconnect to API and CDN · prefetch on link hover/focus · `saveData` path that skips the map preview, the scroll sequence and decorative imagery · virtualised long lists · Redis caching server-side.

## 16.3 PWA / offline (USP 6)

Workbox service worker: app shell precached; prices stale-while-revalidate with a visible age badge; images LRU-capped. Installable manifest with all icon sizes, splash screens, `theme-color`. **Offline lot creation** — complete the form offline, queue it, Background Sync on reconnect, with per-item pending/synced/failed status and conflict handling. Offline price viewing from cache. Honest offline banner stating what still works.

## 16.4 Rendering strategy

Move to SSR/SSG for public routes (`/`, `/prices`, `/prices/:crop`, `/mandis`, `/mandis/:slug`, `/buyers`, legal, help). These are the SEO surfaces and the ones a farmer on a slow connection hits first. Authenticated dashboards remain client-rendered. Either migrate to a framework with first-class SSR or add a pre-render step for the static subset — decide and record in `docs/DECISIONS.md`.

---

# PART 17 — SECURITY AND COMPLIANCE

**Headers (currently absent —** **`vercel.json`** **sets none):** strict CSP with nonces and no `unsafe-inline` · HSTS with preload · `X-Content-Type-Options: nosniff` · `Referrer-Policy: strict-origin-when-cross-origin` · `Permissions-Policy` denying unused APIs (allow `geolocation=(self)`) · `frame-ancestors 'none'`. Target securityheaders.com **grade A**.

**Application:** refresh token httpOnly/Secure/SameSite=Strict with rotation and reuse detection · access token in memory (already done) · CSRF protection for the cookie flow · rate limiting and lockout on all auth endpoints · idempotency on all money-moving endpoints (already partially done) · server-side authorisation on every route, never relying on client role checks · input validation with shared schemas · parameterised queries only · signed URLs for uploads with type and size limits and malware scanning · PII encrypted at rest · secrets in a manager, rotated, never in git.

**Compliance:** DPDP Act 2023 + final DPDP Rules 2025, tracked against their staggered commencement dates (notice/consent/rights/security/breach/grievance obligations as applicable; DPO where legally required, otherwise designated privacy contact) · Consumer Protection (E-Commerce) Rules 2020 (seller details, grievance officer, no unfair trade practice) · IT Rules 2021 grievance officer and timelines · GST invoicing where applicable · RBI PA/PG framework if funds are held · APMC/state marketing law review per state of operation · Legal Metrology for weighment claims.

**Process:** Dependabot + `npm audit` + `pip-audit` gating CI · SAST · `security.txt` and a disclosure policy · penetration test before handling real money · audit logging of every state change · incident response runbook.

---

# PART 18 — TESTING, CI/CD, OBSERVABILITY

## 18.1 Test suite

Unit (Vitest + RTL) for every hook, lib and component — extend the existing `produce.test.js` / `session.test.js`. Integration for every form: validation, error, success, keyboard. E2E (Playwright, already configured) for: farmer register → OTP → location → list lot → receive offer → accept → trade room → settlement; buyer register → requirement → discover → offer → trade; FPO member → pool → publish → payout; and the public path home → rate lookup → mandi detail → sell handoff.

**Two contract tests that would have caught most historical bugs — make both blocking:**

- **Route contract:** crawl every `<Link>`/`<NavLink>` in the app and assert none resolves to the 404 handler.
- **Query-param contract:** assert that every parameter any link emits is consumed by its destination component. (`?crop=` ignored by `PricesPage` and `?role=` ignored by `RegisterPage` were both this class of bug.)

Plus: visual regression on home/prices/dashboard at 360/768/1440 in all three languages · axe on every route · API contract tests against the OpenAPI schema · load test on the price endpoints · **coverage gates: 80% overall, 100% on money arithmetic, unit conversion and authorisation.**

## 18.2 CI/CD

On every PR: lint (oxlint + **Prettier check** — Part 1.3 R2) · typecheck · unit + integration · build · bundle-size diff comment · Lighthouse CI against the Part 16.1 budgets · axe · E2E on the critical journeys · dependency audit. Staging deploy on merge with smoke tests; production behind manual approval with automated rollback on error-rate regression. Database migrations reviewed and reversible.

## 18.3 Observability

Sentry (or equivalent) with source maps, releases, user context — **only then is "our team has been notified" a true statement** (it currently is not). Structured backend logging with request IDs propagated to the frontend via the `request_id` already returned by `lib/http.js`. Uptime and price-sync health checks with alerting. RUM `web-vitals` segmented by device class, connection type and region. Full funnel instrumentation: landing → rate lookup → CTA → register step-by-step → first listing → first offer → first settlement, with per-field form-abandonment tracking. Feature flags for gradual rollout and instant revert. A weekly dashboard with a named owner.

---

# PART 19 — CONTENT, COPY AND RESEARCH OPERATIONS

- `docs/content-style-guide.md`: banned terms with approved replacements · number formatting (Indian grouping, always with unit) · dates (`16 Sep`, never `16/09/2026`) · currency (`₹` prefix, `/qtl` suffix, tabular) · tone.
- Reading level ≤6th standard on all farmer-facing copy, tool-verified.
- A standing panel of 20+ farmers across ≥3 regions and crop types, paid for their time. Five test every significant change before release.
- Weekly review of support-call transcripts; top three confusions become issues.
- Quarterly field visits — observe use in a field, not an office.
- Public changelog in farmer language.

---


---

# PART 19A — MULTI-ROLE PROFESSIONAL REVIEW: WHAT EACH DISCIPLINE MUST BE ABLE TO SIGN OFF

> This part exists because a product can look complete while still being unshippable to engineers, operators, auditors, procurement teams or end users. Every role below receives an explicit sign-off gate. “The AI implemented it” is never evidence.

## 19A.1 Product manager / product owner

The PM must be able to answer, with evidence:

- Which problem-statement clause does this feature solve?
- Which persona uses it, at what moment, and what decision/action does it improve?
- What is the success metric, current baseline, target and measurement method?
- Is this **Core**, **Expansion**, **Partner-dependent**, or **Government-enterprise** scope?
- What happens if the upstream data/provider is unavailable?
- What is intentionally NOT included?
- What feature can be removed if farmer comprehension declines?

Maintain `docs/product/capability-register.md` with columns: capability, problem clause, persona, tier, owner, dependencies, metric, launch gate, current status, evidence link.

## 19A.2 Solution / software architect

Before major implementation the architect must approve:

- bounded contexts and ownership boundaries;
- trade/offer/payment/dispute state machines;
- sync vs async communication decisions;
- API versioning and compatibility strategy;
- provider interfaces and failure isolation;
- transactional integrity across money/trade state transitions;
- geospatial and time-series data strategy;
- offline conflict-resolution model;
- multi-tenancy strategy for future government/enterprise deployments;
- build-vs-buy decisions and vendor exit strategy;
- scaling assumptions, bottlenecks and cost model;
- migration/rollback plan.

Every major decision becomes an ADR. No “temporary” cross-domain database writes without an ADR and removal date.

## 19A.3 Frontend engineer

Frontend sign-off requires:

- mobile-first farmer path validated at 360 px and low-end Android performance profile;
- all async states: initial/loading/refreshing/empty/error/partial/stale/offline/success;
- deep links and back-button behavior correct;
- forms preserve drafts and never lose entered data on transient failures;
- query parameters are typed and contract-tested;
- no business-critical arithmetic duplicated ad hoc in components;
- no provider secrets or privileged rules shipped to the browser;
- charts have readable summaries and accessible tables;
- map is an enhancement, never the sole way to discover a nearby outlet;
- route-level error boundaries and retry behavior exist;
- translation length expansion is tested;
- shared-device privacy is considered: sensitive balances and documents are not left visible after logout/session expiry;
- optimistic UI is used only where a failed operation can be safely reversed; offer acceptance, payment, verification and irreversible state transitions wait for server acknowledgement.

## 19A.4 Backend engineer

Backend sign-off requires:

- OpenAPI is the contract and generated/validated in CI;
- consistent error envelope (prefer RFC 9457 Problem Details semantics or equivalent documented schema);
- cursor pagination for unbounded feeds;
- idempotency for creates/financial/state-transition operations;
- explicit timeouts, retry policies, circuit breakers and provider health states;
- transactional outbox for side effects that must follow committed state changes (notifications, analytics events, provider dispatch);
- domain state machines prevent illegal transitions even if the frontend is bypassed;
- authorization is object- and action-level, not only role-level;
- rate limits distinguish login abuse, search scraping, offer spam and provider quotas;
- all monetary calculations are authoritative server-side;
- all timestamps are UTC internally and localized only at presentation boundaries;
- every mutation emits an audit event with actor, request/correlation ID and before/after or semantic delta as appropriate;
- long-running imports, exports, syncs and notifications run in jobs with retry/dead-letter semantics rather than blocking request threads.

## 19A.5 Database engineer / DBA

DBA sign-off requires:

- ERD plus ownership and retention classification for every table;
- PostGIS indexes and query plans verified for nearby search at target scale;
- price observations partitioned or otherwise lifecycle-managed once volume justifies it;
- uniqueness and natural-key rules prevent duplicate market/price ingestion;
- immutable ledger-like records for legally/audit-relevant transitions; corrections append rather than silently rewrite history where required;
- backups encrypted and restore-tested, not merely configured;
- point-in-time recovery where supported;
- migration scripts are forward and rollback/recovery reviewed;
- destructive migrations use expand/migrate/contract deployment patterns;
- production access is least privilege and audited;
- PII and transactional analytics are separated logically enough to support deletion/retention obligations without destroying required financial/audit records;
- read replicas/materialized views are considered for analytics before OLTP queries are burdened.

## 19A.6 Data engineer

Data engineering must own a **source registry** for Agmarknet/data.gov.in, APMC lists, eNAM references, LGD, WDRA, state sources, weather and every other feed. Each source records:

`source_id · owner · licence/terms · retrieval method · schema version · expected cadence · geographic coverage · freshness SLA · known gaps · unit conventions · dedupe key · parser version · last success · last failure · quality score`.

Every ingestion pipeline must be reproducible, idempotent and observable. Raw source snapshots or hashes are retained when licensing permits, normalized records preserve lineage, schema drift alerts exist, and silent coercion is prohibited.

## 19A.7 ML / forecasting engineer

No model ships because its chart “looks right.” Required artefacts:

- model card per model/version;
- training-data window and lineage;
- leakage review;
- walk-forward backtest;
- naive and seasonal baseline comparison;
- MAE/MAPE or appropriate robust metric plus interval coverage/calibration;
- performance by crop, market/district, season and data-density bucket;
- minimum-data threshold;
- out-of-distribution and missing-source behavior;
- abstention rate;
- drift monitoring;
- shadow/canary deployment before farmer-facing recommendation;
- rollback switch to “data only, no recommendation”;
- human-readable explanation of inputs and uncertainty.

The model must beat a declared baseline consistently enough for the target slice before it is allowed to generate “hold/sell” guidance. If it does not, ship trend intelligence without prescriptive recommendation.

## 19A.8 QA / test engineer

QA owns risk-based coverage, not just line coverage. The test matrix must include:

- happy path;
- permission denial;
- stale price;
- upstream outage;
- duplicated request;
- slow request;
- partial provider success;
- offline-to-online sync;
- expired session mid-transaction;
- two devices editing the same object;
- race between offer acceptance/expiry/withdrawal;
- duplicate payment webhook;
- invalid unit conversion;
- timezone/date boundary;
- language switch mid-flow;
- 200% text zoom;
- keyboard/screen-reader path;
- low-memory/slow-device browser behavior;
- migration from old user data;
- malicious upload;
- unauthorized object ID access;
- rollback after a failed release.

Maintain a traceability matrix: problem requirement → acceptance criterion → automated/manual test → evidence.

## 19A.9 Debugger / production support engineer

A support engineer must be able to diagnose a failed transaction without database guessing. Every user-visible error that reaches support has a non-sensitive reference ID. Required operational tools:

- request/correlation ID end-to-end;
- provider request ID where available;
- searchable structured logs;
- state-transition timeline;
- job/retry/dead-letter status;
- replay-safe admin actions;
- “why is this price shown?” provenance inspector;
- “why did this match rank?” explanation inspector;
- user/session/device metadata only to the extent permitted by privacy policy;
- runbooks for top failure modes;
- feature flag and kill switch dashboard;
- safe impersonation/support mode only if legally approved, heavily audited and incapable of performing sensitive actions without re-authorization.

## 19A.10 DevOps / platform / SRE

Production readiness requires SLOs and failure budgets, not merely deployment success.

Baseline service targets (refine after load testing):

| Service area | Initial SLO target |
| --- | --- |
| Auth and core transaction API availability | 99.9% monthly |
| Public price lookup API availability | 99.9% monthly, graceful stale-data fallback |
| P95 core API latency | <500 ms excluding external-provider latency |
| P95 nearby outlet query | <800 ms at launch dataset scale |
| Critical notification dispatch initiation | <60 s from committed event |
| Price ingestion alerting | alert when expected source window is missed |
| RPO | ≤15 min for transaction data target; explicitly document actual architecture |
| RTO | ≤60 min target for critical transaction service; test at least twice yearly |

Required: IaC, reproducible environments, secrets manager, immutable deployment artefacts, blue/green or canary where practical, database backup/restore drill, documented DR region/strategy, dependency health dashboard, capacity tests, cost alerts and release rollback procedure.

## 19A.11 Security engineer / fraud & abuse analyst

Threat modelling must include both cyber attacks and marketplace abuse:

- account takeover / OTP abuse;
- phone-number enumeration;
- fake farmer/buyer/FPO identities;
- buyer non-payment;
- fake payment screenshots/UTRs;
- GPS spoofing;
- false quality claims;
- collusive bidding;
- offer spam;
- price manipulation attempts;
- scraping/data exfiltration;
- malicious file uploads;
- IDOR/BOLA;
- admin privilege abuse;
- webhook spoofing/replay;
- referral/notification abuse;
- trust-score gaming;
- denial of service against price lookup during peak harvest periods.

Create `docs/security/threat-model.md`, abuse controls, fraud-review queue, audit evidence and incident playbooks. High-risk actions require step-up verification proportional to risk rather than friction everywhere.

## 19A.12 Privacy / legal / compliance

Maintain a processing inventory rather than treating Privacy Policy text as compliance. For every personal-data field record purpose, necessity, source, access roles, retention, processors, deletion rule and consent/legal basis as applicable. Keep policy versioning and user request workflows. Never collect land, identity, bank or exact GPS data merely because it may be useful later.

For September 2026 India readiness, track the DPDP Act 2023 and final DPDP Rules 2025 with their staggered commencement in `docs/compliance-matrix.md`; legal counsel owns conclusions about which duties apply on a given deployment date. Do not make Astra invent legal conclusions.

## 19A.13 Accessibility specialist

Target WCAG 2.2 AA for product quality while also producing a **GIGW 3.0 compliance matrix** for government deployments. Manual testing must include TalkBack on Android, keyboard-only desktop, 200% zoom, focus order, error recovery, accessible documents/PDFs, captions/transcripts, reduced motion and colour-independent status. Automated axe passing is necessary but not sufficient.

## 19A.14 Localization / content designer

Translation is not string substitution. Maintain agricultural terminology glossary by language/region; test market names/crop aliases spoken aloud; localize units, date phrasing and phone/SMS content; avoid bureaucratic vocabulary on farmer surfaces. Provide audio only where it reduces comprehension burden. Every important warning has an actionable next step.

## 19A.15 Customer support / operations

Support needs an operations console, not database access. It must expose user-visible state, timeline, documents allowed for support, provider status, grievance SLA, resend/retry where safe, escalation and notes. Define L1/L2/L3 ownership and escalation. Track contact reason, first-response time, resolution time, reopen rate and top recurring confusion. Every recurring support issue should feed product backlog.

---

# PART 19B — USER AND MARKETPLACE PERSPECTIVE REVIEW

## 19B.1 Farmer acceptance: the product must work for more than the ideal smartphone user

Design/test at least these scenarios:

1. returning smartphone farmer with saved crop/location;
2. first-time farmer with no email and weak literacy;
3. shared-family-phone user who needs privacy and easy account switching/logout;
4. intermittent-network user whose GPS works but data connection does not;
5. user who denies GPS and manually selects village/taluka/district;
6. user whose crop/variety has sparse price data;
7. user who wants to compare options but does not want to list produce;
8. farmer selling a partial quantity;
9. farmer acting through an FPO rather than individually;
10. assisted user calling support/IVR or working through a field agent.

### Farmer “five-second test”

After login a farmer should be able to identify, without scrolling through dense analytics:

- **What is my crop's latest reported price near me?**
- **Where was that price reported and when?**
- **Is there a meaningfully better nearby option after transport/fees?**
- **Do I have anything urgent to respond to?**
- **What is the simplest next action?**

### Farmer trust requirements

- source + reported date on price;
- no guaranteed forecast language;
- visible fee before commitment;
- buyer payment behavior explained in plain language;
- clear cancellation/rejection consequences;
- support reachable without hunting through menus;
- confirmation before irreversible actions;
- paper/PDF/SMS record where practical;
- no dark patterns pushing the farmer toward a platform transaction when an external option has better estimated net realization.

That last rule is strategic: **farmer trust outranks transaction capture.** If KrishiLink's own channel is not best, the comparison must still show that truth.

## 19B.2 Buyer acceptance

Buyers care about dependable procurement, not decorative dashboards. The buyer product must answer:

- What volume do I still need by date and delivery point?
- Which supply is genuinely available and what quality evidence exists?
- What is my landed cost, not merely farm-gate price?
- Can I combine multiple lots without manually reconciling them?
- What is late/rejection/dispute risk?
- What documents will finance, tax and audit teams need?
- Can I repeat a successful supplier relationship?

Add buyer enterprise features where justified: saved procurement templates, approval thresholds, team roles, maker-checker for high-value offers, CSV/API import/export, downloadable procurement trail, invoice/quality-document bundle, delivery SLAs and supplier scorecards. Do not expose farmer personal data beyond what the transaction requires.

## 19B.3 FPO acceptance

FPO product success is daily operational throughput. Required capabilities include:

- member roster/import;
- expected harvest calendar;
- intake/weighment/grade ledger;
- printable/local-language receipt;
- pooling eligibility and exceptions;
- contribution traceability;
- member-wise settlement split;
- service-charge transparency;
- payout reconciliation;
- correction workflow with audit trail;
- offline/poor-connectivity intake option;
- role separation for operator, accountant, manager and authorized signatory;
- reports that reconcile to totals, never independent dashboard arithmetic.

The FPO dashboard's first question is **“what needs to be received, pooled, sold or paid today?”** rather than generic analytics.

## 19B.4 Field agent / support-assisted mode

Government and rural deployments often involve assisted service. Add an optional, deployment-configurable field-agent role with strict safeguards:

- agent can help create/update drafts with explicit farmer confirmation;
- agent cannot accept offers, change bank details or withdraw funds on behalf of a farmer without a separately authorized workflow;
- every assisted action records actor + beneficiary;
- farmer receives SMS/in-app receipt of critical assisted changes;
- agent performance is auditable and fraud-monitored.

Do not enable this role by default in consumer deployment.

---

# PART 19C — GOVERNMENT / PSU / INSTITUTIONAL PROCUREMENT READINESS

> Government-readiness is a deployment profile, not a reason to make the farmer UI bureaucratic.

## 19C.1 Standards and audit profile

For a government-owned or government-procured deployment, prepare a dedicated compliance workstream for:

- GIGW 3.0 conformity and compliance matrix;
- WCAG 2.2 AA product target while satisfying applicable GIGW accessibility checks;
- STQC Website Quality / GIGW certification path where required by the procuring entity;
- security audit and clearance from NIC/STQC/STQC-empanelled/CERT-In-empanelled auditor as applicable to the deployment;
- CERT-In directions/current advisories tracked in the security compliance matrix;
- ISO 27001-aligned ISMS controls where contractually required;
- OWASP ASVS-based application verification;
- government-approved/acceptable hosting and data-residency requirements defined by the specific RFP, including evaluation of GI Cloud/MeghRaj options where relevant;
- accessible documents and multilingual Unicode content;
- records retention, archival and disposal rules specified by the procuring department.

Never stamp “Government compliant” globally. Produce evidence per requirement and per deployment.

## 19C.2 Procurement package

Create `/docs/procurement/` containing:

- executive solution overview;
- problem-to-capability traceability;
- architecture diagrams (context/container/component/deployment/data-flow);
- BoM and third-party dependency register;
- licence/SBOM register;
- implementation plan and milestones;
- assumptions/dependencies/exclusions;
- SLA/SLO schedule;
- support and escalation matrix;
- DR/BCP plan;
- security controls and latest audit status;
- privacy/data-flow inventory;
- data migration plan;
- interoperability/API catalogue;
- exit-management and data-export plan;
- training and knowledge-transfer plan;
- UAT plan;
- acceptance-test matrix;
- warranty/AMC/O&M scope template;
- RACI between department, KrishiLink team and external providers;
- change-request/governance process;
- configurable branding/localization plan.

## 19C.3 Anti-lock-in requirements

A government buyer must be able to exit without losing its data. Therefore:

- export core transactional and master data in documented open formats;
- export uploaded documents with a manifest;
- provide API documentation and schema definitions;
- keep provider adapters replaceable;
- avoid irreversible cloud-proprietary data models in the domain layer;
- document encryption/key ownership;
- define deletion/return of data at contract end;
- if contract requires source-code escrow/transfer, architecture and build documentation must make independent deployment feasible.

## 19C.4 Government administrator / regulator dashboards

Create a separately permissioned oversight surface—never expose raw farmer PII by default. Useful aggregated views:

- market/outlet coverage and verification backlog;
- price-source freshness and failures;
- district adoption and activity;
- transaction completion funnel;
- median settlement time;
- grievance volumes/SLA compliance;
- FPO participation;
- price realization comparison methodology;
- provider/system uptime;
- suspicious/fraud-review counts;
- data quality issues.

Every aggregate metric defines numerator, denominator, time window, exclusions and update cadence. Suppression thresholds protect privacy for very small cohorts.

## 19C.5 Integration posture

Where a government department requires integration with public digital infrastructure, use provider/adapter boundaries and obtain the required authorization. Potential integrations such as DigiLocker, authorized identity services, API Setu or language infrastructure are **deployment-specific capabilities**, not assumptions in the core consumer product.

---

# PART 19D — INVESTOR, JUDGE AND EXECUTIVE DILIGENCE

## 19D.1 What an investor will ask

The product must instrument and be able to answer:

- acquisition: how farmers discover the product and cost per activated user;
- activation: time to first useful price result, not merely registration;
- retention: weekly/monthly returning farmers by crop/region;
- marketplace liquidity: lots receiving ≥1 qualified offer within target time;
- buyer fill rate and repeat purchase rate;
- farmer repeat listing/trade rate;
- transaction completion rate;
- median time from listing → offer → agreement → settlement;
- dispute/rejection rate;
- realized net price vs comparable benchmark, with methodology caveats;
- gross merchandise value only alongside actual transaction count and concentration;
- revenue by stream and gross margin;
- variable cost per active farmer / trade / notification / provider call;
- contribution margin per completed trade or account cohort;
- concentration risk by crop, geography, buyer and provider;
- CAC payback assumptions only when enough real data exists.

Do not optimize vanity registrations at the expense of repeat useful sessions or completed reliable trades.

## 19D.2 Business model clarity

Maintain `docs/business-model.md` with configurable, transparent options rather than hidden monetization:

- transaction/facilitation fee where legally and commercially appropriate;
- buyer/FPO SaaS tiers for workflow tooling;
- logistics/storage referral or service fee only when disclosed;
- government/enterprise licence + implementation + O&M model;
- premium data/analytics only using lawful, appropriately aggregated data and never selling personal farmer data.

For each stream document payer, trigger, rate basis, taxes, refund/cancellation impact, gross margin drivers and regulatory dependency.

## 19D.3 Judge/demo readiness

A hackathon/competition demo must demonstrate product truth without pretending a sandbox is production.

Create a **Demo Mode** only in a separate environment/domain/build configuration:

- banner: `DEMO — synthetic data`; 
- deterministic personas and journeys;
- synthetic prices/offers clearly marked;
- no real SMS/payment/provider actions unless explicitly connected;
- one-click reset;
- seeded edge cases for judge exploration;
- architecture/data-provenance view available to technical judges;
- no demo-only code path allowed to weaken production authorization.

Recommended 6-minute judge story:

1. farmer asks “what is my onion worth near me?”;
2. location-aware official/reported market comparison appears;
3. net-realization comparison shows why headline price alone is insufficient;
4. farmer creates a lot with minimal input;
5. buyer/FPO side shows aggregation/demand;
6. Trade Room shows quality/logistics/payment traceability;
7. close with measurable system outcomes, honesty about current integrations and roadmap.

Judges should leave understanding **why KrishiLink is differentiated**, not just how many screens it has.

## 19D.4 Executive dashboard / board metrics

Board-level dashboard is limited to decision metrics: farmer activation/retention, marketplace liquidity, buyer fill rate, completed trades, settlement reliability, disputes, contribution margin, service availability, critical data-source health, fraud loss, and rollout progress. It must not become a screenshot wall of vanity statistics.

---

# PART 19E — MARKETPLACE TRUST, SAFETY AND DATA GOVERNANCE

## 19E.1 Trust score must resist gaming

A raw percentage is misleading at small sample sizes. TrustScore must display sample size and use a documented confidence-aware method (for example conservative/Bayesian shrinkage) rather than ranking a buyer with 1/1 on-time trade above one with 490/500. Separate dimensions:

- identity/business verification state;
- completed trades;
- on-time payment;
- median payment delay;
- quality rejection rate;
- cancellation/no-show rate;
- dispute rate/outcomes;
- platform tenure;
- recent adverse events.

Never collapse identity verification and behavioral reliability into one unexplained badge.

## 19E.2 Market integrity controls

Add rules/monitoring for anomalous coordinated bidding, self-dealing, duplicate accounts, repeated last-minute cancellations, suspicious price spikes, mass scraping and abusive messaging. Automated controls may flag/restrict but high-impact account sanctions require review/appeal workflows unless immediate containment is necessary for security.

## 19E.3 Data classification

Classify at minimum:

- Public: published market/outlet information intended for public display;
- Internal: operational metrics/configuration;
- Confidential: contracts, provider credentials, internal reviews;
- Personal: user identity/contact/location/activity;
- Highly restricted: bank details, identity documents, payment/verification evidence, security secrets.

Map encryption, access, logging, retention and export rules to classification. Exact GPS must not be exposed to buyers when district/taluka or pickup point is sufficient.

## 19E.4 Data-quality scoring

Every price/outlet/weather/quality record shown in decision support gets machine-readable quality metadata where relevant: source, reported_at, fetched_at, verification state, geocode confidence, transformation/parser version and stale threshold. UI simplifies this for farmers but support/admin can inspect full provenance.

---

# PART 19F — ARCHITECTURE COMPLETENESS AND DOMAIN STATE MACHINES

## 19F.1 Core bounded contexts

At minimum document boundaries for:

1. Identity & Access
2. Geography & Outlets
3. Crops / Quality Catalogue
4. Market Intelligence / Prices
5. Listings / Lots
6. Matching / Requirements
7. Offers / Negotiation
8. Trades / Fulfilment
9. Logistics
10. Storage
11. Payments / Settlement Tracking
12. FPO Aggregation / Payout Allocation
13. Trust / Verification
14. Disputes / Grievances
15. Notifications
16. Reporting / Metrics
17. Admin / Moderation / Data Operations

A module may share one physical database initially, but domain ownership and mutation APIs remain explicit.

## 19F.2 Required state machines

Document and test illegal transitions for:

- Lot: draft → published → partially_matched/active → reserved → sold/expired/withdrawn;
- Offer: draft → submitted → countered → accepted/declined/expired/withdrawn;
- Trade: agreed → quality_pending → weighment_pending → dispatch_ready → in_transit → delivered → invoiced → settlement_pending → paid → closed; with explicit cancelled/disputed branches;
- Storage booking;
- verification case;
- grievance;
- provider payment/notification attempt.

Names may adapt to existing code, but the transition graph must exist and server code must enforce it.

## 19F.3 Event reliability

Use a transactional outbox/event log for side effects triggered by committed domain state changes. Consumers are idempotent. Failed jobs enter retry with bounded exponential backoff and eventually dead-letter/manual review. This prevents “trade accepted but notification never sent” and duplicate webhook side effects.

## 19F.4 API lifecycle

- version public APIs;
- publish OpenAPI;
- compatibility test frontend against backend schema;
- deprecation window before breaking changes;
- documented pagination/filter/sort conventions;
- consistent request IDs;
- webhook signatures, timestamps and replay protection;
- provider callbacks stored raw or hashed/auditable as appropriate before normalization;
- never expose internal DB IDs when a safer opaque public identifier is preferable.

---

# PART 19G — RELEASE, OPERATIONS, DR AND COST CONTROL

## 19G.1 Environment model

Use at least: local → test/CI → staging/UAT → production. Demo is separate from production and cannot share credentials or writable production data. Staging uses non-production provider credentials wherever available.

## 19G.2 Release gates

No production release if any applies:

- unresolved Sev-1/Sev-2 defect in changed journey;
- irreversible migration without restore/recovery test;
- money/unit authorization critical tests failing;
- secrets detected;
- critical/high exploitable security finding without approved exception;
- accessibility blocker on a critical farmer journey;
- provider integration returning mock success;
- price source/provenance absent in a price UI;
- observability absent for newly introduced critical job/provider.

## 19G.3 Incident severity

Define Sev-1 through Sev-4. Examples:

- Sev-1: wrong money calculation, unauthorized data disclosure, systemic duplicate settlements, core platform outage during critical market window;
- Sev-2: major role unable to transact, price pipeline misleadingly reports freshness, widespread notification/payment tracking failure;
- Sev-3: feature degradation with workaround;
- Sev-4: cosmetic/localized issue.

Each incident gets owner, communication cadence, mitigation, root cause and corrective actions. Blameless postmortem does not mean accountability-free follow-up.

## 19G.4 Cost engineering

Track cost per:

- 1,000 price lookups;
- active farmer/month;
- listed lot;
- completed trade;
- SMS/WhatsApp/voice notification;
- map/geocode call;
- GB storage and document scan;
- forecast batch;
- government tenant/region if multi-tenant.

Set budget alarms and provider quotas. A feature that costs more than the value it produces must degrade gracefully or move to a paid/limited path rather than silently causing runaway cloud/provider spend.

## 19G.5 Business continuity

Document manual fallback for critical operations when the platform or a provider is unavailable: record an agreed trade/payment reference, preserve evidence, reconcile later. Business continuity must not create an unaudited shadow process.

---

# PART 19H — CAPABILITY TIERS: STOP THE MASTER SPEC FROM BECOMING AN UNFINISHABLE LOOP

Every capability is tagged with one of four tiers.

### Tier 1 — Core launch / pilot blockers

Must work end-to-end with real or truthful unavailable states:

- auth/session/roles;
- structured location;
- latest official/reported price lookup + provenance;
- nearby substantiated markets/outlets;
- farmer dashboard core viewport;
- lot creation;
- buyer requirements/discovery basics;
- offer/counter/accept;
- Trade Room core timeline;
- FPO member/intake/pooling basics;
- grievance path;
- audit logging;
- notifications needed for core transactions;
- security/accessibility/performance baselines;
- support/admin needed to operate the pilot.

### Tier 2 — Differentiating product intelligence

- channel net-realization calculator;
- trustworthy sale-window advisor after validation gate;
- trust ledger after sufficient transaction sample exists;
- storage booking;
- price alerts;
- advanced buyer procurement;
- FPO settlement/reporting;
- realisation report;
- offline/PWA enhancements.

### Tier 3 — Partner-dependent / regulated expansion

- money movement/escrow model;
- lending/liquidity bridge;
- penny-drop/GST/business verification where provider access is required;
- WhatsApp/IVR integrations requiring approval;
- third-party assays;
- transporter marketplace/live tracking;
- government identity/document integrations.

The product may be production-grade without a Tier 3 provider being commercially activated if the interface, truthful state and operational fallback are complete.

### Tier 4 — Government/enterprise rollout profile

- GIGW/STQC/certification evidence;
- tenant/jurisdiction configuration if required;
- government MIS/oversight dashboard;
- procurement documentation;
- contract-specific hosting/security/DR;
- department integrations;
- source escrow/exit obligations if contracted.

**Definition of Done is evaluated per intended release profile, not as “every future feature in all four tiers must be commercially live.”**


# PART 20 — EXECUTION SEQUENCE

> Each task is a self-contained prompt. Complete in order. A task is done when its acceptance criteria pass, not when it compiles.

## PHASE 0 — Architecture, baseline and rollback point (mandatory before Phase A)

**0.1 Create a clean baseline.** Run and record current frontend/backend tests, build output, bundle sizes, Lighthouse/Web Vitals where available, route inventory, database migration head and API schema. Tag/commit this state so every later phase is reversible.

**0.2 Decide the public rendering strategy now.** Compare: (A) keep the existing React/Vite application and add robust pre-render/SSR for public acquisition routes, versus (B) migrate only the public shell (or whole frontend) to a first-class SSR framework. Default to **preserving the existing stack** unless measured SEO, routing or performance requirements cannot be met cleanly. Record the ADR in `docs/DECISIONS.md`, including migration cost, test impact and rollback. Do **not** build dozens of public pages and postpone this decision to Phase G.

**0.3 Inventory external dependencies.** Create `docs/provider-matrix.md` listing each third-party capability, credentials currently available, sandbox/production status, regulatory/commercial dependency, interface name and honest fallback state.

**0.4 Data-language audit.** Identify every location where the product says `live`, `verified`, `guaranteed`, `all`, `every`, or uses an unsourced number. Create regression tests/lint/content checks for misleading claims where practical.

**Phase 0 acceptance:** architecture ADR approved; baseline tests/build recorded; rollback tag exists; provider matrix exists; no implementation phase starts with an unresolved frontend-rendering strategy.

**CHECKPOINT 0:** tests green → commit/tag → only then start Phase A.

## PHASE A — Foundation (repair the regression)

**A1. Reformat the entire codebase.** Add Prettier (100 cols, single quotes, trailing commas) and `prettier-check` to CI. Reformat every file in `frontend/src`. `LandingPage.jsx`, `RegisterPage.jsx`, `SellPage.jsx`, `BuyerDashboard.jsx`, `FPODashboard.jsx`, `RateLookup.jsx`, `Navbar.jsx`, `Experience.jsx` and `http.js` are currently authored in minified style and must be expanded to one statement per line with meaningful whitespace and section comments. *Accept:* no line exceeds 120 characters; `npm run format:check` passes in CI; a reviewer can diff any component.

**A2. Build the design system.** Implement Part 5.2 tokens as `src/styles/tokens.css`. Delete `index.css` and `styles/experience.css` after migrating every rule. Add a lint rule banning raw hex outside tokens. Set up Storybook. *Accept:* zero raw colour literals in components; contrast check passes for every token pair in use; Storybook builds.

**A3. Build the component library.** Every primitive in Part 5.3, each with all states, each documented in Storybook, each axe-clean. Invert `Field`'s `autoComplete` default so it must be supplied explicitly. *Accept:* every component has a story for default/loading/error/empty/disabled; axe passes on the Storybook build.

**A4. Fix** **`index.html`** **and add SEO/PWA scaffolding.** Meta description, `theme-color`, canonical, `og:`/`twitter:` with a generated image, `hreflang`, `manifest.webmanifest`, `<noscript>` with the support phone number, per-route meta via a `<Head>` helper. *Accept:* Lighthouse SEO ≥95; the app is installable.

**A5. Security headers and deployment hardening.** Part 17. *Accept:* securityheaders.com grade A.

**CHECKPOINT — PHASE A:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE B — Data foundation

**B1. Geography tables and API.** `states`/`districts`/`talukas` seeded from LGD with English + Hindi + Marathi names and centroids. `/api/v1/geo/states|districts|talukas|reverse`. *Accept:* reverse geocoding returns the correct district for 20 spot-checked coordinates across 8 states.

**B2. The outlets dataset.** Implement Part 8.5's 8-layer pipeline as an idempotent `seed_outlets.py`. Migrate `Market` → `outlets` preserving existing rows. Build the admin review queue for unverified geocodes. *Accept:* target ≥3,000 substantiated outlet records nationally; 100% of the 482 APMC rows; ≥80% with verified coordinates; every published outlet has LGD-resolved state/district plus provenance/confidence; the coverage figure is computed from the database and rendered on `/about`.

**B3. Delete the 3-city geocoding dictionary.** Replace `auth/service.py`'s `{"Nashik","Pune","Mumbai"}` lookup with resolution against the geography tables. Write a migration that re-geocodes every existing user and flags ambiguous rows for confirmation on next login. *Accept:* no user has default-Pune coordinates unless they are in Pune; proximity queries return correct results for a user in Ratnagiri.

**B4. Crop registry.** `crops` + `crop_varieties` + `quality_specs` tables with names in three languages, aliases, Agmarknet mappings, reference images per grade. Delete the `CROPS` array from `lib/produce.js`; every surface reads the API. Expand from 9 crops to the full set the Agmarknet feed returns. *Accept:* `grep -rn "'Onion', 'Tomato'" frontend/src/` returns nothing; every crop shown anywhere is listable; language switch translates crop names everywhere.

**B5. Price pipeline.** Part 8.6: scheduler, `price_observations`, Redis cache, freshness semantics, health endpoint, alerting. Key server-side only. *Accept:* the key appears in no frontend bundle (`grep` the build output); a market price is never displayed without its real `price_date` and source/provenance; killing the upstream API produces an honest error, never sample data.

**CHECKPOINT — PHASE B:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE C — Location and auth

**C1.** **`useLocation()`** **hook +** **`CascadingLocationPicker`****.** Part 8.4. Permission-aware, gesture-triggered, cached, with manual fallback. *Accept:* no browser permission prompt fires without a user gesture; denial path is fully usable.

**C2. Replace every free-text location input** in Register and Sell with the picker; persist `state_id`/`district_id`/`taluka_id`/`lat`/`lng`. *Accept:* no free-text field is the primary location input anywhere.

**C3. Post-login location anchoring.** The "Show mandis near you?" card; on grant, the whole dashboard re-anchors. *Accept:* a new farmer goes from login to seeing their five nearest mandis with the latest available official prices in one tap.

**C4. OTP authentication.** Backend service + rate limits + the 6-box `OtpInput` with Web OTP API. Make OTP the primary login and registration path; password optional for farmers. *Accept:* a farmer registers with only a phone number and an OTP; `+91 98765 43210`, `098765 43210` and `9876543210` all resolve to one account.

**C5. Real verification.** Independent `is_verified_*` flags, GSTIN checksum + configured business-verification provider/manual review, configured bank-verification provider (penny-drop where supported), admin review queue, badges that name exactly what was verified and by which workflow. Remove the word "verified" wherever nothing was verified. *Accept:* no badge renders without a passed check behind it.

**C6. Consent records + legal pages.** Part 7.3 content in three languages, versioned, with consent stored against the version. *Accept:* a user can view, export and withdraw every consent; legal review signed off.

**C7. Role-scope the remaining routes.** `/offers`, `/transactions`, `/trades/:id`, `/grievances`. Verify server-side authorisation on every endpoint and document the matrix. *Accept:* a role × route matrix test passes with no redirect loops.

**CHECKPOINT — PHASE C:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE D — The public product

**D1. Rate Lookup v2.** Part 6.2 S3: geolocation-anchored, 5 nearest outlets with distance, sparkline, freshness, three follow-on actions, four states. *Accept:* a first-time visitor sees real prices for their district in under 5 seconds with one tap.

**D2. Home page.** All sections S1–S14 per Part 6.2, honouring the budgets in 6.4 and the prohibitions in 6.3. *Accept:* LCP <2.5 s on throttled 3G; every interactive element passes the Navigation Contract; five farmers can state what the product does after 30 seconds on the page.

**D3. Scroll narrative.** Part 6.6 in full, including the build script, the CI weight gate, and all three fallbacks. **Author the static story first.** *Accept:* reduced-motion and 2G users get the static story and never download frames; sequence weight ≤2.2 MB; the section is keyboard-navigable and screen-reader complete.

**D4. Header + footer.** Part 7.1–7.2. *Accept:* one top bar; mobile menu focus-trapped; every footer link resolves; grievance officer visible on every page.

**D5.** **`/mandis`****,** **`/mandis/:slug`****,** **`/map`****.** Directory, per-outlet SEO pages, clustered map with substantiated outlet types, legend, distance, latest reported rate, directions, storage layer. *Accept:* every outlet rendered is traceable to a source and confidence/verification state; coverage limitations are visible; the map renders the B2 dataset without jank at the target scale.

**D6.** **`/prices`** **and** **`/prices/:crop`****.** Part 9.5, server-rendered. *Accept:* `/prices/onion` ranks-ready with structured data; the mandi comparison shows net-after-freight.

**D7.** **`/calculator`** **— channel comparison.** USP 3, Part 6.2 S6, with editable assumptions, net-to-net comparison, latest available sourced rates, and no hidden hardcoded constants. *Accept:* every figure is fetched or user-entered or a labelled editable assumption; the headline compares net to net.

**D8.** **`/help`****,** **`/about`****,** **`/contact`****,** **`/accuracy`****,** **`/security`****,** **`/404`****.** Real content, task-based guides with audio, call/WhatsApp prominent. *Accept:* every route in Part 4.1 renders; the route-contract test passes.

**CHECKPOINT — PHASE D:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE E — The farmer product

**E1. Farmer dashboard.** All nine blocks, Part 9.1. *Accept:* a farmer sees today's price for their crops, a sell recommendation, and their action queue without scrolling past decoration.

**E2. Forecasting engine + sale-window advisor (USP 1).** Model from arrivals, seasonality, weather and history under the governance rules in Part 9.1. Always a range and a confidence, with abstention when evidence is insufficient. `forecast_outcomes` backtesting written to `/accuracy`. *Accept:* time-respecting walk-forward validation exists before the feature ships; interval coverage/calibration and sample sizes are published; no point estimate is ever rendered without its band; sparse/stale/out-of-distribution conditions abstain instead of pretending confidence.

**E3. 3-tap lot builder.** Part 9.2, including price sanity check, net panel, reserve price, camera-first photos, voice input. *Accept:* a returning farmer lists a lot in 3 taps and 0 typed characters, measured.

**E4. Offers comparison.** Part 9.3, sorted by net, with trust scores and a comparison table. *Accept:* nothing about the money appears after acceptance that wasn't shown before it.

**E5. Trade room, reachable.** Part 9.4; wire it into dashboard, offers and transactions navigation. *Accept:* every stage has evidence and both-party visibility; the PDF record downloads.

**E6. Price alerts.** Part 9.6, SMS + WhatsApp + push. *Accept:* an alert fires within 15 minutes of the threshold being crossed.

**E7. Realisation report.** USP 7 per-farmer: realised vs benchmark, per trade and cumulative. *Accept:* the benchmark is a real APMC modal average over the same window, and the method is documented on `/accuracy`.

**CHECKPOINT — PHASE E:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE F — Buyer, FPO, operations

**F1.** Buyer dashboard (Part 10.1). **F2.** Requirements with quality specs (10.2). **F3.** Discover + multi-lot assembly (10.3). **F4.** FPO members + intake ledger (11.1–11.2). **F5.** FPO pooling + payouts (11.3–11.4). **F6.** FPO compliance + reports (11.5–11.6). **F7.** Trust Ledger computation and surfacing everywhere a counterparty appears (USP 4). **F8.** Storage finder + booking (12.2). **F9.** Logistics marketplace (12.1). **F10.** Quality chain (12.3). **F11.** Payments per the documented model (12.4). **F12.** Grievances end-to-end with published statistics (Part 13). **F13.** Admin console (Part 4.1).

**CHECKPOINT — PHASE F:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE G — Reach and resilience

**G1.** Notification centre + push. **G2.** SMS templates + inbound commands. **G3.** WhatsApp Business integration with inline offer actions. **G4.** IVR line. **G5.** PWA + offline lot creation with Background Sync. **G6.** Voice input + TTS in three languages. **G7.** Simple mode + guided audio tour. **G8.** Complete/optimise the SSR/SSG or pre-render strategy chosen in Phase 0; do not introduce a late framework migration here.

**CHECKPOINT — PHASE G:** run the phase-specific acceptance suite + full regression smoke tests; update ADR/status docs; commit a clean rollback point before continuing.

## PHASE H — Quality gates (continuous, not final)

**H1.** Full test suite including both contract tests (18.1). **H2.** CI pipeline with all gates (18.2). **H3.** Observability and funnel instrumentation (18.3). **H4.** Accessibility certification (15.1). **H5.** i18n completeness gate + native review (15.2). **H6.** Performance budgets enforced (16.1). **H7.** Penetration test. **H8.** Farmer panel established and consulted (Part 19).

---


---

# PART 20A — ASTRA 6 MODULAR EXECUTION CONTRACT

> Do NOT paste the entire master specification into a coding loop and tell the agent to “build everything.” The master specification is the source of truth; execution happens through bounded work packets below.

## 20A.1 Rules for every Astra work packet

For each packet Astra must:

1. read the master sections explicitly referenced by that packet;
2. inspect existing implementation before proposing replacement;
3. write `docs/work/<packet-id>-plan.md` with current state, intended changes, files/tables/endpoints affected, migration risk and tests;
4. make the smallest coherent implementation that satisfies the packet;
5. run the packet's tests plus impacted regression tests;
6. write `docs/work/<packet-id>-result.md` with commands/results, unresolved issues, screenshots/evidence where useful and exact next dependencies;
7. create a clean git checkpoint/commit if the environment allows;
8. STOP the packet if a blocker requires external credentials/legal approval/data rather than inventing success;
9. never silently expand scope into a later packet;
10. never rewrite a working subsystem solely for style.

### Required completion status

Every packet ends in exactly one of:

- `PASS` — acceptance criteria evidenced;
- `PASS_WITH_EXTERNAL_DEPENDENCY` — software/interface complete, activation waits on named external dependency;
- `BLOCKED` — cannot safely continue; document exact blocker;
- `FAIL` — implementation attempted but acceptance criteria not met; revert or isolate before next packet.

Only `PASS` and explicitly approved `PASS_WITH_EXTERNAL_DEPENDENCY` advance.

## 20A.2 Packet 00 — Repository truth and baseline

**Read:** Parts 0–1, 16–18, 19A, 19F–19H.

Deliver: branch diff inventory, runnable baseline, architecture map, dependency/SBOM snapshot, environment matrix, existing test inventory, Lighthouse/axe/API baselines, database schema/ERD, current security/provider inventory, backup of baseline state. No redesign.

## 20A.3 Packet 01 — Architecture and domain contracts

**Read:** Parts 2, 4, 8, 19F.

Deliver: bounded-context diagram, state machines, API conventions, ID strategy, transactional outbox decision, provider-interface conventions, rendering-stack ADR, offline conflict ADR, multi-tenancy stance. Do not implement visual redesign yet.

## 20A.4 Packet 02 — Engineering foundation and design system

**Read:** Parts 5, 7.1–7.2, 15–18.

Deliver: readable formatting, lint/format/type gates, design tokens, core components, accessibility primitives, app shells, ErrorBoundary/DataState patterns, Storybook/component docs where retained, security headers baseline and CI gates. Preserve business behavior.

## 20A.5 Packet 03 — Geography, outlet provenance and crop registry

**Read:** Parts 8.3–8.5, 19A.5–19A.6, 19E.

Deliver: geography tables/API, outlet registry/import pipeline, provenance/confidence/admin review, crop/variety/quality registry, geocoding correction migration, data-quality dashboards and tests. No claim of comprehensive coverage beyond measured dataset.

## 20A.6 Packet 04 — Official/reported market-price pipeline

**Read:** Parts 6.2 S3, 8.6, 9.5, 19A.6.

Deliver: server-side credentials, ingestion scheduler/jobs, raw/normalized lineage, freshness semantics, cache, source health, price APIs, truthful stale state, price UI primitive and unit tests. Do not build forecasting here.

## 20A.7 Packet 05 — Identity, onboarding, authorization and consent

**Read:** Parts 7.3, 8.1–8.2, 17, 19A.11–19A.12.

Deliver: OTP/password strategy, phone normalization, roles/object authorization, token rotation, consent records, legal-page version framework, structured location onboarding, provider interfaces for verification, security/abuse tests. External provider success may remain pending honestly.

## 20A.8 Packet 06 — Farmer core pilot

**Read:** Parts 9.1–9.4, 19B.1, Tier 1 in 19H.

Deliver only farmer Tier-1 journey: post-login location/price/action viewport, lot builder, lot management, offers/counter/accept, reachable Trade Room core stages, records, core notifications, support links. Validate the 3-tap target; if user testing disproves it, optimize for comprehension rather than gaming the metric.

## 20A.9 Packet 07 — Buyer core pilot

**Read:** Part 10, 19B.2, Tier 1.

Deliver requirements, discover/match, landed-cost basics, offer management, trade participation, role/team basics where required. Test farmer-data minimization and object authorization.

## 20A.10 Packet 08 — FPO core pilot

**Read:** Part 11, 19B.3, Tier 1.

Deliver member roster/import, intake ledger, receipts, pooling, contribution traceability, publish/offer/trade connection, basic payout allocation records. Test low-connectivity intake and correction audit trail.

## 20A.11 Packet 09 — Public product, homepage and discovery

**Read:** Parts 3–7, 16, 19D.3.

Deliver public rate lookup, homepage progressively enhanced journey, mandi/outlet directory/map, price pages, help/about/contact/legal routes, SEO/rendering strategy and truthful social proof rules. Scroll sequence is added only after static story and performance budget pass.

## 20A.12 Packet 10 — Trade operations: quality, logistics, storage and disputes

**Read:** Parts 12–14, 19A.9, 19E.

Deliver quality evidence chain, storage UI/bookings using available backend, logistics abstraction/quotes, dispute workflow, transaction timeline and admin/support operations. Partner-dependent providers can be `PASS_WITH_EXTERNAL_DEPENDENCY`.

## 20A.13 Packet 11 — Intelligence and differentiation

**Read:** USP 1/3/4/7, Parts 9.5–9.6, 19A.7, 19E.1.

Sequence internally:

1. net-realization calculator;
2. price alerts;
3. trust-score computation only after sample-size-safe method exists;
4. trend/seasonality intelligence;
5. forecasting in shadow mode;
6. sale-window recommendation only after validation gate.

Never jump directly to prescriptive AI/ML.

## 20A.14 Packet 12 — Offline, multilingual, voice and reach

**Read:** Parts 14–16.

Deliver installable PWA, cached truthful price viewing, offline draft/lot queue, sync conflict UX, Hindi/Marathi completeness, low-literacy simple mode, selective audio/voice, SMS/push. WhatsApp/IVR are external-provider sub-packets.

## 20A.15 Packet 13 — Admin, fraud, support and operational tooling

**Read:** Parts 13, 17–19A, 19E–19G.

Deliver verification/outlet review, price-source health, dispute queue, support timeline, fraud flags, audit explorer, provider health, safe retry/replay actions, permissioned metrics and runbooks. Admin features receive the same accessibility/security rigor as public UI.

## 20A.16 Packet 14 — Government/enterprise readiness

**Read:** Part 19C and Tier 4.

Deliver compliance matrix, procurement pack, GIGW evidence, security-audit readiness, export/exit plan, department MIS, hosting/DR options, training/UAT materials and contract configuration boundaries. Do not claim certification before an external certifier issues it.

## 20A.17 Packet 15 — Production hardening and release candidate

**Read:** Parts 16–18, 19G, Part 21.

Run full regression, load/soak/failure tests, restore drill, security test, accessibility/manual review, stale-provider drills, migration rehearsal, observability verification, SLO dashboards, cost checks and release rollback rehearsal. Produce `docs/release/production-readiness.md` with signed evidence per discipline.

## 20A.18 Packet 16 — Pilot evidence and iteration

Software completion is not product completion. Run measured pilot/user research. Capture farmer comprehension, time-to-value, listing success, buyer fill, FPO throughput, support reasons, disputes and realisation methodology. Feed findings back as versioned product changes. Do not rewrite the whole product after a single anecdote.

---

# PART 20B — ROLE-BASED SIGN-OFF CHECKLIST BEFORE ANY RELEASE

A release candidate cannot be declared production-ready based on one developer's judgment. Record sign-off/evidence for applicable roles:

| Role | Must sign off / evidence |
| --- | --- |
| Product | scope, success metric, exclusions, user journey |
| UX research | comprehension/usability evidence with target users |
| Frontend | responsive/a11y/performance/error states |
| Backend | API/state-machine/auth/idempotency correctness |
| DBA | migration/index/backup/restore/data integrity |
| Data engineering | source lineage/freshness/schema quality |
| ML | only if ML feature included: validation/model card/rollback |
| QA | traceability matrix + critical regression pass |
| Security | threat model + findings disposition |
| Privacy/legal | policy/processing/provider/compliance review |
| SRE/DevOps | deployment/monitoring/DR/rollback/capacity |
| Support/Ops | runbook/admin tooling/escalation readiness |
| Localization | target-language review |
| Accessibility | manual + automated evidence |
| Business owner | fees/provider contracts/support capacity |
| Government procurement | only for government release: compliance/procurement/UAT evidence |

One person may hold multiple roles in a small team, but the checklist does not disappear.


# PART 21 — DEFINITION OF DONE

**Truth**

-  No fabricated identifier, company, certification, transaction or statistic is presented as production truth; synthetic fixtures exist only in isolated test/demo environments and are unmistakably labelled and blocked from production ingestion
-  Every claim on the site is verifiable by the user or a third party
-  The fee model is published on the home page and matches the Terms exactly
-  "Live" appears only over genuinely live data; every price shows its real reported date
-  Forecast accuracy, dispute statistics and realisation-vs-benchmark are published

**Navigation**

-  Every link resolves — enforced by the route-contract test
-  Every query parameter sent is consumed — enforced by the param-contract test
-  Every interactive element works or is visibly labelled a preview
-  Intent survives every auth redirect; farmer, buyer and FPO have three distinct paths

**Comprehension**

-  Every farmer-facing string passes the 6th-standard reading test with a real farmer
-  Three languages at 100% coverage, native-reviewed, CI-gated
-  Simple mode and audio playback ship and are tested with low-literacy users

**Capability** — all 26 rows of the Part 2 map delivered

-  Nearby mandi board · sale-window advisor · buyer directory · quality specs · demand signals · logistics · storage · trust ledger · liquidity partner integration (when a real regulated partner is configured) · offer competition · aggregation · quality chain · lot builder · offers · payment timeline · grievances · realisation report · cost transparency · FPO OS · supply planner · trade record

**Function**

-  Session survives refresh and expiry; roles enforced client and server side
-  Zero silent sample-data fallbacks anywhere
-  No production UI can report an external verification/payment/message/finance success unless a real configured provider or documented manual-review workflow produced it
-  Government daily mandi observations are labelled as latest/reported official prices, not real-time “live” ticks unless the source actually provides real-time semantics
-  OTP login works; phone normalises on every path; recovery works
-  Location structured everywhere; geocoding correct nationwide
-  Unit/price cannot produce an order-of-magnitude error
-  A returning farmer lists a lot in 3 taps and 0 typed characters

**Quality**

-  LCP <2.5 s, INP <200 ms, CLS <0.1 on a real mid-range Android over throttled 3G
-  Initial JS <150 KB gzip; above-fold images <200 KB; scroll sequence ≤2.2 MB with all three fallbacks
-  Zero axe violations on every route; every journey completable by keyboard and by screen reader
- `prefers-reduced-motion` honoured globally
-  All four states on every async surface
-  Works offline for price viewing and lot creation
-  Prettier-enforced; no file authored in minified style

**Governance**

-  DPDP consent, withdrawal and data-principal rights implemented
-  Terms, Privacy, Refunds, Grievance Policy complete in three languages, legally reviewed
-  securityheaders.com grade A; penetration test completed and resolved
-  Error reporting live, so "our team has been notified" is true
-  Regression test for every bug listed in Part 1.3
-  Farmer panel established, paid, and consulted on a documented cadence

---

*Execute Part 20 in order. Verify every acceptance criterion. Where a shortcut and this document disagree, this document wins.*

---

# PART 22 — EXTERNAL EVIDENCE REGISTER AND FRESHNESS POLICY

The competitive, legal, government and standards landscape changes. Create `docs/evidence-register.md`. Each externally dependent claim records: claim, source URL/document, publisher, publication/update date, date checked, owner and next review date.

Priority official sources to track include:

- Guidelines for Indian Government Websites and Apps (GIGW 3.0), NIC/MeitY: https://guidelines.india.gov.in/
- STQC Website Quality Certification: https://stqc.gov.in/
- CERT-In directions/advisories: https://www.cert-in.org.in/
- MeitY DPDP Act/Rules notifications: https://www.meity.gov.in/
- data.gov.in / Agmarknet price resources: https://www.data.gov.in/
- eNAM official materials: https://enam.gov.in/
- WDRA official information: https://wdra.gov.in/
- Local Government Directory: https://lgdirectory.gov.in/
- Bhashini/Digital India language infrastructure where used: https://bhashini.gov.in/
- GI Cloud/MeghRaj guidance where a government deployment requires it: https://www.meity.gov.in/

**Do not hardcode volatile competitor user counts, mandi counts, government programme totals or regulatory interpretations into public copy without a dated source.**

---

# PART 23 — FINAL PRODUCT PRINCIPLE

KrishiLink does not win by having the most screens. It wins if each participant gets a materially better decision or transaction with less uncertainty and less effort:

- the farmer gets truthful, local, understandable options and can act with minimal input;
- the buyer gets dependable supply, landed-cost visibility and traceable quality/fulfilment;
- the FPO gets an operating ledger from member intake to pooled sale to member settlement;
- operations can resolve failures without hidden database work;
- engineers can change the system without breaking money, units, permissions or data lineage;
- government can procure, audit, operate and exit the platform without lock-in or unverifiable claims;
- investors can see defensible network liquidity, retention, reliability and unit economics rather than vanity growth;
- judges can verify that the differentiated workflows are real, technically credible and honest about external dependencies.

**When completeness conflicts with clarity, reliability or trust, choose clarity, reliability and trust. A smaller capability that works end-to-end is more valuable than a larger surface that only demos well.**
