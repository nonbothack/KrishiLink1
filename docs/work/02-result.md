# Work Packet 02 — Engineering Foundation and Design System

**Status: PASS_WITH_EXTERNAL_DEPENDENCY**

**Date:** 2026-09-17  
**Branch:** `abdulrehman`  
**Scope:** Packet 02 only. No Packet 03 work, database migration, endpoint, commit, or push was performed.

## Executive summary

Packet 02 establishes a maintainable frontend foundation while preserving the existing React/Vite routes, workflows, query parameters, API integration, and English/Hindi/Marathi translation system. The frontend now has a shared design token layer and authored application stylesheet, reusable typed accessibility and data-state primitives, local error recovery, formatting/type/security/bundle gates, static response-header baselines, and CI coverage for those gates. Existing server-rendered business content and route components were not broadly redesigned.

The code and local checks are complete. Live Nginx/edge header behavior could not be exercised because the Docker engine and deployment edge are external to this checkout; static Nginx/Vercel configuration parity is checked in CI. No production header behavior is claimed from that static check alone.

## Architecture decisions

- Keep React + Vite and the current client-routed application. No SSR migration or service decomposition.
- Replace duplicated/unused Tailwind and legacy styling layers with `frontend/src/styles/tokens.css` and `frontend/src/styles/app.css`. Tokens cover brand and semantic colors, type, spacing, shapes, elevation, motion, layout, and touch targets.
- Keep existing JavaScript route pages. Type-check the shared component foundation with strict TypeScript rather than initiating a wholesale application conversion.
- Share typed Button, Card, Badge, StatusPill, Skeleton, Field, Notice, DataState, `useResource`, and PageHeading primitives. Preserve visible loading/error/empty states and explicit stale/offline labels; API failures do not become sample data.
- Keep ErrorBoundary recovery local to the affected UI, with a retry action and navigation path. It makes no false claim about reporting an error.
- Keep copy in the existing translation system. Hindi and Marathi use Devanagari-aware system font stacks and increased line-height; no external font is fetched.
- Preserve lazy route splitting and enforce gzip budgets on initial resources.
- Apply matching baseline response headers in Nginx and Vercel configuration and verify configuration parity. CSP `connect-src` permits HTTPS/WSS because the production API origin is not yet fixed; narrow it when deployment origins are known.
- Do not add Storybook. Component contracts, translation requirements, and accessibility use are documented beside the shared components.

## Components and app shells

`frontend/src/components/Experience.tsx` adds the typed shared primitives; `Experience.test.jsx` tests their behavior. `frontend/src/components/ErrorBoundary.tsx` supplies retry/navigation recovery. Public and dashboard shells retain existing navigation and content. The public shell now supports a skip link and Escape-to-close mobile menu with focus return; the dashboard shell has a skip link and focusable main target. Existing screen components remain the source for their domain-specific layouts.

## Legacy CSS disposition

Removed the imported `frontend/src/index.css` Tailwind layer and the duplicate `frontend/src/styles/experience.css`. Vite no longer loads the unused Tailwind plugin. Their required active visual rules were consolidated into the tokenized `app.css`; unused decorative/duplicate layers were not restored. Screen-level inline layout values touched during migration now use shared classes/tokens. No product route or business behavior was removed as part of this cleanup.

## Accessibility and i18n

- Shared controls use native semantics, visible focus, labels, descriptions, and linked validation errors. Icon-only controls require an accessible name. Buttons default to `type="button"`; loading controls expose busy/disabled state.
- Added keyboard skip navigation, Escape handling for the mobile menu, focus return, reduced-motion handling, and a 48px minimum check for the primary homepage action.
- Playwright/Axe scans cover `/`, `/login`, `/register`, `/prices`, `/map`, `/help`, `/terms`, `/privacy`, and `/about`, at desktop and mobile projects. Homepage checks exercise English, Hindi, and Marathi over 360x640, 390x844, 768x1024, and 1440x900 viewports, with overflow, primary-action size, document language, and accessible-structure assertions.
- Browser test assertions use axe-core WCAG 2 A/AA, 2.1 A/AA, and 2.2 AA tags. This is automated coverage, not a claim of complete WCAG conformance or native-speaker review.
- Fonts rely on local system fallbacks (including Noto Sans Devanagari/Nirmala UI); no self-hosted font assets were available.

## Performance

Production Vite build passed. The initial JS graph is **106.99 KiB gzip**, below the 150 KiB budget. Initial JS plus CSS and static assets is **112.65 KiB gzip**, below the 400 KiB budget. The map remains lazy-loaded as a separate **45.64 KiB gzip** chunk. The generated initial CSS is 24.39 kB raw / 5.82 kB gzip. No Lighthouse run is claimed.

## Tests and verification

| Command/check | Result |
| --- | --- |
| `python -m pytest -q` (backend regression baseline) | 125 passed, 0 failed, 0 skipped; existing Python 3.14 asyncio deprecation warning |
| `python -m ruff check app` | Passed |
| `python -m mypy app` | Passed, 70 files |
| `npm run lint` | Passed |
| `npm run test` | 17 passed across 3 files |
| `npm run test:e2e` | 8 passed (desktop and mobile projects; 2.2 minutes) |
| `npm run build` | Passed; production assets and Vite manifest generated |
| `npm run check:security` | Passed; six matching static headers and baseline CSP directives verified |
| `npm run check:bundle` | Passed; 106.99 KiB initial JS gzip / 112.65 KiB initial JS + CSS + static assets gzip |
| `tsc --noEmit` with TypeScript 5.9.3 | Passed |
| Prettier 3.6.2 `--check` | Passed for frontend source, scripts, E2E, and root frontend configuration files |
| `git diff --check` | Passed after final documentation update |
| Live Docker/Nginx header probe | Not run: Docker engine unavailable in this environment; static configuration checks ran instead |
| Storybook | Not run/not added: component documentation retained in `frontend/src/components/README.md` |
| Lighthouse | Not run: no browser performance audit was part of available local checks |

The first expanded Playwright attempt exceeded its 30-second per-test default while iterating the viewport/language matrix. The test timeout was raised to 120 seconds for those matrix journeys and the final complete run passed. Two concurrent npm-exec checks encountered a Windows npm registry/cache `EACCES`; serial retries with approved package-cache access both passed. No test was skipped in the final runs.

## Regressions

No route, API contract, authentication/session behavior, translation key ownership, or domain workflow was intentionally changed. Regression evidence is the preserved 125-test backend suite, 17 frontend unit tests, and eight final browser journeys. Browser tests explicitly cover protected intent through login and public/mobile navigation behavior. Remaining production concerns from Packets 00/00A/01 are not resolved by this foundation packet and remain in their prior audit records.

## Security baseline

The frontend now checks parity for six static headers across the Nginx and Vercel configurations, including content-type sniffing, framing, referrer, permissions, transport, and CSP directives. CSP allows inline styles required by current map/UI behavior and HTTPS/WSS connections while the API host remains configurable. Static inspection cannot prove deployed response behavior; the actual hosting configuration must be probed after deployment. This packet does not claim to resolve previously documented backend security blockers.

## Migrations and endpoints

No database migrations, models, API endpoints, or backend implementation were added or changed by Packet 02.

## Changes made and files changed

Packet 02 implementation files:

- `.github/workflows/ci.yml`
- `docs/DECISIONS.md`
- `docs/work/02-plan.md`
- `docs/work/02-result.md`
- `frontend/.oxlintrc.json`, `.prettierignore`, `.prettierrc.json`, `Dockerfile`, `index.html`, `nginx.conf`, `package.json`, `package-lock.json`, `tsconfig.json`, `vercel.json`, `vite.config.js`
- `frontend/scripts/check-bundle-size.mjs`, `check-security-headers.mjs`, `run-e2e.mjs`
- `frontend/src/components/README.md`, `ErrorBoundary.tsx`, `Experience.tsx`, `Experience.test.jsx`, `design-system.typecheck.tsx`
- `frontend/src/hooks/useLanguage.d.ts`, `frontend/src/main.jsx`, `frontend/src/layouts/DashboardLayout.jsx`, `frontend/src/components/Navbar.jsx`
- `frontend/src/styles/tokens.css`, `frontend/src/styles/app.css`; removed `frontend/src/index.css` and `frontend/src/styles/experience.css`
- `frontend/src/pages/BuyerDashboard.jsx`, `FPODashboard.jsx`, `GrievancesPage.jsx`, `InfoPage.jsx`, `MapPage.jsx`, `OffersPage.jsx`
- `frontend/e2e/critical-journeys.spec.js`

Existing JavaScript frontend source files covered by the new formatter were formatted for readable style; behavior changes were limited to shared design-system migration and the explicit accessibility improvements documented above. The backend and earlier Packet 00/00A/01 files remain in the shared working tree from their earlier work; this list isolates Packet 02 changes rather than attributing those prior edits to this packet.

## Risks

- CSP `connect-src` remains broad (`https:`/`wss:`) until actual API origins are set; static checks cannot choose safe deployment-specific hosts.
- Header and CSP parity is verified in source configuration, not against a live edge. Docker/Nginx runtime behavior remains unverified.
- Automated axe scans do not replace screen-reader, keyboard-only, field, or native-speaker usability sessions. Low-literacy and low-connectivity usability still needs direct farmer/FPO/buyer validation.
- System Devanagari font availability varies by device, which can alter wrapping and metrics beyond tested browser/device configurations.
- Initial bundle budgets cover build output gzip size, not field-network latency or Lighthouse/Core Web Vitals.
- Prior production blockers recorded in Packet 00/00A remain outside Packet 02 scope.

## External dependencies

- Docker engine / deployment environment for live Nginx header and CSP response verification.
- Production API and tile origins to narrow CSP `connect-src`.
- Redistributable Devanagari fonts if consistent typography across unsupported devices is required.
- Farmer, FPO, and buyer participants for field usability and language review.

## Rollback

Revert the Packet 02 frontend foundation and CI/documentation changes together. The predecessor style files (`frontend/src/index.css` and `frontend/src/styles/experience.css`) were removed; recover them from the Packet 02 base revision if rollback is needed. Reinstall the previous frontend dependency set from that revision's `package.json` and lockfile. Do not roll back prior Packet 00/00A/01 work as part of this packet rollback.

## Deferred decisions

- Narrow CSP to fixed deployment origins once frontend API and tile-host configuration is known.
- Run live Nginx/Vercel security-header probes and Lighthouse/Core Web Vitals on a provisioned deployment.
- Validate contrast, translation, and task completion with farmers/FPOs/buyers across target devices and assistive technology.
- Consider Storybook only if component inventory and contribution workflow grow beyond the adjacent component guide and unit tests.
- Broader JavaScript-to-TypeScript conversion remains outside this packet.

## Recommended next packet

Packet 03, only after review of Packet 02 and its external runtime limitations. Packet 03 was not started in this work.

## Git state

Branch remains `abdulrehman`. No commit or push was made. The working tree also contains prior Packet 00/00A/01 changes and pre-existing modifications; they were preserved and not reset. Review the shared working tree before any later checkpoint.
