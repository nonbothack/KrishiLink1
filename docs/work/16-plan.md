# Work Packet 16 plan — pilot evidence and iteration

## Current state

Packet 15B left the engineering release candidate ready with external operational sign-offs pending. Repository inspection found no `docs/pilot` evidence set, participant matrix, anonymized session export or first-party pilot event ledger. Existing telemetry is operational request/outbox logging; no participant research evidence can be inferred from it.

## Scope

Create a pre-registered, privacy-safe pilot protocol, role scripts, participant/observation templates, a machine-readable anonymized session schema and a deterministic analysis tool with no-data abstention. Do not change product behavior or claim pilot results without real participants.

## Files and interfaces

New files are under `docs/pilot/`, `scripts/analyze_pilot_sessions.py` and `backend/tests/test_packet16_research.py`. No application endpoint or database table is added because an unapproved research datastore would increase privacy scope and there is no real session source to integrate.

## Risks and dependencies

The packet cannot reach PASS without a paid, consented farmer/buyer/FPO panel, a named moderator, safe staging accounts, language/accessibility review and anonymized session exports. Raw recordings stay outside git. No migration is required.

## Verification plan

Run the new deterministic tests, full backend pytest, Ruff/mypy/compile checks, schema/script checks and `git diff --check`. Retain the already verified Packet15B frontend baseline because no frontend code changes are made.

