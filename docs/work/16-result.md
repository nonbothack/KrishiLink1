# Work Packet 16 — Pilot evidence and iteration

## Overall status: BLOCKED

**BLOCKED — pilot participants not yet available.** Repository inspection found no real participant matrix, consent records or anonymized session exports. Packet 16 therefore does not claim usability, comprehension, adoption, time-to-value, buyer fill, FPO throughput, support, disputes, realization or satisfaction results. The research kit and no-fabrication analysis path are complete; the product itself was not changed.

## 1. Executive summary

Packet 16 established a pre-registered research protocol, role-specific moderated scripts, privacy-safe observation format, machine-readable session schema, deterministic analysis script and evidence-linked iteration backlog. The required paid farmer/buyer/FPO panel has not been recruited or run, so the acceptance evidence is blocked.

## 2. Repository state

Branch is `abdulrehman`. The working tree already contained prior packet changes; Packet 16 added only research documentation, a standard-library analysis tool and focused tests. No commit, push or tag was made. Packet 17 was not started.

## 3. Engineering RC status

**READY (inherited from Packet 15B).** Packet15B recorded the engineering RC as ready with external VAPT, legal/privacy, manual accessibility/native-language review, provider contracts/infrastructure evidence and stakeholder UAT pending. Packet 16 did not alter application behavior.

## 4. Pilot usability evidence status

**BLOCKED / INSUFFICIENT.** There are zero real sessions (`n = 0`), so no threshold can be evaluated and no segment can be represented.

## 5. Production launch status

**NOT APPROVED / EXTERNAL SIGNOFF PENDING.** A research kit cannot substitute for participant evidence or the release sign-offs recorded by Packet 15B.

## 6. Research objectives

The plan measures farmer comprehension/time-to-value/listing, buyer fill and privacy comprehension, FPO traceability/throughput, support reasons, disputes and realization methodology without inventing claims.

## 7. Pre-registered hypotheses and thresholds

H1–H7 and their denominators are in `docs/pilot/16-research-plan.md`. They require minimum sample sizes and separate prompted/coached outcomes from unassisted success.

## 8. Recruitment and participant panel

Target panel: 6–10 farmers, 3–5 buyers and 2–4 FPO operators, varied across English/Hindi/Marathi, device, network and context. **Recorded: none.** Recruitment, compensation and named research ownership remain external dependencies.

## 9. Consent and ethics

Consent language, withdrawal, retention, compensation and stop rules are specified. No consent was obtained in this run; no recordings or raw personal data were added to the repository.

## 10. Safe pilot environment

Scripts require isolated staging accounts and synthetic transactions. No real payment, offer acceptance or private account data may be used. A safe participant-ready environment has not been demonstrated in Packet 16.

## 11. Farmer script coverage

The farmer script covers five-second first impression, reported price/source/date, location, lot review/publish, duplicate retry, offers, Trade Room, notifications/support, intermittent network, shared-device isolation and optional simple/voice paths.

## 12. Buyer script coverage

The buyer script covers verification semantics, requirements, FPO discovery, farmer-data minimization, offer/quantity handling, canonical Trade Room, notifications and support.

## 13. FPO script coverage

The FPO script covers member versus platform user, intake/correction, multi-member pools, conservation, publish, offer/trade and exact trade-to-member trace, including cross-FPO denial.

## 14. Device and network coverage

The plan requests 360×640, 390×844, 768×1024 and 1440×900 plus intermittent-network observations. No participant segment was available, so coverage is unverified.

## 15. Language coverage

English, Hindi and Marathi are required in the matrix and scripts. No native speaker session or manual language review was conducted.

## 16. Accessibility coverage

The scripts include keyboard/screen-reader, touch target, focus, text scaling and status comprehension checks where applicable. No manual participant accessibility session was conducted.

## 17. Observation provenance

Each observation requires session, participant code, build, role, task, outcome, elapsed time, assistance, severity and an external evidence reference. No observations exist yet.

## 18. Session schema

`docs/pilot/data/session-schema.json` constrains anonymized `S16-*` sessions, `P16-*` participants, roles, task outcomes, timing and assistance. It excludes direct identity fields.

## 19. Analysis implementation

`scripts/analyze_pilot_sessions.py` validates records, reports explicit `n`, task outcomes, timing medians, assistance, comprehension and issue counts, and returns `NO PILOT DATA` for absent/empty exports. It has no random or demo fallback.

## 20. Analysis result

No real export was supplied. The only valid evidence state is `NO PILOT DATA`; no aggregate metrics are reported.

## 21. Five-second comprehension

Not measured. No claim can be made about what a farmer notices without scrolling.

## 22. Price/source/date comprehension

Not measured. The acceptance rubric requires amount, unit, market, report date, source and reported-price meaning.

## 23. Time to first useful insight

Not measured. The registered definition starts at the first authenticated usable dashboard state and requires a correct crop/price/unit/source-date statement.

## 24. Listing success and effort

Not measured. The analysis distinguishes persisted canonical listing success from an offline draft and does not claim a three-tap result.

## 25. Buyer fill

Not measured. No persisted pilot requirement/offer records were supplied for a compatible-unit fill calculation.

## 26. FPO throughput

Not measured. No participant trace sessions were supplied.

## 27. Support and error reasons

Not measured. The observation template provides stable issue codes and severity for future sessions.

## 28. Disputes and realization methodology

Not measured. No pilot trade observations were used to infer dispute or realization outcomes.

## 29. Privacy/security observations

Not measured with participants. The scripts explicitly test cross-account isolation and unnecessary farmer/member data exposure; any observed failure is a release blocker.

## 30. Research instrumentation

No third-party analytics SDK or new persistent event stream was added. Existing operational logs/outbox events are not participant evidence. The schema and manual observation boundary avoid collecting PII until a reviewed research datastore exists.

## 31. Privacy and data minimization

Participant codes are required; names, contacts, precise GPS, credentials, bank data and raw recordings are prohibited from committed artifacts. Retention and deletion remain to be approved by the research/privacy owner.

## 32. Findings

`docs/pilot/16-findings.md` states `NO PILOT DATA`. There are no evidence-linked findings, testimonials or public claims.

## 33. Iteration backlog

`docs/pilot/iteration-backlog.md` is intentionally empty until a real finding is linked to a session/task/build. No speculative UI or domain change was made from an anecdote.

## 34. Product changes

None. This packet added research artifacts and tests only.

## 35. Focused tests added

Three backend tests cover explicit no-data status, malformed-record rejection and denominator-preserving analysis with unassisted success semantics. Fixtures are isolated test data, not pilot evidence.

## 36. Full backend verification

`python -m pytest -q` — **225 passed, 0 failed, 0 skipped**. Collection confirmed 225 tests. A pytest-asyncio deprecation warning was reported; it did not affect the result.

## 37. Static verification

`python -m ruff check app` passed; `python -m mypy app` passed with no issues in 91 source files; `python -m compileall -q app alembic/versions ../scripts` passed; and `git diff --check` passed (Git emitted only existing LF/CRLF normalization warnings).

## 38. Frontend verification

No frontend files changed. Fresh checks passed: `npm run lint`; `npm run test -- --run` (40 tests); `npm run build` (Vite build, prerender/SEO, provider-secret, offline and bundle checks); and `npm run test:e2e` (30 passed in 4.3 minutes). The build correctly omitted dynamic public pages when the API was unavailable rather than substituting sample data.

## 39. Browser evidence

No participant browser sessions were run. Existing automated browser coverage is engineering regression evidence, not human pilot evidence.

## 40. Regression protection

The analysis tests reject malformed/no-data input and preserve explicit denominators. Existing Packet15B application race/soak/rollback evidence was not modified.

## 41. Security impact

No production authorization or data path changed. The research protocol adds explicit prohibitions against real credentials, payments, cross-account inspection and raw PII in committed exports.

## 42. Accessibility impact

No product UI changed. Accessibility observations are scripted for future sessions; manual assistive-technology evidence remains absent.

## 43. Performance impact

No runtime bundle, endpoint or database impact. The analysis tool uses only the Python standard library and bounded input records.

## 44. Migrations/endpoints

No database migration and no application endpoint were added. This avoids creating an ungoverned research data store.

## 45. Rollback instructions

Packet16 changes are additive. To roll back the research kit, remove the Packet16 files listed below and revert the tracker entry; no database rollback is required. Do not delete any future approved raw research data outside the repository as part of a code rollback.

## 46. Files changed

- `docs/pilot/README.md`
- `docs/pilot/16-research-plan.md`
- `docs/pilot/participant-matrix.md`
- `docs/pilot/session-script-farmer.md`
- `docs/pilot/session-script-buyer.md`
- `docs/pilot/session-script-fpo.md`
- `docs/pilot/observation-template.md`
- `docs/pilot/metric-definitions.md`
- `docs/pilot/16-findings.md`
- `docs/pilot/16-analysis.md`
- `docs/pilot/iteration-backlog.md`
- `docs/pilot/data/session-schema.json`
- `docs/work/16-plan.md`
- `docs/work/16-result.md`
- `scripts/analyze_pilot_sessions.py`
- `backend/tests/test_packet16_research.py`
- `PROGRESS_TRACKER.md`

## 47. External dependencies

Real paid participant recruitment and compensation; consent/ethics approval; named moderator/research owner; staging accounts; native-language and accessibility review; approved research storage/retention; stakeholder UAT; VAPT/legal/privacy/provider sign-offs inherited from Packet15B.

## 48. Risks

The main risk is treating engineering tests or synthetic fixtures as human evidence. Other risks are convenience-panel bias, moderator assistance contaminating success, unreviewed language translation, privacy leakage in notes and unmeasured low-connectivity behavior.

## 49. Deferred decisions

Choose a reviewed research datastore, participant compensation policy, recording retention period, native-language moderator process, event instrumentation boundary and release thresholds for each segment before sessions begin.

## 50. Acceptance gaps

No participant evidence, no consented panel, no session metrics, no findings, no iteration validation and no human accessibility/native-language review were available. These are blocking gaps under Packet16 semantics.

## 51. Recommended pilot decision

**CONTINUE_PILOT.** The kit is ready for a real, paid and consented panel; do not promote the product or publish pilot claims until the sessions and analysis are complete.

## 52. Recommended next packet

No later packet is started. After real evidence is collected and this result is updated, the owner should decide whether to continue with fixes or pause for P1 remediation. Packet 17 is not initiated by this run.

## 53. Git status

Working tree contains the prior packet changes plus the Packet16 research kit. No commit, push or tag was made.

## 54. Evidence classification

**Verified locally:** research artifacts exist; deterministic analysis behavior is testable; no-data path is explicit. **Verified through deterministic tests:** malformed records are rejected and denominators are preserved. **Externally unverified:** every real participant, consent, human comprehension, language, accessibility, network and product-iteration claim.

## 55. Pilot recommendation wording

The only truthful participant statement today is: `No pilot sessions available; usability evidence is blocked.` Do not replace it with “early users love,” “farmers saved,” “buyers filled,” or similar language.

## 56. Release decision separation

Engineering RC: **READY** (Packet15B evidence). Pilot usability evidence: **BLOCKED / INSUFFICIENT**. Production launch: **NOT APPROVED / EXTERNAL SIGNOFF PENDING**.

## 57. Packet boundary

Packet 16 only was executed. No forecast, marketplace, offline, admin, government or production feature work was started.

## 58. Final stop condition

This packet stops here until real participants or approved anonymized session data are available. The status remains **BLOCKED** rather than manufacturing completion.
