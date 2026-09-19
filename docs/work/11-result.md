# Packet 11 — Intelligence and Differentiation: completion evidence

Date: 2026-09-18  
Branch: `abdulrehman`  
Status: **PASS_WITH_EXTERNAL_DEPENDENCY**

## 1. Executive summary

Packet 11 establishes evidence-gated descriptive intelligence, owner-scoped reported-price alerts, factual Trust Ledger projections, and truthful abstention contracts. The audit found no locally eligible official historical series, so no forecast was trained, no model was promoted, and no sale-window recommendation or public accuracy statistic was fabricated. Missing geography/cost/payment evidence similarly disables demand ratios, channel winners, and payment-timing claims.

The completed implementation provides APIs and farmer UI for deterministic reported-price alerts; tightens the existing price-trend endpoint to descriptive-only comparable observations; adds private, sample-aware factual buyer history; and permits owner-only side-by-side comparison of genuine current offers and qualifying reported prices while leaving unknown costs unknown. PostgreSQL/PostGIS migration/locking rehearsal and production AGMARKNET data/provider access were unavailable; these are external verification dependencies.

## 2. Historical-data audit

The evidence inventory is in [`11-data-audit.md`](11-data-audit.md). The only eligible official path is Packet 04's persisted observation pipeline: active `agmarknet-data-gov-v1` parser/source and registry, canonical active/tradable crop and market, normalized unit, quality, report/fetch timestamps, and retained row provenance.

The local `backend/krishilink.db` has 960 legacy `DemoPriceAdapter` observations across 64 crop/market groups and 15 consecutive dates. That legacy schema lacks Packet 04's provenance/normalization contract and is synthetic. Six unreferenced `backend/mandi_*.json` exports contain 1,257 rows, 830 exact dimension/date keys and 427 duplicate excess rows across overlapping files, only two report dates, inconsistent/absent units, and no row-level source lineage. Neither source is eligible for training, benchmark, alert or public-statistic evidence. The audit therefore found zero eligible local forecast segments; it does not assert that production has zero data.

## 3. Intelligence eligibility rules

The policy and proposed gates are versioned in [ADR-009](../DECISIONS.md) and [`11-model-card.md`](11-model-card.md). Descriptive movement requires at least seven distinct report dates, one crop/market/variety/grade/unit/source dimension, HIGH or MEDIUM quality, and a latest report no older than seven days. Trend direction uses a configurable 1.5% endpoint movement threshold; the endpoint reports the sample, dates, unit, source, and explicitly labels the result descriptive-only.

Forecast segment proposal: at least 365 distinct report dates spanning 18 months; latest observation ≤3 days old; no gap >14 days in the latest 90 days; stable dimensions and source/normalization versions; and ≥30 chronological rolling-origin outcomes. These gates are conservative deployment policy, not empirically validated claims. Current active model is `null` in [`11-model-registry.yml`](11-model-registry.yml); forecast requests return structured abstention.

## 4. Forecast architecture

No predictor, training endpoint, model artifact, candidate promotion, or client-side model was added. `/api/v1/intelligence/forecasts/{crop_id}` returns `FORECAST_UNAVAILABLE`, a reason (`FORECASTS_DISABLED` or `NO_ACTIVE_VALIDATED_MODEL`), null forecast/model/date fields, and a methodology version. Inference remains server-side by contract; segment eligibility and prediction logging cannot be claimed as active until real data and a validated model lifecycle exist.

## 5. Training/evaluation method

No training was run because there is no genuine eligible local dataset. The model card predeclares chronological holdout and rolling-origin evaluation; features must be known at prediction time. Random time-series shuffling is prohibited. Baselines are last observation and rolling median; seasonal naive is considered only after two complete cycles. Leakage tests require future observations/future-derived features to remain outside each prediction fold. Model promotion is gated by predeclared baseline, sample and interval-coverage conditions.

## 6. Baselines

The future evaluation must compare candidate MAE against the stronger of last-observation and rolling-median baselines. Proposed promotion requires ≥10% lower MAE on ≥70% of eligible segments, at least 30 rolling-origin predictions, and at least 50 valid outcomes per segment for interval calibration. Failing any gate leaves the model unavailable/shadow. No baseline metric is claimed from demo data.

## 7. Leakage prevention

No untraceable CSV or future platform activity entered a training set. The accepted data contract uses Packet 04 source observation IDs/version lineage and report/retrieval timestamps. Requirements, trades, quality outcomes, arrivals and other later evidence are excluded from price-only training unless a future version proves that each feature existed at prediction time. Deterministic synthetic series are used only in isolated tests of mechanics, not in performance claims.

## 8. Forecast metrics

No model metrics are published because no eligible model/evaluation exists. The model card requires MAE and median absolute error in INR/unit, valid relative error, directional accuracy, interval coverage and interval width by crop/market/horizon. Aggregate success cannot override a failing segment.

## 9. Prediction intervals/calibration

There is no active interval or confidence claim. A future nominal 80% range must demonstrate 75–85% empirical coverage over at least 50 valid chronological outcomes per segment, with interval width reported. No library-generated nominal label is treated as calibration evidence.

## 10. OOD/abstention

Forecast and sale-window APIs abstain when no validated model and complete inputs exist. The documented gate rejects stale (>3-day) latest observations, recent gaps >14 days, unseen/inconsistent dimensions/source/unit, insufficient history, and inputs outside validation support. Descriptive price history remains independently available when its own seven-date and freshness gates pass.

## 11. Model registry/versioning

[`11-model-registry.yml`](11-model-registry.yml) contains no active or candidate predictor. [`11-model-card.md`](11-model-card.md) defines the metadata, reproducibility, evaluation, shadow/promotion, rollback and monitoring required before activation. No arbitrary model path or unsafe deserialization is introduced; ordinary users cannot start a training job.

## 12. Model card

The model card records intended/non-intended use, target, source population, preprocessing, segment thresholds, baselines, chronological evaluation, metrics, interval semantics, OOD/abstention, monitoring, rollback and limitations. Its version `forecast-policy-v1` is a governance policy, not a deployed model.

## 13. Shadow/promotion workflow

No candidate exists to shadow or promote. Promotion requirements are documented, including no leakage, ≥30 rolling-origin predictions, baseline improvement on ≥70% of eligible segments, and calibrated interval coverage from ≥50 outcomes per segment. These require an auditable operator workflow before any future activation; the current feature flag fails closed for forecasts.

## 14. Model monitoring/drift

No model is active, so no model error/drift metric is represented as measured. Required future metrics include source freshness, feature/prediction drift, outcome error, interval coverage and abstention rate by segment. Forecast, alert and Trust summaries have independent backend settings; forecasts default off. Model monitoring/atomic promotion remains deferred until a registered model exists.

## 15. Sale-window advisor

`/api/v1/intelligence/sale-window/{crop_id}` returns `NOT_ENOUGH_DATA`, null sell/wait values, and the reason that validated forecast and complete evidenced waiting costs are unavailable. It does not advise holding, invent a horizon, or perform an action.

## 16. Cost/assumption truth

The sale-window response explicitly marks that waiting costs are not included. Channel comparison returns actual evidence fields and gross values only. Freight, commission, storage and transport remain unknown/null; user assumptions are not silently stored as verified facts. No net proceeds or winner is calculated when any relevant costs are missing.

## 17. Channel comparison

`GET /api/v1/intelligence/lots/{lot_id}/channels` is owner-scoped (admin/operator exception) and only compares compatible INR/quintal lot evidence. It may show a genuine pending unexpired buyer offer and a fresh, exact crop/market/variety/grade official observation from the active source. Gross is Decimal-rendered; buyer private contact is not projected. MSP, eNAM, processor and storage-linked channels are explicitly unavailable. `net_ranking_enabled` is always false while unknown costs remain.

## 18. Trust Ledger methodology

`GET /api/v1/intelligence/trust/{buyer_id}` emits separate business-verification state and factual platform-history fields, not stars, a composite score or a rank. Eligible denominator is a canonical `COMPLETED` transaction with a matching immutable positive-quantity/price/gross term snapshot and distinct buyer/seller. Fewer than five eligible trades is `LIMITED_HISTORY`; zero is `NO_PLATFORM_HISTORY_YET`. The projection includes calculation time and sample period.

## 19. Trust small-sample handling

The endpoint reports counts and labels limited history; it does not compute a 1/1 reliability rate or rank a new buyer above an established buyer. Self-trades are excluded. This is deliberately more conservative than a Bayesian summary because the current packet has no defensible common behavioral outcome definition for a composite rate.

## 20. Payment/dispute evidence eligibility

Payment timing is always `UNAVAILABLE` until provider-verified settlement evidence with a defined timing contract exists; participant-entered UTR/payment reports do not qualify. Disputes are counted only when linked to an eligible completed trade; counts/statuses are descriptive, the denominator is eligible completed trades, and no fault or outcome is inferred. Private descriptions, evidence and counterparties are not returned.

## 21. Demand signals

`/api/v1/intelligence/demand/{crop_id}` (and requirement activity alias) abstains because buyer requirements hold free-text locations while supply geography is district/coordinate based. The API returns null quantities rather than mixing incomparable geographies or implying scarcity.

## 22. Price alerts

Farmer UI and APIs let a farmer create/list/disable up to 20 active alerts for a canonical crop, market, optional crop-owned variety, grade, threshold, direction and INR/quintal unit. The alert evaluator runs every 15 minutes through the existing Celery architecture; it consumes only fresh (≤7 days), HIGH/MEDIUM observations from the official Packet 04 source fetched after rule creation. Unique `(alert, observation)` evaluation receipts, row locking and transactional Notification + Outbox insertion prevent duplicate trigger delivery. A qualifying observation fires once; an observation on the opposite side re-arms the next crossing. Same-key retries return the existing alert. This is an observation alert, not a sale-price guarantee.

## 23. Realization-vs-benchmark

No realization-uplift metric is published. Agreed immutable trade terms are not themselves proof of realized payment; local official price evidence is absent. A valid future comparison must predefine exact crop/product, unit, market/geography, date window and observation selection method. No causal “income increased” wording is used.

## 24. `/accuracy` transparency

The Packet 09 public `/accuracy` state remains the truthful insufficient-production-evidence message. No evaluation number, public model coverage, prediction count or platform uplift was added. Build-time SEO fixture data is isolated in the existing test script and is not substituted into production rendering.

## 25. Farmer UX

The authenticated “More” surface links to a localized reported-price alert page. The form uses canonical crop and market APIs, clear threshold/direction/unit fields, loading/error/success states, retry-safe idempotency key reuse, and disable controls. Notification rendering uses persisted metadata for crop/market/price/report date/source. Copy for this feature is present in English, Hindi and Marathi. No forecasting chart or unsupported recommendation is shown.

## 26. Buyer/FPO UX

This packet does not add intelligence dashboards for buyers/FPOs or expose member/member-allocation evidence. Buyer Trust facts are an authenticated factual projection; owner-only lot channel comparison avoids disclosing unrelated lots or buyer PII. No demand badge or ranking is surfaced.

## 27. Security/privacy

Forecast/demand public contracts expose only canonical market-level status, not private lot features. Lot channel access is owner-scoped. Price alerts are farmer-only, owner-scoped, rate-limited, bounded to 20 active rules, validated against active canonical crop/market and crop-owned variety, and audited on create/disable. Trust access is limited to the buyer themself, farmer/FPO counterpart-facing roles and admin/operator; private dispute text and raw payment references are omitted. New notification metadata contains only report facts needed by the recipient.

## 28. Accessibility/i18n

Alert page and notification copy use the existing translation architecture for English/Hindi/Marathi. Browser tests run axe against the alert page and exercise keyboard-accessible page controls; the general frontend accessibility regression suite also passes. This does not replace manual screen-reader/native-speaker review.

## 29. Responsive review

Alert E2E visits 360×640, 390×844, 768×1024 and 1440×900, checks no horizontal overflow, creates/receives/disables the alert, and performs automated accessibility checks. The full browser suite is run separately; no claim is made about production device usability beyond deterministic browser coverage.

## 30. Performance/bundle impact

No ML/chart library or client model was added. The alert page is route-loaded. Final bundle check: initial JS 133.57 KiB gzip / 150 KiB budget; initial JS + CSS + static assets 141.94 KiB gzip / 400 KiB. Build generated route chunks and passed the repository budget.

## 31. Background jobs

The existing Celery app schedules `intelligence.evaluate_price_alerts` every 900 seconds. The task honors the alert feature switch, runs the evaluator through the existing DB session, and relies on Notification + Outbox. Redis/Celery production execution was not available for live verification.

## 32. Tests added

`backend/tests/test_packet11_intelligence.py` adds 10 focused tests covering forecast/sale-window abstention, demand geography abstention, Trust denominator/privacy/payment unavailability, unknown-cost channel handling and owner isolation, alert threshold/rearm/dedup/outbox, alert role/owner/unit/idempotency, stale-alert rejection, and descriptive-trend sample/dimension/quality requirements. `frontend/e2e/critical-journeys.spec.js` adds an accessible farmer create/receive/disable alert journey at all four target viewports.

## 33. Full verification results

Final full-suite backend/frontend results and durations are recorded here after completion of the running full test commands. Checks executed for this packet:

| Command/check | Result |
|---|---|
| `python -m pytest -q -ra` (fresh isolated SQLite, `ENV=development`, `DEBUG=false`) | Passed: 201/201, 0 failed, 0 skipped; about 8 minutes observed wall time |
| `python -m pytest -q tests/test_packet11_intelligence.py` | 10 passed |
| `python -m ruff check app tests/test_packet11_intelligence.py` | Passed |
| `python -m mypy app` | Passed, 86 source files |
| `python -m compileall -q app alembic/versions` | Passed |
| `npm run lint` | Passed |
| `npm run test -- --run` | Passed, 22 tests across 6 files |
| `npm run build` | Passed; production build, public prerender/SEO and price-key secrecy checks passed |
| `npm run test:e2e` | Passed, 22 tests (desktop/mobile projects), 3.5 minutes |
| Alert E2E grep run | Passed, 2 tests (desktop/mobile projects) |
| `npm run check:bundle` | Passed: 133.57 KiB initial JS gzip; 141.94 KiB JS+CSS+static assets gzip |
| `npm run check:security` | Passed: six static headers and baseline CSP directives |
| `npm run test:seo-fixture` | Passed; fixture-backed public pages rendered; no production sample substitution |
| `npm run typecheck` | Not run successfully: local `tsc` executable not recognized |
| `npm run format:check` | Not run successfully: local `prettier` executable not recognized |
| Alembic head/history | Passed; one head `b611e2a7c930`, linear from Packet 10 revision |
| Packet 11 PostgreSQL SQL generation | Passed for revision range `d10a6f5b4c32:b611e2a7c930` |
| Full offline PostgreSQL SQL generation | Blocked by pre-existing data-dependent `c4e83d2f1a60` migration calling `bind.execute` offline |
| Live PostgreSQL/PostGIS migration/locking | Not run; service unavailable |
| `git diff --check` | Passed (line-ending warnings only) |

The corrected development-mode full run is the acceptance run. Pytest quiet mode printed its 100% completion but suppressed the final count/runtime summary; `--collect-only` independently confirmed 201 collected, and the zero-failure exit plus progress contained no skips. Observed wall time was about eight minutes. It emitted one `pytest-asyncio` deprecation warning for `asyncio.get_event_loop_policy`. The initial exploratory run with `ENV=test` failed three legacy development-only tests because that environment setting was incorrect; it is not the acceptance result.

## 34. Migrations

`b611e2a7c930_packet11_price_alerts.py` adds `notifications.metadata`, `price_alert_rules`, and unique rule/observation `price_alert_evaluations`, with threshold/direction/unit constraints and lookup indexes. Downgrade drops these additions. Alembic graph has one head and the Packet 10 → Packet 11 PostgreSQL SQL range generated successfully. No live PostgreSQL execution, rollback rehearsal or lock/concurrency claim is made. A full offline SQL render still encounters the pre-existing Packet 03 data-dependent migration limitation.

## 35. Files changed

Packet 11 source/test files: `backend/app/core/config.py`, `backend/app/main.py`, `backend/app/models.py`, `backend/app/modules/intelligence/__init__.py`, `backend/app/modules/intelligence/router.py`, `backend/app/modules/intelligence/service.py`, `backend/app/modules/notifications/router.py`, `backend/app/modules/notifications/service.py`, `backend/app/modules/prices/router.py`, `backend/app/workers/celery_app.py`, `backend/alembic/versions/b611e2a7c930_packet11_price_alerts.py`, `backend/tests/test_packet11_intelligence.py`, `frontend/src/App.jsx`, `frontend/src/lib/session.js`, `frontend/src/lib/session.test.js`, `frontend/src/pages/FarmerMorePage.jsx`, `frontend/src/pages/FarmerPriceAlertsPage.jsx`, `frontend/src/services/api.js`, `frontend/src/utils/copy.js`, `frontend/src/utils/translations.js`, and `frontend/e2e/critical-journeys.spec.js`.

Packet 11 documentation: `docs/work/11-data-audit.md`, `docs/work/11-plan.md`, `docs/work/11-model-card.md`, `docs/work/11-model-registry.yml`, `docs/work/11-result.md`, `docs/DECISIONS.md`, `PROGRESS_TRACKER.md`. The overall checkout already contained extensive uncommitted work from Packets 00–10 before Packet 11; this task did not commit or push it.

## 36. Regressions checked

The complete backend suite, frontend unit/lint/build/browser suites, existing bundle/security/SEO checks, and Packet 11 focused tests are the regression gates. Price provenance remains tied to Packet 04; no synthetic legacy price rows are surfaced. Packet 09 `/accuracy` remains evidence-limited. Trade, FPO conservation, payment-evidence and prior privacy contracts are included in the full regression suite; results are reported only after the full run completes.

## 37. Deferred work

Packet 12 offline/PWA, SMS/WhatsApp/IVR, weather/arrival integration, public or farmer-facing forecasts, recommendation activation, model training/registry persistence, shadow prediction/outcome logging, demand geography normalization, Trust Ledger rates/ranking, verified-cost channel net comparisons, payment timing, realization uplift, alert external delivery, admin model control/monitoring UI and production analytics are not implemented. No Packet 12 work was started.

## 38. Risks

- Forecast launch thresholds are predeclared conservative gates; they still require validation against real observations before claiming utility.
- Official source freshness, market holidays/revisions, grade/unit normalization and upstream coverage can cause abstention.
- Alert runtime depends on the existing Celery/Redis/Outbox production configuration and PostgreSQL locking semantics.
- Trust history counts depend on canonical `COMPLETED` state and immutable terms; no provider-backed payment or dispute-fault signal exists.
- Channel comparison exposes only comparable gross facts, so it cannot choose the best net outcome.
- Full migration SQL remains sensitive to an older offline-incompatible data migration.

## 39. External dependencies

Production AGMARKNET/data.gov.in credentials and genuine persisted observations; PostgreSQL/PostGIS migration and row-lock rehearsal; Redis/Celery worker runtime; real provider settlement evidence; stable requirement geography; approved production notification delivery and support operations. Native-speaker and manual assistive-technology review are also follow-ups, not blockers to automated catalogue/test coverage.

## 40. Git status

Working branch is `abdulrehman`. No commit or push was made. The working tree contains the Packet 11 changes plus pre-existing uncommitted Packet 00–10 work; detailed status is in the local `git status --short --branch` output. Packet 12 was not started.
