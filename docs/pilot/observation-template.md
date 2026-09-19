# Session observation template

Create one record per task observation. Use participant codes only.

| field | required meaning |
|---|---|
| session_id | Anonymous session identifier |
| participant_code | Matrix code, never a name/contact |
| build | Release/build identifier |
| role | farmer, buyer or fpo |
| task_id | Script task identifier |
| outcome | SUCCESS, PARTIAL, FAIL or NOT_ATTEMPTED |
| elapsed_ms | From task start to completed/abandoned outcome |
| assistance | NONE, PROMPT, COACHED or ABORTED |
| comprehension | PASS, PARTIAL, FAIL or NOT_TESTED, with the answer rubric |
| issue_code | Stable issue code or `NONE` |
| severity | P0, P1, P2, P3 or INFO |
| evidence_ref | Note/screenshot/recording reference kept outside git |
| notes | Minimal observation, no raw PII or sensitive credentials |

Record the participant’s words faithfully where needed, but redact identifiers. Distinguish observed behavior from moderator interpretation.

