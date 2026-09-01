# KRISHILINK — CHANGELOG

All notable changes to the KrishiLink codebase are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0-audit] - 2026-09-01

### Added
- Created `docs/KRISHILINK_IMPLEMENTATION_AUDIT.md` providing a comprehensive system audit, verified test counts (73 passing tests), active vs dead architecture inventory, security analysis, and phased roadmap.
- Created `docs/IMPLEMENTATION_STATUS.md` for real-time tracking of domain capabilities and release gates.
- Created `docs/PRODUCT_DECISIONS.md` recording foundational engineering and architectural decisions (ADRs).
- Verified `KrishiLink_Master_Product_Build_Specification_v3.md` across root and `docs/` paths.

### Verified
- Automated test suite: 73 passed in 7.12s (`backend/tests/`).
- Frontend production bundle: 0 errors in Vite 8 build (`dist/`).
- Python static typing: 0 errors in 58 files (`mypy app`).
- CI configuration: Clean Postgres/PostGIS, Redis, Alembic, Ruff, Mypy, and Pytest pipeline in `.github/workflows/ci.yml`.

### Identified for Remediation (Phase 0.5)
- `SEC-01`: Rate limiting on `POST /api/v1/auth/refresh`.
- `SEC-02` / `SEC-03`: Server-side logout session revocation & frontend API trigger.
- `SEC-04` / `SEC-05`: Automatic JWT refresh token renewal on 401 & boot session revalidation via `GET /auth/me`.
- `SEC-06`: Idempotency key scoping to `(user_id, endpoint_path, key)`.
- `SEC-07` / `SEC-08`: Reverse proxy IP header extraction and in-memory bucket eviction in rate limiter.
- `SEC-09`: Production debug & OpenAPI documentation gating.
- Hygiene: Removal of dead legacy Flask dependencies/files and dead frontend `lib/apiClient.js`.
