# Work Packet 02 — Engineering Foundation and Design System Plan

Date: 2026-09-17  
Branch: `abdulrehman`  
Scope: frontend foundation only; no new dashboards or product-flow redesign, no backend refactor, no commit or push.

## Verified current state

- React 19 + Vite + React Router; route-level lazy loading is already present and must be retained.
- `main.jsx` imports both `index.css` and `styles/experience.css`. `index.css` imports Tailwind and contains an older token/component set with `@apply`; the active experience stylesheet separately defines a competing palette and most app surfaces, often as minified CSS and raw colors. Tailwind utilities are not used by app components, so the Tailwind layer is removable after confirming the new stylesheet builds.
- Existing reusable code is in `components/Experience.jsx` (Field, Notice, DataState, PageHeading, useResource), `ErrorBoundary.jsx`, `Navbar.jsx`, `Footer.jsx`, and the two layout components. Existing behavior includes auth/session refresh, URL query prefill/filter contracts, translated strings, and API-backed async states; preserve these contracts.
- `Field` currently defaults every control to `autoComplete="off"`. This overrides explicit autocomplete intent supplied by the login, registration and address forms.
- Frontend has Oxlint and Vitest, but no formatter/typecheck scripts or blocking CI frontend checks for formatting, types, accessibility and bundle budgets. Playwright currently runs four desktop/mobile cases; axe is applied only to the public homepage.
- Production static headers are absent in both Nginx and Vercel configuration. Leaflet requires external OpenStreetMap tiles and inlined marker assets; the configured policy must account for those actual resources and the configurable API origin.
- Existing package build output from Packet 01: initial entry JS 247.52 KB / 79.42 KB gzip, CSS 56.99 KB / 11.45 KB gzip, plus lazy route chunks. Re-measure after migration.

## Intended implementation

1. Replace the two competing CSS systems with one token layer plus one formatted application stylesheet, using semantic tokens for colors, type, spacing, radius, elevation, focus, motion, containers and breakpoints. Remove only unused Tailwind scaffold/dependencies and dead decorative CSS; retain used layout and domain styles.
2. Harden and document the existing primitives rather than redesign product screens: Button, Field, Card, Badge/StatusPill, Notice, DataState/Skeleton, PageHeading and ErrorBoundary. Use translation infrastructure for reusable visible labels; remove the autocomplete-off default; maintain native semantics and 48px controls.
3. Add tests for primitive semantics, labels, loading/error/empty/stale/offline state, and error-boundary recovery. Expand Playwright checks to responsive key public/auth/protected routes and all three languages with axe checks, without adding fabricated data to the product.
4. Add security headers to both Nginx and Vercel static-host configurations, using CSP directives compatible with the app's API fetch, Leaflet tiles, and local assets. Keep development server behavior unchanged.
5. Add Prettier formatting and JavaScript type checking as reproducible frontend scripts/CI gates if package installation is available; apply readable formatting in frontend source. Add measurable initial bundle budget reporting/gating without eagerly loading maps/charts.
6. Record component usage/accessibility guidance in a lightweight component README rather than adding Storybook dependencies unless the existing repository already retains Storybook.

## Expected files/surfaces

- `frontend/src/styles/tokens.css`, a consolidated app stylesheet, `frontend/src/main.jsx`.
- `frontend/src/components/Experience.jsx`, `ErrorBoundary.jsx`, reusable primitive tests and component guidance.
- `frontend/index.html`, `frontend/nginx.conf`, `frontend/vercel.json`, frontend package/config files, and `.github/workflows/ci.yml`.
- `docs/work/02-plan.md`, `docs/work/02-result.md`, and `PROGRESS_TRACKER.md`.
- No API routes, backend files, database models, or migrations.

## Risks and migration approach

Style consolidation can unintentionally change pages; preserve existing selectors and compare builds/screenshots at 360x640, 390x844, 768x1024 and 1440x900. CSP must permit configured API calls and OpenStreetMap tiles while keeping script sources self-only. A frontend-wide formatting pass will touch many files, so verify it is formatting-only and retain semantic changes narrowly. Current locale dictionaries may contain gaps; do not silently change the established English fallback globally in this foundation packet.

## Verification

Run `npm run lint`, formatter check, frontend typecheck, `npm run test`, `npm run build`, and `npm run test:e2e`; add primitive/axe coverage and check production headers and bundle sizes. Run `python -m pytest -q`, `python -m ruff check app`, and `python -m mypy app` to protect the 125-test backend baseline. Finish with `git diff --check` and inspect the complete diff/status; no commit/push and no Packet 03.
