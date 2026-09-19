# Packet 11 plan — Intelligence and differentiation

## Objective

Implement an evidence-governed intelligence foundation on top of Packets 03–10. Treat abstention as the correct user-visible answer until adequate evidence exists. No forecast or recommendation is enabled from demo/unprovenanced data.

## Verified constraints

- Packet 04 has a provenance-filtered reported-price path but no local real official series (see `docs/work/11-data-audit.md`).
- Existing `/prices/trends/{crop_name}` was willing to produce a trend from only two observations and included the latest row in its comparison mean; it omitted unit/freshness/observation-count context.
- `/accuracy` currently truthfully reports that verified model-accuracy evidence is unavailable; preserve that claim.
- Buyer requirement locations are free text, so district-level demand/supply ratios are not comparable.
- Payment references/reports are not provider settlement evidence; no payment-timing reliability can be derived.
- Notification + outbox infrastructure exists and is the only permissible alert delivery path.

## Implementation scope

1. Add an auditable historical-data inventory and explicit forecast methodology/model card; no training, model artifact, prediction logging, or promotion until genuine evidence qualifies.
2. Make descriptive trend output require a comparable same-market/crop/variety/grade/unit series with a clear sample, dates, source, freshness and method; otherwise abstain.
3. Add owner-scoped deterministic reported-price alert rules with canonical crop/market, explicit INR/quintal threshold, observation-level deduplication, in-app Notification and transactional Outbox only. Alerts are observation-triggered, not predictions.
4. Add evidence-only Trust Ledger facts without composite scores/stars/rates. Exclude self-trades; use canonical completed trade + immutable term snapshot. Never derive payment timing from participant reports or status strings. Restrict private payloads.
5. Add only side-by-side real channel facts where terms/units compare; unknown costs remain null and disable net ranking. If current contracts cannot support a safe comparison, return unavailable rather than approximate.
6. Record demand, realization benchmark, forecast activation, and public accuracy as abstaining/unavailable when common evidence/geography/payment/outcome criteria fail. Keep `/accuracy` truthful.
7. Add focused tests for eligibility, stale/sparse abstention, alert ownership/deduplication/outbox, trust denominator/privacy, and unknown-cost non-ranking.
8. Add an ADR for minimum-data thresholds, model deployment gates, Trust Ledger denominator/evidence, and channel cost semantics.

## Verification

Run full backend suite, targeted intelligence tests, Ruff, mypy, compileall, frontend lint/unit/build/E2E, bundle/security checks, secret scan and `git diff --check`. Record infrastructure skips honestly. Do not commit, push, or begin Packet 12.

## Stop condition

Packet 11 ends with operational intelligence primitives and truthful abstention. It does not end with a farmer-facing production forecast unless genuine validated series and all deployment gates are met.
