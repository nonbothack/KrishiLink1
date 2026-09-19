# Packet 16S plan

## Purpose

Find obvious navigation, comprehension, truthfulness, authorization, accessibility, and failure-state problems before real pilot sessions. This is a pre-pilot rehearsal, not validation.

## Baseline rule

The first OpenUser run was executed before any KrishiLink product fix. No product fix was made during this packet. A second run used a correctly proxied Vite test server to separate the first run's frontend configuration failure from the app's truthful empty-data behavior.

## Target versus executed matrix

The requested target was approximately 30 synthetic personas: 15 farmers, 7 buyers, 5 FPO operators, and 3 operations/support personas. The executed matrix was intentionally smaller because each browser run is an exploratory smoke test and the external MiroFish simulation was used for cross-stakeholder semantic rehearsal. Actual counts are recorded in `personas.md` and `16s-result.md`; no target count is presented as completed.

## Finding rules

Findings use `S16-###` identifiers. Each record carries source, role, scenario, build/environment, evidence, frequency, severity, type, recommendation, decision, and whether real-user validation is required. A single truth, privacy, authorization, or data-loss observation is actionable even without repetition. Repeated behavior is stronger only when it occurs in independent runs.

## Status rules

`PASS` requires no unresolved synthetic P0/P1. `PASS_WITH_FINDINGS` allows only P2/P3 and real-user validation questions. `FAIL` is used for a credible unresolved P0/P1 or an essential journey that the rehearsal cannot complete. `BLOCKED` is reserved for testing infrastructure that cannot execute.
