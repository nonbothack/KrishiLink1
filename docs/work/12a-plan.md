# Packet 12A — Web Push Completion Plan

## Scope
Close Packet 12's known Web Push gap only. Preserve the existing notification/outbox, authentication, service-worker cache policy, offline write prohibition, and Packet 12 experience features. Do not start Packet 13.

## Current evidence
- `NotificationService.create_notification` persists a canonical Notification and its OutboxEvent in the same transaction.
- `outbox.process_pending` claims events with `FOR UPDATE SKIP LOCKED`; it currently publishes to the existing event stream and has legacy SMS dispatch only.
- The service worker caches only shell/static GET assets and never queues/replays writes.
- Authenticated notification reads are scoped to `user.id`; the frontend logout currently clears credentials immediately and does not reconcile browser push state.
- No push subscription or provider delivery models/API exist. Packet 12 result records this gap as FAIL.

## Design decisions
1. Add user-owned subscription records keyed by a SHA-256 endpoint digest, plus per-notification/per-subscription delivery receipts and immutable attempt rows. Persist endpoint/key values only in the subscription record; do not expose them in logs or responses.
2. Use `pywebpush==2.5.0` behind a server-only adapter. Keep disabled/unconfigured as truthful states; no mock delivery adapter in production.
3. Expose authenticated capability, subscribe/upsert, explicit same-browser reconciliation, unsubscribe, and admin/operator aggregate health endpoints. Never accept a user ID from the client.
4. Validate HTTPS push endpoints against an explicit push-service host allowlist to prevent SSRF. Permit same-owner endpoint refresh; reject active cross-account ownership unless the old owner's association was revoked and the new user explicitly subscribes.
5. Dispatch only existing `NOTIFICATION_*` outbox events to a dedicated worker task. Build a minimal localized payload from the canonical Notification; never use user-supplied message text for push. Persist deduplicated delivery receipts and bounded outcomes; revoke subscriptions on 404/410.
6. Add `push` and `notificationclick` handlers to the existing service worker. Display only safe category templates and allow only validated same-origin application paths; preserve GET-only caching and never add background sync or mutation replay.
7. Put explicit permission controls in authenticated farmer settings. No prompt on mount/login. Logout performs bounded best-effort server revoke and local unsubscribe before clearing the user session. On later authenticated mount, reconcile only when browser permission is already granted and a subscription already exists.
8. Use English/Hindi/Marathi templates and UI labels. Price alerts may include only public report facts; offer/trade/support pushes remain generic.

## Planned files
- Backend: models, config/env examples, push provider/service/schemas/router, worker dispatch, Alembic migration, focused tests, requirements pin.
- Frontend: push preferences component/helper/tests, translations, authenticated farmer settings placement, logout cleanup, service-worker push/click handlers and tests, private-key scan extension.
- Evidence: this plan, canonical `docs/work/12-result.md`, and `PROGRESS_TRACKER.md`.

## Verification
Run targeted push tests; full backend suite; Ruff, mypy and compile; frontend lint/unit/build/E2E, bundle/offline/security checks, TypeScript/format if binaries are present; Alembic head/history and offline PostgreSQL SQL generation; secret scan and `git diff --check`. Report PostgreSQL execution and live internet push separately if unavailable.

## Risks / non-goals
- Real browser delivery requires production VAPID credentials, HTTPS, a push-capable browser, and network access; tests will inject a fake sender only at the unit boundary.
- SQLite tests cannot establish production PostgreSQL lock behavior.
- No WhatsApp/IVR/SMS changes, PWA background sync, push-triggered financial action, Packet 13 work, commit, or push.
