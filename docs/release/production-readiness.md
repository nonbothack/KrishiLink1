# KrishiLink production readiness — Packet 15

**Engineering release candidate: READY**  
**Production launch approval: EXTERNAL SIGNOFF PENDING**

This is an internal release-candidate review for branch `abdulrehman`. It is
not production approval and does not claim certification, live provider
success, or completed disaster recovery.

## Executive decision

Packet 15B closed the remaining technical RC gates on the isolated Docker
Desktop rehearsal: the seeded PostgreSQL application race matrix passed, the
clean 30-minute soak recorded zero errors, and an immutable A→B→A→B rollback
ended with healthy API/frontend/worker services. RC_B is hardened to non-root
runtime users. The engineering candidate is ready for external and human
sign-off; production launch remains unapproved.

Historical Packet 15A `BLOCKED` evidence is retained in its own result and
rollback/concurrency records. It is not the current Packet 15B engineering
status.

## Evidence matrix

| Area | Status | Evidence |
|---|---|---|
| Branch/candidate manifest | VERIFIED LOCALLY | `release-candidate-manifest.json` |
| Production config fail-closed | VERIFIED LOCALLY | `backend/app/core/config.py`, disposable production API boot |
| Test DB isolation | VERIFIED LOCALLY | `backend/conftest.py`, full regression |
| Liveness/readiness contract | VERIFIED LOCALLY | `/api/v1/health`, `/api/v1/health/ready` |
| PostgreSQL/PostGIS migration | PASS — isolated | `evidence/migration-rehearsal.md` |
| PostgreSQL backup/restore | PASS — isolated | `evidence/database-restore.md` |
| PostgreSQL application races | PASS — isolated | `evidence/concurrency-rehearsal.md`, `packet15b-race-output.json` |
| Redis/Celery recovery | PASS — bounded | `evidence/failure-drills.md` |
| Private object storage | PASS — MinIO rehearsal | `evidence/failure-drills.md` |
| Clean 30-minute soak | PASS | `evidence/load-30m-clean.json`, `evidence/soak-test.md` |
| Two-version application rollback | PASS — local | `evidence/rollback-rehearsal.md` |
| Container runtime security | PASS — local | RC_B UID/capability inspection |
| VAPT/manual accessibility/legal/UAT | EXTERNAL/HUMAN DEPENDENCY | Requires named reviewers and deployed environment |

## Runtime notes

The final local rehearsal used the disposable Compose override that removes
bind mounts and Uvicorn reload from application services. This executes
immutable release images and is the documented local RC runtime; the source
Compose file retains development-oriented defaults and is not itself a
production deployment manifest.

RC_B backend/worker/Beat run as UID 100 `app`; nginx runs as UID 101 `nginx`.
Both images had zero effective/permitted/ambient capabilities in inspection.
Docker Scout is unavailable in the installed CLI, so no Scout vulnerability
result is claimed.

## Verification summary

- Backend: full `python -m pytest -q` completed with exit code 0; Ruff and
  mypy passed. The historical suite remains 222 tests; no failures or skips
  were reported.
- Frontend: lint, 40 Vitest tests, build, typecheck and 30 browser tests passed.
  PWA/offline/security/bundle checks and high-severity npm audit passed.
- Prettier format check remains a pre-existing failure on 65 files; Packet 15B
  touched files were checked without a broad rewrite.

## External launch gate

Production launch still requires deployed-environment VAPT, legal/privacy
approval, manual/native-language/accessibility review, provider contracts and
health evidence, production observability/RPO/RTO rehearsal, and stakeholder
UAT. These are external/human approvals, not unresolved engineering race or
rollback gates.

Packet 16 remains deferred.
