# Packet 12 — Offline, Multilingual Voice and Reach

**Status: PASS_WITH_EXTERNAL_DEPENDENCY**

The initial Packet 12 result was `FAIL` because Web Push had no subscription or delivery pipeline. **Packet 12A below closes that software gap** by adding explicit account-scoped browser subscriptions, persistence, notification/outbox dispatch, deduplicated delivery attempts, and service-worker display/click behavior. Real internet delivery remains externally unverified because this environment has no VAPID credentials and does not have the pinned `pywebpush` runtime package installed. No mocked push or SMS response is presented as production delivery.

## Implemented behavior and acceptance evidence

### Installable shell and truthful cached data

- Added a standalone PWA manifest, reviewed local SVG icon, generated shell asset list, offline fallback page, and production-only service-worker registration/update UI.
- The service worker handles same-origin `GET` requests for the allowlisted app shell/static assets only. It does not cache API responses, authenticated user data, evidence files, signed URLs, or mutation requests. There is no Background Sync handler.
- Public crop catalogue and reported-price responses are cached in bounded IndexedDB snapshots only after successful API responses. On a network failure, the price surface can use that saved response and retains its report date, source, unit, and local cache time. Private user resources do not fall back to shared cache.
- `npm run check:pwa` passed against a production preview. Browser inspection found the shell and four entry assets cached, with `apiCached: false`; the offline root rendered. Browser logs showed expected offline failures for an uncached harvest image and the public crops API, not an API cache hit.
- A successful response was not asserted as live, current, or guaranteed; cache time and upstream report time remain distinct.

### Offline lot queue and isolation

- IndexedDB contains a dedicated queue with `LOT_CREATE` as its only operation, schema version 1, a strict field allowlist, farmer owner ID, idempotency key, creation time, and explicit `QUEUED`/`NEEDS_REVIEW` states.
- Queue bounds are five listings per farmer, 25 total, 16 KiB per payload, 30 days of age, and five manual attempts. Capacity errors do not silently evict work.
- The Sell flow allows an offline review and a separate explicit “save for sending later” action. It does not claim publication, compute a contractual quote/gross offline, or queue FPO, offer, trade, payment, verification, notification, or other state-changing requests.
- Queue processing is foreground-only and user initiated. Before each request the UI checks the current farmer identity and the persisted local session identity against the queue owner. The API request uses the same idempotency key. Server authorization remains authoritative. Validation/auth/conflict conditions stop automatic retries and require review; retry exhaustion/expiry similarly requires review.
- `npm run test:e2e` passed all **26** desktop/mobile browser tests in **5.4 minutes**. Packet 12 journeys verified that A’s saved lot and simple-mode preference are absent for B, return for A, do not post when connectivity returns, and post only after A explicitly requests sync with the original idempotency key. The test server accepted exactly one listing.
- This is an offline queue, not full offline synchronization. The tested workflow transitions an already-open app offline; uncached route chunks and provider-dependent views are not claimed to work in a cold offline launch.

### Remote-action security and provider truth

- No incoming SMS, WhatsApp, voice, or push action handler was added. SMS/notification routes are not offer-acceptance, counter, payment, trade, or account-action routes; a backend route-surface regression test checks this boundary. Consequential actions continue to require the normal authenticated application APIs.
- SMS disabled/demo mode now returns `success: false`, `status: DEMO`, and `provider: demo`, without returning the recipient phone or message content. It makes no carrier request. Configured external provider response tests remain mocked unit tests and are not evidence of actual delivery.
- Browser dictation is opt-in, requires an explicit disclosure/consent control, and can only fill a draft location field; it cannot submit a form. Browser speech recognition may process audio outside KrishiLink depending on the browser provider. Read-aloud is user-triggered and only available when the device exposes a matching language voice.
- The original Packet 12 implementation had no Web Push subscription or send pipeline; Packet 12A closes this gap below. WhatsApp and IVR remain separate provider sub-packets. No delivery-ready/sent claim is made for those external channels or hosted KrishiLink TTS.

### Language, simple mode, and accessibility

- New offline queue, stale/cache, simple-mode, PWA update, and browser speech copy uses the existing English/Hindi/Marathi translation infrastructure. Simple-mode preference is keyed by farmer account ID.
- E2E checked English, Hindi, and Marathi `lang` behavior and horizontal overflow at 360×640, 390×844, 768×1024, and 1440×900. Axe checks passed at 360×640 on the queue screen. A component test verified dictated text only populates a field and never submits.
- Automated checks do not constitute native-speaker review or a manual screen-reader/device-browser speech review; those remain follow-ups.

## Verification

| Command | Result |
|---|---|
| `python -m pytest -q -o addopts=` (fresh isolated SQLite DB) | **209 passed, 0 failed, 0 skipped** in 816.36 seconds; one `pytest-asyncio` deprecation warning. SQLite does not establish PostgreSQL locking behavior. |
| `python -m ruff check app` | Passed. |
| `python -m mypy app` | Passed: no issues in 89 source files. |
| `python -m compileall -q app alembic/versions` | Passed. |
| `npm run lint` | Passed. |
| `npm run test` | Passed on final verification: 12 files, 40 tests. |
| `npm run test:e2e` | Existing Packet 12/whole-journey suite passed: 26 desktop/mobile tests; the new `e2e/packet12-web-push.spec.js` passed separately on desktop and mobile (2 more executions). |
| `npm run build` | Passed: Vite build, service-worker generation, 20 public-route prerenders, SEO rendering, provider-key scan, and offline/provider-truth checks. |
| `npm run check:bundle` | Passed: initial JS **141.55 KiB gzip / 150 KiB**; initial JS + CSS + static assets **150.38 KiB gzip / 400 KiB**. |
| `npm run check:pwa` | Passed: production preview installed shell and rendered offline root; no API cache. |
| `npm run check:offline` | Passed. |
| `npm run check:security` | Passed: 6 static security headers and baseline CSP directives. |
| `git diff --check` | Passed; Git emitted normal LF→CRLF working-copy notices. |
| `npm run typecheck` | Unavailable: repository-local `tsc` executable is not installed (`'tsc' is not recognized`). |
| `npm run format:check` | Unavailable: repository-local `prettier` executable is not installed (`'prettier' is not recognized`). |

The final full pytest rerun used a fresh isolated SQLite database and returned its count summary. The only warning was the installed `pytest-asyncio` deprecation for `asyncio.get_event_loop_policy`.

## Migrations, APIs, and infrastructure

- Packet 12 itself added no database migration. Packet 12A adds the additive migration `d73f2c91a604` for subscriptions, deduplicated delivery receipts, and attempt history. `python -m alembic heads` reports this single head; offline PostgreSQL SQL generation for `b611e2a7c930:d73f2c91a604` succeeded and the generated table/constraint/index SQL was inspected.
- No PostgreSQL/PostGIS migration execution or row-lock race verification was performed. Redis/Celery production runtime, actual browser-to-push-service internet delivery, VAPID key provisioning, production SMS, and handset delivery remain external/unavailable. The pinned `pywebpush==2.5.0` dependency is declared but is not installed in this local Python runtime. Web Push reports unavailable until dependency, feature switch, and VAPID values are configured.
- The production build omitted absolute canonical/sitemap URLs because `PUBLIC_SITE_URL` is unset. It omitted dynamic crop/outlet prerenders because the API was unavailable; it did not substitute sample data.

## Files changed for Packet 12

- Backend: `backend/app/modules/notifications/sms_service.py`; `backend/tests/test_sms_service.py`.
- Frontend PWA/offline: `frontend/index.html`; `frontend/package.json`; `frontend/public/manifest.webmanifest`; `frontend/public/icons/krishilink.svg`; `frontend/public/offline.html`; `frontend/public/service-worker.js`; `frontend/scripts/generate-service-worker.mjs`; `frontend/scripts/check-pwa-browser.mjs`; `frontend/scripts/check-offline-safety.mjs`.
- Frontend behavior/components: `frontend/src/App.jsx`; `frontend/src/layouts/DashboardLayout.jsx`; `frontend/src/pages/SellPage.jsx`; `frontend/src/pages/FarmerMorePage.jsx`; `frontend/src/pages/FarmerDashboard.jsx`; `frontend/src/components/RateLookup.jsx`; `frontend/src/components/OfflineLotQueue.jsx`; `frontend/src/components/PwaLifecycle.jsx`; `frontend/src/components/VoiceControls.jsx`; `frontend/src/lib/offlineStore.js`; `frontend/src/lib/offlinePresentation.js`; `frontend/src/lib/experiencePreferences.js`; `frontend/src/services/api.js`; `frontend/src/utils/copy.js`; `frontend/src/styles/app.css`.
- Frontend tests: `frontend/src/lib/offlineStore.test.js`; `frontend/src/services/offline-cache.test.js`; `frontend/src/components/VoiceControls.test.jsx`; `frontend/src/utils/copy.test.js`; `frontend/e2e/packet12-offline.spec.js`.
- Evidence: `docs/work/12-plan.md`; this result; `PROGRESS_TRACKER.md`.

## Risks and rollback

- Device/browser IndexedDB can be cleared, unavailable, or shared at the OS/browser profile level; local queue storage is owner-scoped, not encrypted. Users must retain control of their signed-in account and device.
- The safe service worker caches only the app entry graph and static shell; this is not broad route-level offline access. Browser-native speech behavior/voice availability varies by device and browser.
- Web Push capability remains off/unavailable until the runtime installs the pinned provider library and an operator configures VAPID credentials/subject and enables the switch. Real push-service delivery and browser receipt have not been verified. Production SMS delivery requires a deliberately configured provider and credentials; provider acceptance is not handset delivery. WhatsApp and IVR require separate provider integrations.
- Rollback: revert the Packet 12 frontend/backend changes and deploy the previous release. To clear an already-installed client worker during a forward rollback, deploy a worker version that unregisters itself and deletes only KrishiLink-owned cache names; advise affected users to reopen the site online before relying on the old shell. IndexedDB queue removal must be communicated because clearing it deletes unsent farmer drafts; do not silently clear it as part of rollback.

## Git state and next step

Working branch: `abdulrehman`. No commit or push was made. The repository contains substantial earlier-packet working-tree changes; this result does not attribute them to Packet 12A. Packet 12 is closed locally with an external provider verification dependency. Packet 13 was not started.

## Packet 12A — Web Push completion

### Implementation

- Added `web_push_subscriptions`, uniquely keyed by a SHA-256 endpoint digest and owned by the authenticated user. Endpoint and encryption keys are never returned by APIs or included in delivery attempts/log fields. Multiple browsers/devices can have separate rows. Same-owner registration updates language/key material; active cross-account reassignment requires the authenticated user's explicit subscribe action and records an audit event. Passive reconciliation revokes a stale previous-account association and asks for a fresh explicit action instead of transferring it silently.
- Added authenticated capability, register, reconcile, and current-device revoke APIs. The client cannot submit an owner ID. An aggregate-only operator health endpoint is limited to admin/operator roles. Endpoint validation requires HTTPS, port 443/default, and configured push-service hosts; credentials/userinfo, local/private hosts, unsupported hosts, malformed VAPID keys, and excess input are rejected.
- Added operator configuration for an independent kill switch, public VAPID key, `SecretStr` private VAPID key, subject, host allowlist, and bounded attempts. The private value is server-only. The standards-based `pywebpush==2.5.0` adapter is pinned; no encryption/VAPID cryptography was hand-written. [The upstream pywebpush project](https://github.com/web-push-libs/pywebpush) and [its package release](https://pypi.org/project/pywebpush/) document the maintained Web Push implementation used here.
- Added an outbox consumer for existing `NOTIFICATION_*` events. It queues a dedicated worker task using the canonical persisted Notification ID; it never sends in an HTTP request or creates a parallel notification. A unique notification/device delivery receipt prevents repeat sends after a recorded success. Attempt rows record attempt number, status category/code, and start/completion times without storing endpoint, payload, or provider error text.
- Transient provider outcomes use bounded retry receipts and a 60-second Celery retry sweep. Provider 404/410 outcomes mark the receipt gone and revoke the subscription; permanent 4xx outcomes fail without retry. Leases and row locks protect concurrent task claims, with database uniqueness as the final deduplication guard. PostgreSQL concurrency was statically reviewed, not executed locally.
- The authenticated notification settings page is available to all roles. It checks capability without prompting; permission is requested only after the user selects “Turn on notifications.” Logout makes a bounded best-effort server revoke while credentials remain available and removes the local browser subscription even offline. An existing permission/subscription never silently reassociates across accounts.
- Push messages use localized EN/HI/MR category summaries. Offer, trade, and support messages contain no counterparty PII, money, dispute text, payment reference, or evidence. Price-alert summaries include only canonical public reported-price facts when all fields are present; the threshold and user-specific location are excluded.
- The service worker validates a versioned payload, bounds displayed strings, falls back safely for malformed data, and opens only allowlisted same-origin app routes. The existing GET-only shell/static cache and no-background-sync/no-write-replay behavior are unchanged. Normal application authentication and object authorization still govern opened routes.

### Packet 12A verification

- Backend: 7 focused Web Push tests cover authenticated subscription ownership/reassociation, endpoint/key validation, private-key non-disclosure, localized private-safe payloads, existing Notification/outbox dispatch, success deduplication, transient retry, 410 invalidation, and aggregate operator health. Full regression: **209 passed, 0 failed, 0 skipped**.
- Frontend: 8 new unit tests cover no automatic permission prompt, explicit opt-in, unavailable provider state, account reassociation consent, key decoding, unsupported browsers, and local unsubscribe on logout. Full Vitest suite: **40 passed**.
- Service worker: 2 tests cover safe notification rendering, internal click navigation, malformed payload fallback, and external destination rejection. Browser coverage: **2 tests passed** on desktop and mobile; it proves no prompt on page load, explicit A subscription, local cleanup after server revoke failure, no automatic B reassociation, explicit B subscription, all three languages, no horizontal overflow at 360/390/768/1440 px, and a 48 px control.
- Existing offline regression: all **26** desktop/mobile Playwright tests passed. Production PWA browser check confirmed the shell/entry assets are cached, API paths are not cached, and the offline shell still renders.
- Production build passed SEO prerender/render checks, private-key scan, and offline/provider-truth checks. Initial JS is **141.55 KiB gzip**, within the 150 KiB budget. Static security-header/CSP check passed.
- Alembic graph has one head (`d73f2c91a604`). Offline PostgreSQL SQL generation succeeded. No live PostgreSQL/PostGIS migration, locking test, Redis/Celery worker runtime, actual Web Push network send, or real device receipt was available. `pywebpush` is not installed in this host runtime; the dependency pin is present in `backend/requirements.txt`.
- TypeScript and Prettier checks remain unavailable because local executables are missing. `git diff --check` passed; Git emitted only the repository's normal LF-to-CRLF working-copy notices.

### Packet 12A files

- Backend: `backend/app/core/config.py`, `backend/app/models.py`, `backend/app/modules/notifications/router.py`, `backend/app/modules/notifications/web_push_schemas.py`, `backend/app/modules/notifications/web_push_provider.py`, `backend/app/modules/notifications/web_push_service.py`, `backend/app/workers/celery_app.py`, `backend/alembic/versions/d73f2c91a604_web_push_delivery.py`, `backend/requirements.txt`, `backend/.env.example`, `backend/tests/test_packet12a_web_push.py`.
- Frontend: `.env.example`, `frontend/public/service-worker.js`, `frontend/scripts/check-offline-safety.mjs`, `frontend/scripts/check-price-key-secrecy.mjs`, `frontend/src/App.jsx`, `frontend/src/hooks/useAuth.jsx`, `frontend/src/layouts/DashboardLayout.jsx`, `frontend/src/pages/FarmerMorePage.jsx`, `frontend/src/pages/NotificationSettingsPage.jsx`, `frontend/src/components/WebPushPreferences.jsx`, `frontend/src/components/WebPushPreferences.test.jsx`, `frontend/src/services/webPush.js`, `frontend/src/services/webPush.test.js`, `frontend/src/test/service-worker-push.test.js`, `frontend/src/styles/app.css`, `frontend/src/utils/copy.js`, `frontend/e2e/packet12-web-push.spec.js`.
- Evidence: `docs/work/12a-plan.md`, `docs/work/12-result.md`, `PROGRESS_TRACKER.md`.
