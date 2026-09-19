# Work Packet 00 plan — repository truth and baseline

## Scope

Audit the current `abdulrehman` checkout without implementing Packet 01 or future product features. Treat code, migrations, runtime behavior, tests, configuration, and git history as evidence. Preserve existing functionality and all pre-existing working-tree changes.

## Current state at start

- Branch: `abdulrehman` at `9d61c0e`.
- Pre-existing working tree changes: modified `AGENTS.md`; untracked `docs/krishilink-v4/` specification and work-packet files. These are user-provided inputs and will not be rewritten.
- `main` is at `4304286`; the current branch is five commits ahead and contains large backend hardening/trade-room work plus a substantial frontend simplification.
- Historical documentation conflicts with current branch and test-count claims; all claims require re-verification.
- Local frontend/backend were runnable before this packet, with backend falling back to SQLite because local PostgreSQL was unavailable.

## Intended changes

Documentation and reproducible evidence only:

1. Write a branch-diff inventory and identify specific `main` components/behaviors worth selective recovery.
2. Map architecture, routes, APIs, data models, migrations, state machines, providers, environments, and frontend/backend contracts.
3. Produce a capability matrix using the required statuses: VERIFIED WORKING, PARTIAL, BROKEN, UNREACHABLE, MISSING, EXTERNAL DEPENDENCY, and SECURITY/PRODUCTION BLOCKER.
4. Capture dependency/SBOM, database schema/ERD, security/provider, test, API, accessibility, performance/Lighthouse, CI/CD, observability, and deployment baselines.
5. Create a baseline backup as repository metadata (commit/tree/branch/diff hashes and generated inventories), without copying secrets or mutable databases.
6. Record all commands, passes, failures, skips, limitations, and rollback instructions in `docs/work/00-result.md`.
7. Update `PROGRESS_TRACKER.md` only with a concise Packet 00 result if doing so does not overwrite historical context.

## Expected files affected

- `docs/work/00-plan.md`
- `docs/work/00-result.md`
- `docs/work/00-capability-matrix.md`
- `docs/work/00-architecture-and-data.md`
- `docs/work/00-baseline-evidence.md`
- `docs/product/capability-register.md` if needed to satisfy the referenced master-spec baseline requirement
- `PROGRESS_TRACKER.md` (append-only Packet 00 note)

No application code, endpoint, model, or migration changes are planned.

## Database and migration risk

- Read-only schema and migration inspection.
- Migration upgrade/downgrade checks may create disposable local/test databases only.
- No manual DDL and no production database access.
- SQLite results will be identified separately from PostgreSQL/PostGIS behavior; unavailable infrastructure will be reported, not inferred.

## Verification plan

- Backend: `python -m pytest -v`, `python -m ruff check app`, `python -m mypy app`, Alembic head/history and safe migration checks where the environment permits.
- Frontend: `npm run lint`, `npm run test`, `npm run build`, Playwright E2E/axe, route and API behavior inspection.
- API: generate/inspect OpenAPI, health endpoints, representative auth/RBAC and error-contract probes.
- Performance/accessibility: Lighthouse and axe where installed/runnable; otherwise record the exact missing dependency or browser constraint.
- Dependencies/security: package manifests/lockfiles, `npm audit`, Python dependency inventory and vulnerability audit if tooling/network permits, secret-pattern scan, provider/config inventory.
- Runtime/deployment: inspect Dockerfiles, Compose, CI, environment examples, health behavior, and production configuration safeguards.

## Stop conditions

Stop after Packet 00. External credentials, legal review, production infrastructure, provider approval, or unavailable tooling will be documented as dependencies and will not be simulated.
