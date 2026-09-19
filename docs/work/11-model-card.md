# Packet 11 model card — no active forecast model

Status: **No active model; farmer-facing forecasts disabled.** Version: `forecast-policy-v1` (governance policy only, not a deployed predictor). Review date: 2026-09-18.

## Intended and non-intended use

No forecast output is currently generated. If a future eligible segment passes the deployment gate, the initial candidate will estimate a range for the future *reported modal wholesale price* for one canonical crop, official source market, compatible variety/grade, normalized unit, and a 7/14/30-day horizon. It will not estimate an individual farmer's achieved sale price, a buyer offer, national price, income, or guaranteed outcome. It will not autonomously list produce, accept an offer, reserve storage, or book logistics.

## Data and preprocessing contract

Only persisted observations from the active Packet 04 AGMARKNET daily reported-price source (`agmarknet-data-gov-v1`, registry `agmarknet-daily-reported-prices`) are eligible. Every observation must carry canonical crop/market, report date, compatible variety/grade/unit, non-LOW quality status, source record lineage, parser/normalization version, and retrieval timestamp. Demo adapter data, local JSON exports without row provenance, inferred arrivals, weather from generic web calls, and future platform activity are excluded. Unit/source/dimension changes split or invalidate a segment; malformed records may be excluded with a recorded reason, while genuine price shocks remain in evaluation.

## Segment eligibility

Proposed launch gate per segment: at least 365 distinct report dates spanning at least 18 months; latest observation at most 3 days old; no report-date gap greater than 14 days in the latest 90-day window; stable canonical crop, market, variety/grade dimension, price unit, source and normalization versions; at least 30 chronological rolling-origin outcomes. The time span allows season coverage, the observation count prevents sparse histories from qualifying, the recent-gap gate catches source outages, and rolling origins measure more than one lucky holdout. A segment failing any gate abstains. These are predeclared conservative gates, not empirical proof of adequacy and not a promise of forecast availability.

## Candidate method and evaluation

No candidate has been trained or evaluated because this checkout contains zero eligible official history. When evidence exists, start with deterministic last-observation and rolling-median baselines; test seasonal naive only after at least two complete seasonal cycles. Use chronological holdout followed by rolling-origin evaluation; never randomly shuffle time. Features must be timestamped and known at prediction time. Tests must assert future observations and future-derived features cannot enter a fold. Record MAE and median absolute error in INR/unit, relative error only where denominator is valid, directional accuracy, interval empirical coverage and interval width, by crop/market/horizon.

## Promotion gate

Candidate → shadow requires a reproducible run, source snapshot references, code/config version, and no leakage. Shadow → active requires ≥30 rolling-origin predictions; at least 10% lower MAE than the better simple baseline on ≥70% of eligible segments; nominal-80% interval coverage between 75% and 85% across at least 50 valid outcomes per segment; no stale, OOD, source-break or unit-inconsistent segment; and reviewed per-segment error. Because the coverage gate requires 50 outcomes, promotion cannot occur with only 30. If a gate fails, preserve the previous active model (if any) and abstain. This repository currently has no model registry rows, candidate artifacts, evaluation records, or active version.

## Prediction ranges and wording

Only calibrated prediction intervals may be shown. Public wording must say the horizon, generation time, last source date, market/crop, and empirical holdout coverage method. Do not call a nominal interval a probability/confidence percentage until calibration is demonstrated. Exact farmer prices and causal income uplift are outside the target.

## OOD, staleness, and abstention

Abstain for unknown market/crop/variety, unit/source/normalization changes, fewer than the segment thresholds, latest report older than 3 days, a >14-day recent gap, extreme inputs outside validation support, or unacceptable per-segment metrics. Descriptive reported history remains available independently. No forecast API fallback may substitute a moving average or fabricated growth rate.

## Monitoring, rollback, reproducibility

There is no active model to monitor. Future activation must persist model/version, training window, observation ID range, feature schema, code reference, deterministic seed, algorithm/config, evaluation report and status; log each prediction immutably with model, horizon, snapshot, interval and source date; match outcomes using a fixed future-observation rule; and monitor data freshness, input/prediction drift, error, coverage and abstention by segment. Promotion is atomic and prior active versions are retained for rollback. Operator environment switches currently disable forecasts, price alerts, and Trust summaries independently; future promotion requires an audited operator path before it is exposed.

## Limitations

The thresholds and baseline policy are governance gates, not calibrated claims about Indian agricultural price dynamics. Market holidays, revisions, reporting delays, variety and grade coding, and source coverage may cause abstention. Production official-source credentials and a live PostgreSQL/PostGIS rehearsal are unavailable in this workspace.
