# Packet 15B — Final Release-Candidate Gate Closure

## Status

**PASS_WITH_EXTERNAL_DEPENDENCY**

The engineering release candidate is READY. All Packet 15B technical hard
gates executed successfully on the isolated Docker/PostgreSQL rehearsal:
application races, clean soak, non-root runtime, immutable A→B→A→B rollback,
PWA safety, full backend/frontend regressions and browser smoke. Production
launch remains pending external/human approvals and deployed-environment
evidence.

## 1. Executive summary

Packet 15B closed the three Packet 15A release blockers. A focused
PostgreSQL-only application harness caught and fixed a stale ORM identity-map
race that could duplicate an accepted offer; the rerun passed. The clean
steady-state soak recorded 8,997 successful readiness requests with zero
errors. RC_A and RC_B were retained as distinct images, deployed, rolled back,
and redeployed with smoke after every transition. RC_B runs as non-root with
zero effective/permitted/ambient capabilities in local inspection.

## 2. Prior Packet 15A evidence retained

The migration, backup/restore, Redis/PostgreSQL outage, private MinIO,
production-config, qualified outage-overlap load run, and Packet 15A regression
evidence remain unchanged. The earlier `BLOCKED` result is retained at
`docs/work/15a-result.md` for audit history.

## 3. Seeded PostgreSQL test environment

A fresh `krishilink_packet15b` database was migrated to Alembic head
`e1f4a7b9c2d3` on the real PostGIS service. The harness used independent
sessions, thread barriers and the application service/router functions. It did
not use SQLite for race assertions. Raw redacted output is
`docs/release/evidence/packet15b-race-output.json`.

## 4–15. Application race matrix

- **Lot race:** two 8-qtl accepts against a 10-qtl lot produced one
  transaction, 8 qtl reserved, and one safe 409.
- **Requirement-overfill race:** two 8-qtl accepts against a 10-qtl buyer
  requirement left committed quantity at 8 qtl.
- **Accept/withdraw:** one terminal transition won; no duplicate trade.
- **Accept/counter:** counter and accept serialized; the original offer did
  not produce duplicate trades.
- **Expiry:** server-time expiry rejected both attempts; no transaction.
- **Duplicate acceptance/idempotency:** repeated key returned the original
  successful response; one transaction and one idempotency record.
- **FPO intake:** competing 6-qtl contributions against a 10-qtl receipt
  persisted only 6 qtl.
- **FPO pool sale:** concurrent acceptance serialized and produced one trade
  and one allocation set.
- **Allocation conservation:** a 1.000-qtl sale at ₹101/qtl reconciled to
  exactly 1.000 qtl and ₹101.00 with Decimal residual handling.
- **Outbox:** `FOR UPDATE SKIP LOCKED` allowed exactly one worker claim.
- **Web Push:** concurrent delivery produced one delivery receipt and one
  attempt for one notification/device pair.
- **Packet 13 fraud case:** the row-locked decision path allowed one terminal
  decision and returned 409 to the loser; fraud remains a review signal.

## 16. PostgreSQL isolation/locking conclusions

The harness verifies the relevant application lock paths on PostgreSQL. A
production multi-node race load, managed database failover and network fault
injection remain outside this local rehearsal.

## 17–19. Clean soak and resource growth

`CLEAN_STEADY_STATE_RUN` lasted 1,800 seconds at 5 RPS with no planned outage:
8,997 requests, 8,997 HTTP 200, zero errors, P50 6.59 ms, P95 8.89 ms,
P99 12.92 ms, maximum 112.23 ms. Backend memory was 244.9→246.5 MiB and
worker memory 464.7→527 MiB; PostgreSQL connections 10→11; Redis memory
2,226,352→2,350,160 bytes; outbox pending 0→0. Full data is in
`docs/release/evidence/load-30m-clean.json`.

## 20–22. Runtime hardening and capabilities

RC_B backend, worker and Beat run as UID 100 `app`; the frontend runs as UID
101 `nginx`. Backend and frontend had zero effective, permitted and ambient
Linux capabilities. Docker Scout is unavailable in the installed CLI, so no
Scout scan is claimed.

## 23–30. RC identities, deployment, rollback and PWA

- RC_A backend: `sha256:72afcfba29f120913a77bde433d4754b921c595352ba87370cf221f8758563ca`.
- RC_B backend: `sha256:ad01df7cb530d11a49a9d744e6ea73a06e49110a11a5259d5ce089cec5ebf74d`.
- RC_A frontend: `sha256:d53312087b4878dbb7f79ea66220cf625971b0e9a8116a3983901d39969e5e72`.
- RC_B frontend: `sha256:dcd95357434053cff0293b3fbc1e1c2bfd62f5b4120477369c9960f6208c06ab`.
- RC_B deployed and smoked 200; rollback to RC_A smoked 200; redeploy to RC_B
  smoked 200.
- PWA snapshots are retained under `docs/release/evidence/rollback-artifacts/`.
  The service-worker content hash is intentionally identical because the
  IndexedDB queue/cache contract did not change. Existing Packet 12 browser
  evidence proves account-scoped draft preservation and foreground-only sync;
  no background write replay is present.

## 31. Release smoke

After the final RC_B redeploy: backend readiness 200, frontend `/health` 200,
backend/frontend/worker healthy, scheduler running, PostgreSQL/Redis/MinIO
healthy.

## 32–33. Formatting and dependency status

Ruff passes. Global Prettier still reports 65 pre-existing files; no broad
rewrite was performed. Frontend `npm audit --audit-level=high` reported no
high-severity vulnerabilities. Docker Scout is unavailable and is explicitly
not claimed.

## 34–36. Regression and integration results

- Backend `python -m pytest -q`: exit code 0, 222 tests, no failures/skips
  reported; `python -m ruff check app` passed; `python -m mypy app` passed.
- Frontend `npm run lint`: passed; `npm run test -- --run`: 40 tests passed;
  `npm run build`: passed with PWA/offline/SEO/security/secret checks;
  `npm run test:e2e`: 30 passed in 4.7 minutes.
- Final integration smoke: API readiness and frontend health both returned 200
  after RC_B redeploy.

## 37–38. Release manifest and checker

`python scripts/create_release_candidate_manifest.py` and
`python scripts/check_release_candidate.py` are required after the final docs
and build state. The checker must continue to recognize the uncommitted,
evidence-controlled snapshot.

## 39–40. Blockers and engineering findings

Packet 15A engineering blockers are resolved. Remaining engineering findings
are the development-oriented source Compose defaults, pre-existing Prettier
debt and unavailable Docker Scout scan; these do not invalidate the isolated
RC_B rehearsal. No P0/P1 application race or rollback finding remains.

## 41. External sign-offs

Pending: deployed-environment VAPT, legal/privacy approval, manual/native-
language/accessibility review, real provider contracts and delivery evidence,
production observability/RPO/RTO rehearsal, and stakeholder UAT.

## 42–43. Release status

**Engineering RC: READY.**  
**Production launch: EXTERNAL SIGNOFF PENDING / NOT APPROVED.**

## 44. Files changed

- `backend/app/modules/offers/router.py` — refresh locked offer state before
  transition validation.
- `backend/app/modules/admin/router.py` — lock fraud-case decision rows.
- `backend/Dockerfile`, `frontend/Dockerfile` — non-root release image users.
- `scripts/packet15b_postgres_races.py` — PostgreSQL application race harness.
- `scripts/packet15b_clean_soak.py` — clean steady-state soak and resource
  snapshots.
- `docs/release/evidence/*` — Packet 15B race, soak and rollback evidence.
- `docs/release/production-readiness.md`, `docs/release/known-blockers.md`.
- `docs/work/15b-result.md`.

## 45. Packet 16 deferred scope

Packet 16 was not started. Any further product features, provider activation,
production deployment, or certification work requires a separate explicit
packet instruction.

## 46. Git status

Working tree remains uncommitted on `abdulrehman`. No commit, push or tag was
created.
