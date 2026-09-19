# Work Packet 09 — Public Product, Homepage and Discovery

**Status: PASS_WITH_EXTERNAL_DEPENDENCY**  
**Branch:** `abdulrehman`  
**Scope:** Packet 09 only. No commit or push.

## Executive summary

Packet 09 adds public product and discovery routes while keeping public claims tied to repository data. Public prices are described as reported observations with their date and source. Market pages are generated only from reviewed outlet records, and buyer discovery exposes business-level information only after business verification. The stale bundled `live_mandi_prices.json` sample dataset was removed.

Public pages are now pre-rendered into route-specific HTML during the frontend build. The SEO checker inspects the generated files, including titles, descriptions, canonical metadata, visible content, robots directives, structured data and sitemap entries; changing `document.title` in a client-only shell is not treated as SEO completion. Dynamic crop and outlet pages are generated only when the configured public API returns real registry/price records. A fixture-backed build verified that path. The ordinary local build had no public API origin or site origin configured, so it generated no dynamic crop/outlet pages and omitted absolute canonical/sitemap URLs rather than inventing data.

## Truthful public claims and user experience

- The homepage, reported-prices experience, market directory/detail, crop-price detail, verified-business directory, help, about, contact, security and policy routes use plain-language public copy. The home page does not assert unsupported live prices, best prices, market counts, user counts, endorsements or testimonials.
- Public market-rate language distinguishes a reported observation from a contractual price. Generated crop pages preserve the real crop, market, report date, unit and source from the API. No sample price is substituted when the API or observations are unavailable.
- Public outlet listings require active reviewed records with usable coordinates and confidence. Detail pages expose a limited public projection; source links are HTTP(S)-only and `source_ref`/internal review fields are not exposed. Buyer/FPO/storage coordinates cannot be enumerated through the public `category=all` map request; private map layers require elevated access.
- `/api/v1/users/buyers` now returns only business-reviewed buyer organizations and an allowlisted organization-level projection. It omits account IDs, personal names, email, phone, precise location and ratings. The test also verifies that an unreviewed business is absent.
- The old bundled `frontend/public/data/live_mandi_prices.json` dataset was deleted. Unused legacy translation entries that said “Today's Best Price,” “Live AGMARKNET,” or claimed private map layers/proximity were revised in English, Hindi and Marathi to avoid resurfacing those unsupported claims.
- Legal text remains visibly marked as draft and `noindex` pending legal review. Support phone/email render only when configured; an absent channel is described as unavailable and the real authenticated grievance route remains available.

## SEO and deployment behavior

The Vite build now runs React server rendering for the public route subset, then generates route HTML from allowlisted API snapshots. It writes `robots.txt` and a sitemap, adds route-specific title/description and social metadata, and includes structured data only where supported (WebSite/SearchAction, visible FAQ, and real outlet breadcrumb/place facts). Mandi reference prices deliberately do not use Product/Offer schema. No `hreflang` is emitted because the app has no distinct stable locale URLs.

`PUBLIC_SITE_URL` is required for absolute canonical, social and sitemap URLs. `PUBLIC_PRERENDER_API_BASE_URL` (or the configured public API base) must be reachable during build for dynamic crop/outlet pages. These values are wired into the frontend Docker build and documented in the environment examples. The local Nginx fallback resolves generated `index.html` files before the SPA shell; Vercel keeps the SPA fallback rewrite, with generated static files taking filesystem precedence. Deployment routing itself was not exercised against a live Vercel/Nginx host.

The fixture-backed build generated 22 public route HTML files and a sitemap with 14 entries, including one crop page and one outlet page from real-shaped API records. It asserted the exact reported date/source/price and verified that buyer PII and an unsafe JavaScript source URL were omitted. The normal local build generated 20 static public routes and recorded 8 sitemap-eligible paths in its manifest; it generated zero crop/outlet pages because the API was unavailable. Since the canonical origin was unset, it correctly omitted the absolute `sitemap.xml` and URL-based canonical metadata. This is intentional fail-closed behavior. Dynamic snapshots are build-time data, so deployment must rebuild on an appropriate cadence to keep crawlable observations current; visible report dates remain the source of freshness truth.

## Frontend, accessibility and performance

Public navigation, responsive directory/detail pages, FAQs, accessible mobile menu, help/contact/legal content and EN/HI/MR copy were added through the existing React/Vite and translation architecture. Public copy coverage tests require every `public*` key in all three languages. Policy drafts are not indexable. The map remains lazy-loaded and is not part of the initial server-rendered page.

Browser coverage ran on desktop and mobile projects. The home route was checked at 360×640, 390×844, 768×1024 and 1440×900 in English, Hindi and Marathi, including 48px primary-action sizing, horizontal-overflow checks and axe WCAG 2.2 AA tags. Public/sign-in routes received axe checks; public discovery checks cover dated reported prices, reviewed outlets, business-only buyer data and source-link safety. Keyboard skip navigation and Escape-to-close mobile-menu behavior are covered. This is automated coverage, not a manual screen-reader review.

The final full browser run passed 18/18 tests in 3.9 minutes. A preceding run that competed with the full backend suite timed out in one multi-route accessibility test (17/18); the same desktop/mobile accessibility test then passed 2/2 when isolated, and the final full run passed. Frontend production budgets passed: initial JS 128.33 KiB gzip against 150 KiB; JS+CSS+static assets 136.57 KiB against 400 KiB.

## Backend/privacy changes

No database schema or migration was added. Three Packet 09 backend tests cover the public buyer projection/verification gate, reviewed outlet detail projection and safe source URL handling, and public/private map layers. The Packet 05 buyer-directory regression was updated to assert privacy and verification without assuming the test database has no separately seeded reviewed buyer.

The final clean isolated SQLite regression command was:

```text
DATABASE_URL=sqlite:///C:/abdul/backend/.packet09-full-final.db
python -m pytest -q --durations=0
```

Result: **183 collected, 183 passed, 0 failed, 0 skipped**; process exit code 0. Pytest reported one `pytest-asyncio` deprecation warning (`asyncio.get_event_loop_policy`). The first run exposed the brittle test assumption described above; the corrected test and clean full-suite rerun passed. SQLite does not verify PostgreSQL row-locking or PostGIS runtime behavior; Packet 09 introduced no migration or lock-sensitive database changes.

## Verification results

| Check | Result |
|---|---|
| `python -m pytest -q --durations=0` on clean isolated SQLite | PASS — 183 passed, 0 failed, 0 skipped; one pytest-asyncio deprecation warning |
| `python -m ruff check app tests/test_packet09_public_surface.py` | PASS |
| `python -m mypy app` | PASS — 82 source files |
| `python -m compileall -q app tests` | PASS |
| `npm run lint` | PASS |
| `npm run test` | PASS — 21 tests across 6 files |
| `npm run test:e2e` | PASS — 18 browser tests, desktop/mobile |
| `npm run test:seo-fixture` | PASS — generated and checked API-backed crop/outlet HTML; buyer PII and unsafe source URL excluded |
| `npm run build` | PASS — 20 static routes, 8 sitemap entries; no dynamic API data fabricated |
| `npm run check:security` | PASS — 6 matching static security headers and baseline CSP directives |
| `npm run check:bundle` | PASS — within both configured budgets |
| Provider-key scan in build | PASS — no configured credential material in frontend output |
| `git diff --check` | PASS — no whitespace errors; Git emitted only existing LF-to-CRLF working-copy warnings |
| TypeScript / Prettier | NOT RUN — repository-local `tsc` and `prettier` binaries are absent |

## Migrations, risks and external dependencies

There is no Packet 09 migration. PostgreSQL/PostGIS and live deployment routing were not available for rehearsal. The remaining activation requirements are build-time configuration of the production public origin and reachable public API, real reviewed crop/price/outlet data, a production rebuild cadence for crawlable snapshots, approved legal copy, and any real support channel the operator wants displayed. Native-speaker review of critical legal/agricultural terms and manual assistive-technology review remain release follow-ups.

The principal production risk is deployment misconfiguration: without `PUBLIC_SITE_URL` and a reachable `PUBLIC_PRERENDER_API_BASE_URL`, the site remains usable as an SPA but does not publish absolute SEO URLs or dynamic crop/outlet landing pages. The build warns and fails closed rather than claiming those pages exist. Static snapshots also age until a new deployment build.

## Files added or updated for Packet 09

- Backend: `backend/app/modules/users/router.py`, `backend/app/modules/markets/router.py`, `backend/tests/test_packet09_public_surface.py`, `backend/tests/test_packet05_identity.py`.
- Public frontend: `frontend/src/App.jsx`, `frontend/src/main.jsx`, `frontend/src/layouts/PublicLayout.jsx`, `frontend/src/components/{Navbar,Footer,RateLookup,PublicMarketsMap}.jsx`, `frontend/src/pages/{LandingPage,InfoPage,PricesPage,MapPage,CropPricePage,MandiDirectoryPage,MandiDetailPage,PublicBuyerDirectoryPage}.jsx`, and `frontend/src/services/api.js`.
- SEO/rendering: `frontend/index.html`, `frontend/vite.config.js`, `frontend/src/lib/{metadata,publicSnapshot}.js`, `frontend/scripts/{prerender-public,check-seo-rendering,test-prerender-fixture}.mjs`, and `frontend/public/og-default.svg`. The build generates `robots.txt`; it emits `sitemap.xml` only when `PUBLIC_SITE_URL` is configured.
- Copy/styles/tests: `frontend/src/utils/{copy.js,copy.test.js,translations.js}`, `frontend/src/content/policies.js`, `frontend/src/styles/{app.css,tokens.css}`, and `frontend/e2e/critical-journeys.spec.js`.
- Build/deployment/docs: `frontend/package.json`, `frontend/package-lock.json`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/vercel.json`, `docker-compose.yml`, `.env.example`, `frontend/.env.example`, `docs/DECISIONS.md`, `docs/work/09-plan.md`, `PROGRESS_TRACKER.md`.
- Removed: `frontend/public/data/live_mandi_prices.json`.

## Git state

Branch is `abdulrehman`. The working tree remains dirty with Packet 00–08A work as well as Packet 09 changes; no commit or push was made. Packet 10 was not started.
