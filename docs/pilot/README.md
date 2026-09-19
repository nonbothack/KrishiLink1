# KrishiLink Packet 16 pilot evidence kit

This directory contains the pre-registered research protocol, anonymized session schema, observation templates and deterministic analysis for Work Packet 16. It is a research instrument, not evidence that a pilot has happened.

## Current evidence state

At Packet 16 execution time there are **no real participant records, consent records or session exports in this repository**. The participant matrix is intentionally empty. No usability, comprehension, adoption, price-realisation or satisfaction claim may be made from this checkout.

The correct packet status is therefore **BLOCKED — pilot participants not yet available**. A paid panel of real farmers, buyers and FPO operators, informed consent, a safe staging environment and a named moderator are required before sessions can be run.

## How to use the kit

1. Pre-register the hypotheses and thresholds in `16-research-plan.md`.
2. Recruit and compensate participants using the matrix in `participant-matrix.md`; use participant codes only.
3. Obtain consent before recording notes, screen captures or task outcomes. Do not commit raw recordings, phone numbers, names, precise addresses or financial identifiers.
4. Run the role-specific scripts on a labelled staging/demo build. Never ask a participant to make a real payment, accept a real offer or expose another account.
5. Record one structured session per participant using `data/session-schema.json` and `observation-template.md`.
6. Run `python scripts/analyze_pilot_sessions.py --input <anonymized-export.json> --out <analysis.json>`. The script rejects malformed records and prints `NO PILOT DATA` when no sessions are supplied; it never invents a denominator or fallback result.
7. Copy only anonymized, traceable aggregate findings into `16-findings.md`, link each finding to session/task evidence, and create a versioned item in `iteration-backlog.md`.

Synthetic fixtures are allowed inside automated tests only. They are not pilot evidence and must never be copied into production or public marketing.

