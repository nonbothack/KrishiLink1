# Packet 15B two-version rollback rehearsal

**Status: PASS — local immutable-image and PWA rehearsal**

The isolated Compose project executed this exact sequence without changing database schema or data:

1. Retained RC_A image IDs and PWA artifact snapshot.
2. Deployed RC_B and observed API readiness 200, frontend health 200, and healthy backend/worker/frontend containers.
3. Retagged the retained RC_A backend, worker, scheduler and frontend images, recreated the services, and observed API readiness 200 and frontend health 200.
4. Retagged RC_B, recreated the services again, and observed API readiness 200 and frontend health 200.

| Artifact | RC_A | RC_B |
|---|---|---|
| Backend | `sha256:72afcfba29f120913a77bde433d4754b921c595352ba87370cf221f8758563ca` | `sha256:ad01df7cb530d11a49a9d744e6ea73a06e49110a11a5259d5ce089cec5ebf74d` |
| Frontend | `sha256:d53312087b4878dbb7f79ea66220cf625971b0e9a8116a3983901d39969e5e72` | `sha256:dcd95357434053cff0293b3fbc1e1c2bfd62f5b4120477369c9960f6208c06ab` |
| PWA service worker | `26A348C8345F5DA5CA462302EA9265DF6565C1C4B0DAD5C648A523798D05EB9` | same shell hash; the immutable container artifact is distinct |

RC_B is the hardened candidate. Backend/worker/Beat run as UID 100 `app`; the frontend runs as UID 101 `nginx`. The identical service-worker content is intentional: the offline IndexedDB queue schema/cache contract did not change, so queued drafts survive an update/rollback. Existing browser evidence in `frontend/e2e/packet12-offline.spec.js` proves account-scoped draft isolation, foreground-only replay, and preservation across logout/account switch. No background mutation replay was introduced.

Database compatibility was verified by leaving the migrated PostgreSQL schema unchanged through every A/B switch and by the prior Packet 15A backup/restore and migration rehearsals. This is a local single-host rollback rehearsal; multi-node orchestration and production traffic draining remain external.

