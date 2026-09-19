# Work Packet 09 — Public Product, Homepage and Discovery

## Scope and baseline

Branch: `abdulrehman`. Execute Packet 09 only; do not commit or push. Packet 08A is accepted as the persisted FPO baseline. The working tree already contains uncommitted changes from Packets 00–08A; preserve them and keep this packet's edits scoped.

Repository inspection found a React/Vite SPA with a public homepage, price lookup, a reviewed-market map, and four informational pages. The app has no public mandi directory/detail, crop-specific price routes, buyer directory, contact page, complete public legal route set, sitemap, robots policy, or route-specific static HTML. `frontend/index.html` is one generic document and the frontend only changes the DOM language attribute; it does not provide route metadata. `MapPage` consumes the reviewed `/markets` endpoint, while the older `/markets/locations` projection can expose individual buyer, FPO and storage coordinates. The public `/users/buyers` projection includes account names and location fields and does not require business verification.

Existing source-of-truth constraints: AGMARKNET rows are daily reported observations, crop and outlet records are canonical registries, only active reviewed outlets meeting confidence thresholds are publicly listed, source/coordinate verification dimensions must not be conflated, and terms/privacy documents remain drafts pending legal review. The Packet 09 product must not show unsupported live/best-price claims, statistics, testimonials, support contacts, legal facts, or outlet counts.

## Decisions

1. Keep React + Vite. Add build-time pre-rendering for the public route subset so initial HTML contains route-specific title, description, canonical metadata (when configured), useful public page content, and dynamic crop/outlet snapshots only when obtained from the real public API. Client React hydrates the HTML and refreshes data through the current API. If public API data is unavailable during build, omit dynamic crop/outlet pages and sitemap entries rather than inventing registry records or asserting that data is absent.
2. Use `PUBLIC_SITE_URL` for absolute canonical, social and sitemap URLs. Do not emit `hreflang` until English/Hindi/Marathi have distinct stable URLs; local-storage language selection is not a language URL.
3. The public crop-price and outlet pages describe reported observations and registry facts. They do not use Product/Offer markup for non-contractual mandi reference prices. Price rows retain report date, unit and source. Outlet directory pages use the existing reviewed-market gate; buyer/FPO/storage precise locations are excluded from the public map.
4. Public buyer listings show business-verified organization-level fields only; hide personal names, account IDs, contact fields and precise location. Do not surface transaction-derived ratings or fabricated standing requirements.
5. Legal pages remain prominently marked as drafts and `noindex` until approved. Public support details render only from explicitly configured deployment values; absent details are stated as unavailable. The public grievance link leads to the real authenticated workflow.

## Implementation and verification plan

- Add route-specific public pages and plain English/Hindi/Marathi copy using the existing catalog.
- Improve public navigation, footer, mobile menu and home-page hierarchy while keeping price lookup based on the official reported-price API and preserving explicit user-initiated geolocation only.
- Add safe buyer projection and slug-addressable reviewed outlet detail projection; keep map rendering limited to reviewed public outlets.
- Add Vite SSR pre-render generation for public routes and canonical registry-derived crop/outlet routes, metadata, JSON-LD only where evidence supports it, `robots.txt`, and a sitemap. Add a checker that inspects generated HTML to prevent a title-only CSR implementation from passing.
- Add focused backend/frontend tests, then run the existing frontend build/lint/unit/E2E/security/bundle gates and relevant backend suite. Browser review covers 360×640, 390×844, 768×1024 and 1440×900 if available.

## Out of scope and dependencies

No forecasting, sale advice, net-realization comparison, trust score, payment movement, storage/logistics discovery, synthetic demo data, organization/legal claims, or Packet 10 work. Dynamic static generation in deployment requires a public API origin and site origin; a current official price/outlet dataset is not assumed. Legal review, support-channel configuration, provider provisioning, and PostgreSQL/PostGIS live behavior remain external where applicable.
