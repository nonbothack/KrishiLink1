# Work Packet 03 — Completion and Repository Evidence

**Overall status: PASS_WITH_EXTERNAL_DEPENDENCY**  
**Branch:** `abdulrehman`  
**Scope:** Geography, outlet provenance and crop registry only. Packet 04 was not started. No commit or push was made.

## 1. Executive summary

Implemented structured Indian administrative geography references, an auditable data-source registry, confidence-gated outlet publication, a review-first strict CSV importer, and an expanded canonical crop registry with multilingual labels, aliases, supported units and tradable status. Existing `markets` and crop records are retained to preserve price-history foreign keys. Unknown or legacy information remains explicitly unknown/reviewable rather than being promoted into trusted data.

No outlet dataset was imported. The repository's `List_Of_APMC.csv` cannot be decoded as UTF-8 and has no verified publisher or license terms. A small trustworthy registry is preferable to inflated counts; no target count or fabricated coordinates were used. External authoritative, license-cleared LGD/outlet sources and a PostgreSQL/PostGIS runtime remain necessary before production rollout.

## 2. Geography

Added `geo_states`, `geo_districts` and `geo_subdistricts`, with optional LGD codes, language labels, source references and hierarchy constraints. Added nullable structured IDs to users and markets while retaining their legacy text fields. Removed the implicit Maharashtra default so an unknown state stays unknown. Geography lookup endpoints return only exact hierarchy matches; there is no city-name-to-district guess or fallback coordinate.

No geography seed rows were added because this checkout contains no authoritative, versioned LGD snapshot. Coordinates must be in India bounds at review and publication time. User location coordinates are not inferred from entered text.

## 3. Outlet registry and provenance

The existing `markets` table remains the canonical outlet entity, retaining price observation relationships. New source identity, outlet type, normalized name, structured geography, coordinate/source confidence, verification state and review metadata support review and audit. Existing outlets are preserved as `needs_review`; legacy coordinates are labeled `unknown_legacy` with null confidence. The public market list and nearby results include only active verified outlets with coordinate and source confidence of at least 0.85. PostgreSQL nearby filtering and distance use PostGIS geography operations; SQLite tests use Haversine for deterministic test behavior.

An admin/operator review queue and quality summary expose evidence gaps, confidence coverage, invalid bounds, stale reviews and suspicious coordinate clusters. Publication requires an approved/not-applicable source, explicit coordinate provenance and confidence, source confidence, India-bounded coordinates, and a consistent state/district mapping with LGD codes. Review and source registry mutations are audited.

The importer requires UTF-8 CSV input, a registered active source with acceptable terms, required identity/region fields, parser version and source metadata. It applies deterministic source references, validates coordinates and supplied hierarchy, reports rejected/review rows, and never geocodes or fuzzy-merges. Imported rows receive no numeric confidence by default: a coordinate in a file is not evidence of accuracy by itself. Missing or unassessed coordinates and sources leave candidates unpublished. Supplied LGD codes are cross-checked against the row's administrative labels.

## 4. Crop registry

Expanded existing crops with stable slugs, aliases, Hindi/Marathi display labels, AGMARKNET labels, supported units, and active/tradable flags; expanded varieties and added optional crop quality specifications. The migration preserves existing crop IDs and historical references, normalizes unsupported legacy units to the canonical quintal default, and seeds multilingual metadata only for the nine crop labels already shipped in the frontend. Unknown price-feed commodities are retained as inactive, non-tradable records and cannot be selected in public crop APIs or tradable lot/FPO flows.

Frontend crop selection now uses the canonical API registry for rates, sell listings and FPO lot flows. `UNIT_FACTORS` remains a unit conversion utility, not a duplicate crop catalogue.

## 5. Migration and import behavior

Added Alembic revision `c4e83d2f1a60` after `790546cf29fe`. It creates the geography/source/quality tables, extends users/markets/crops/varieties, backfills existing crop metadata and marks old outlets for review without deleting rows or observations. Existing outlet source links are reconstructed only where a price observation provides a source trail; their license status remains `unknown`.

The revision compiles and Alembic history resolves to the new head. PostgreSQL/PostGIS upgrade and downgrade were not run because this environment has no provisioned PostgreSQL/PostGIS service. SQLite migration upgrade is also not claimed: prior repository findings document application imports eagerly creating current-schema tables in SQLite before Alembic runs, which makes that route an invalid migration test here. Production migration execution must be tested on a representative PostgreSQL/PostGIS copy before deployment.

No current APMC file rows were imported, and no migration ran against the existing `backend/krishilink.db`. Test execution used a separate scratch SQLite database.

## 6. API and contracts

- `GET /api/v1/geo/states`, `/districts`, `/subdistricts` and exact `resolve` operations expose only registered reference data.
- `GET /api/v1/crops`, crop detail and alias resolution expose active/tradable canonical crop entries and their localized/quality metadata.
- Public `/api/v1/markets` and `/locations` mandi results gate on verified status and confidence. Nearby query coordinates must be supplied as a pair, be within India bounds and use a bounded radius.
- Admin/operator market review and quality routes are role-protected. Source registry writes are admin-only; approved source terms require license evidence.
- Price ingestion resolves canonical crop aliases and retains unknown crop observations under non-tradable records. Market labels without authoritative outlet identity remain review candidates.

## 7. Quality rules

Correctness and evidence govern publication, not import count. Source license must be approved or explicitly not applicable; unknown/restricted sources cannot be used for public outlets. Source and coordinate confidence must each be explicitly assessed at 0.85 or higher, coordinates must be attributable and in bounds, and administrative references must be internally consistent. Ambiguous names are not fuzzy-merged. Invalid encodings, missing required identity, invalid coordinates and unapproved sources are rejected or left in review with row-level outcomes. No sample data, guessed coordinates, hardcoded confidence values or fallback outlet pins are generated.

## 8. Capability matrix

| Area | Packet 03 finding/status | Evidence / boundary |
|---|---|---|
| Authentication and authorization | PARTIAL; geography IDs validated when supplied; review/source routes role-gated | `auth/service.py`, `markets/router.py`; legacy free-text registration remains compatible and is not authoritative geography |
| Sessions/token handling | VERIFIED relative to prior baseline; unchanged in this packet | Existing auth/session implementation; Packet 03 does not re-audit Packet 00A remediation |
| Farmer experience | PARTIAL | Sell crop list consumes canonical API; no authoritative geo selector data exists |
| Buyer experience | PARTIAL | Existing flows retained; no new buyer-specific geography experience |
| FPO experience | PARTIAL | FPO crop choices use registry; aggregation resolves aliases and rejects non-tradable crops |
| Prices | PARTIAL | Ingestion normalizes crops; historical price observations remain linked; no new price-provider data is claimed |
| Geography/location | PARTIAL | Hierarchy schema and exact APIs implemented; authoritative LGD data absent |
| Mandi/outlet data | PARTIAL / EXTERNAL DEPENDENCY | Source/review/import pipeline implemented; existing rows are unverified and current CSV unusable |
| Lots | VERIFIED contract integration for crop eligibility | Lot flow resolves canonical tradable crops; unrelated lot lifecycle retained |
| Matching | PARTIAL, preserved | Canonical crop resolution integrated; no new matching feature or production dataset |
| Offers | VERIFIED relative to prior baseline; unchanged | Packet 03 does not change offer lifecycle |
| Trades/trade room | VERIFIED relative to prior baseline; unchanged | Packet 03 does not change trade lifecycle |
| Payments | PARTIAL / EXTERNAL DEPENDENCY | Existing provider limits remain as documented in prior packet results |
| Logistics | MISSING as a verified outlet/geography dataset | No authoritative logistics registry supplied |
| Storage | PARTIAL | Existing records/routes retained; no source/coordinate trust rollout for storage records |
| Quality | PARTIAL | Crop specification schema and admin outlet-quality reporting exist; no authoritative grade dataset imported |
| Disputes | VERIFIED relative to prior baseline; unchanged | Packet 03 does not change dispute lifecycle |
| Notifications | VERIFIED relative to prior baseline; unchanged | Packet 03 does not change notification lifecycle |
| Admin | PARTIAL | Audited source registry, outlet queue, review action and quality report added |
| i18n | PARTIAL | Canonical crop registry supports English/Hindi/Marathi; geography records await sourced localized labels |
| Accessibility | VERIFIED relative to Packet 02 baseline; unchanged | Packet 03 adds no new interaction-heavy UI |
| Offline/PWA | PARTIAL per prior baseline; unchanged | No new offline data or write queue introduced |
| Tests | VERIFIED for current repository tests | Full backend suite, focused provenance tests, frontend unit tests; see §9 |
| CI/CD | PARTIAL per prior baseline; unchanged | Local checks pass; no CI run because nothing was pushed |
| Security | PARTIAL | Role gates, confidence gates and audit records added; migration/runtime and source governance still need production verification |
| Observability | PARTIAL | Admin quality counters and importer row outcomes added; no external telemetry stack verified |
| Deployment | EXTERNAL DEPENDENCY for database rollout | Frontend build passes; PostgreSQL/PostGIS migration/runtime unavailable |

## 9. Tests and verification

Commands run:

- `$env:DATABASE_URL='sqlite:///C:/abdul/backend/packet03_test.db'; python -m pytest -q`: full backend suite passed, no failures and no skips. This checkout's prior 125-test baseline plus seven Packet 03 focused tests yields 132 passing tests. One Python 3.14 `pytest-asyncio` deprecation warning was emitted.
- `$env:DATABASE_URL='sqlite:///C:/abdul/backend/packet03_test.db'; python -m pytest tests/test_packet03_geography_registry.py -q`: 7 passed; covers unresolved/exact geography, crop alias/localization and unknown crop, strict/idempotent importer and source/encoding/coordinate rejection, verified-only nearby results, and review authorization/provenance.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm test -- --run`: 4 test files, 18 tests passed, including canonical multilingual crop selector coverage.
- `cd frontend && npm run build`: passed (Vite production build).
- `cd backend && python -m ruff check app`: passed.
- `cd backend && python -m mypy app`: passed, 74 source files.
- `python -m compileall -q backend/alembic/versions/c4e83d2f1a60_geography_outlet_crop_registry.py`: passed.
- `cd backend && python -m alembic history -r c4e83d2f1a60:`: passed; parent/head chain is `790546cf29fe -> c4e83d2f1a60`.
- `git diff --check`: passed; only Git LF/CRLF working-copy notices were emitted.
- PostgreSQL/PostGIS integration and Alembic upgrade/downgrade: not run; service unavailable, not counted as a passing test.
- Frontend E2E, Docker/Compose runtime and live API checks: not run for this packet; no relevant running PostgreSQL/PostGIS stack was available and no new full user journey was added.
- An intermediate full-suite rerun caught a `NameError` in the newly added importer test assertions; the test setup was corrected, the focused tests passed, and the final full backend rerun passed. No application test failure remained.

## 10. PostGIS

The model retains the PostGIS geography column and GIST indexing. Nearby market filtering/distance in PostgreSQL uses `ST_DWithin`/`ST_Distance` over geography; low-confidence or unverified outlet coordinates are excluded before spatial ranking. SQLite tests verify deterministic behavior with actual Haversine distance, not PostGIS execution. Spatial SQL compilation/runtime and index query plans require validation on the deployment PostGIS version before release.

## 11. Regressions

No regressions were observed in the full existing backend test suite, frontend tests, lint or build. All pre-existing outlet and crop references are preserved. Existing unverified market rows no longer appear as trusted public outlet pins; this is an intentional safety correction. Historical/import data whose crop alias is unknown remains stored but is not surfaced as tradable.

## 12. Production blockers and security issues

- **SECURITY/PRODUCTION BLOCKER:** no approved source licensing evidence exists for the checked-in APMC file; it is not imported or published.
- **PRODUCTION BLOCKER:** no authoritative LGD state/district/subdistrict snapshot is bundled, so structured hierarchy selection and outlet publication will remain empty until supplied.
- **PRODUCTION BLOCKER:** PostgreSQL/PostGIS migration and spatial query behavior have not been exercised in this environment.
- Existing public buyer/storage/FPO map surfaces were not redesigned by this packet; their data-governance and coordinate-provenance needs remain for a separately scoped review. Packet 00/00A findings about unrelated provider/auth risks remain as previously documented.
- Source license approval is an admin operation and is audited, but deployment governance must ensure the reviewer has actual legal evidence; the application cannot determine the truth of license terms by itself.

No secrets or external credentials were added or exposed.

## 13. Changes made and files changed

Packet 03 implementation/evidence files:

- `backend/app/models.py`
- `backend/app/main.py`
- `backend/app/modules/auth/schemas.py`, `backend/app/modules/auth/service.py`
- `backend/app/modules/crops/router.py`, new `backend/app/modules/crops/service.py`
- new `backend/app/modules/geography/__init__.py`, `backend/app/modules/geography/router.py`
- `backend/app/modules/markets/import_apmc.py`, new `backend/app/modules/markets/service.py`, `backend/app/modules/markets/router.py`
- `backend/app/modules/prices/import_mandi.py`, `backend/app/modules/prices/sync_service.py`
- `backend/app/modules/lots/router.py`, `backend/app/modules/fpo/service.py`
- `backend/alembic/versions/c4e83d2f1a60_geography_outlet_crop_registry.py`
- `backend/tests/test_packet03_geography_registry.py`
- `frontend/src/lib/produce.js`, `frontend/src/components/RateLookup.jsx`, new `frontend/src/components/RateLookup.test.jsx`, `frontend/src/pages/SellPage.jsx`, `frontend/src/pages/FPODashboard.jsx`, `frontend/src/utils/translations.js`
- `docs/DECISIONS.md`, `docs/work/03-plan.md`, `docs/work/03-result.md`, `PROGRESS_TRACKER.md`

This checkout also has prior-packet uncommitted changes. They were retained and not included as Packet 03 work. No commit or push was made.

## 14. Deferred decisions

- Which official LGD release/version and administrative naming policy to adopt.
- Which authoritative mandi/APMC/eNAM/outlet sources may legally be reused and by what retrieval method/cadence.
- Whether to add separate canonical buyer-market, collection-center, warehouse and logistics facility types or keep them in distinct domain tables.
- Whether localization should cover all crops/geography and how to handle transliteration collisions.
- Whether crop grade thresholds are sourced as official standards, buyer-specific contracts or both.
- Whether outlet confidence thresholds remain 0.85 after calibration against a representative, manually verified dataset.

## 15. Risks

- A migration may expose legacy null/constraint assumptions in the production database; test upgrade and downgrade against a sanitized production-like PostgreSQL/PostGIS snapshot first.
- Free-text historical state/district values cannot be backfilled safely without a sourced canonical map; they intentionally remain unmatched.
- Deterministic keys prevent repeated source rows from creating fresh candidates, but semantically duplicated records across different sources still require human adjudication.
- Public outlet coverage may be low until licensing and source onboarding are resolved. This is a truthful coverage state, not an implementation failure.
- PostGIS geography casts, extension/index compatibility and planner behavior remain version-dependent until live validation.

## 16. External dependencies

1. A lawful, authoritative, machine-readable Indian state/district/subdistrict dataset with LGD codes and version/provenance.
2. A license-cleared, maintained mandi/APMC/outlet dataset with stable IDs, region references and coordinate method/accuracy or enough provenance for manual verification.
3. PostgreSQL/PostGIS runtime matching production for migration, spatial integration and query-plan verification.
4. A source governance owner to approve/reject license evidence and periodically review outlet freshness and confidence.

No Packet 04 work was started. Stop condition satisfied.
