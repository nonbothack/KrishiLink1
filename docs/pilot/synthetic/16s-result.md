# Packet 16S — Synthetic User Simulation & UX Stress Test

**Status: FAIL (historical acceptance remains open)**

This status applies only to the synthetic rehearsal. Real Packet 16 remains **BLOCKED / INSUFFICIENT** because no paid, consented participants have completed sessions.

## 1. Executive summary

The continuation repaired the local browser path without changing security controls: Vite 5174 proxies to an isolated backend 8002 whose local origin allow-list includes only the explicit test origins. The repaired empty-price smoke passed through login to `/sell`, and a separate local-only positive fixture passed source/date/unit inspection and login. Two P2 UX inconsistencies remain under investigation. The original 5173/5174 P1 environment failures are preserved below as historical evidence. The full approximately-30 browser matrix has not yet been executed, so this packet remains open and is not presented as a completed PASS.

## 2. Tool versions

- OpenUser CLI: 0.1.1
- OpenUser daemon: local `127.0.0.1:8737`
- Chromium: Playwright-managed Chrome for Testing 153.0.8010.12
- MiroFish: `uv` 0.12.17, isolated Python 3.12.14
- Codex CLI: 0.155.0-alpha.9.2
- Node: v24.13.0; npm: 11.6.2
- Python available in KrishiLink shell: 3.14.3; MiroFish used isolated 3.12.14
- Docker CLI was unavailable in the current shell; no Docker claim is made here.

## 3. Exact repository URLs

- KrishiLink: `C:\abdul`
- Frontend tested: `http://localhost:5173` static preview and `http://localhost:5174` Vite dev server
- Backend tested: `http://localhost:8001`
- Frontend health: `http://localhost:5173/health` returned 200
- Backend API health: `http://localhost:8001/api/v1/health` returned 200 in demo mode

## 4. Tool commit SHAs

- MiroFish: `d8dc889433b116247475db9830788dea224400e1`
- OpenUser was run from npm package 0.1.1; no repository SHA was available from the package invocation.

## 5. Installation method

OpenUser was installed with `npx --yes openuser-cli` using a clean local npm cache, then Chromium was installed with `npx playwright install chromium`. MiroFish was cloned to `C:\krishilink-sim-tools\mirofish`, synchronized with an isolated `uv` Python 3.12 environment, and kept outside KrishiLink. A rapidfuzz lock refresh was required for Windows compatibility in the external checkout only.

## 6. Security review

OpenUser ran against localhost and the daemon was bound to `127.0.0.1`. Synthetic credentials were used only in a local test database and are omitted from committed evidence. The MiroFish source pack was redacted and contained no secrets or private records. No origin guard, CSP, authentication, or production provider control was weakened. Full artifacts remain outside the repository.

## 7. KrishiLink build tested

The existing working tree build was tested; no Packet 16S product changes were made. The static 5173 preview and a temporary 5174 Vite server were both examined because their API behavior differed.

## 8. Environment

The backend and frontend health endpoints were reachable. The official price endpoint returned an empty observation list, so a no-price state was the expected truthful result. The 5173 static preview had no `/api` proxy and returned the SPA shell for same-origin API paths. For continuation, a Vite server on 5174 proxied to an isolated backend on 8002 using the mapped Postgres/Redis services; the local backend explicitly allowed 5174 and rejected no arbitrary origins.

## 9. OpenUser configuration

One local project was registered, first at 5173 and then patched to 5174 through the local OpenUser API. Tester runs used the OpenUser tester MCP role and local browser artifacts. Generated OpenUser config/skill files were setup artifacts and are removed before completion.

## 10. OpenUser smoke

Five farmer runs are now recorded. The repaired empty-price smoke (`run_PThKmMh9IUjq`) passed price-state inspection, login, and `/sell`. The positive fixture run (`run_buhIFmwBFPJJ`) passed source/date/unit inspection, login, and `/sell`, and recorded two P2 UX findings. The original failed runs remain unchanged in the evidence log.

## 11. Farmer persona matrix

Target 15; executed three synthetic farmer personas: novice 360x640, novice 360x640, and novice 390x844. Coverage was English price-empty state, Sell entry, and login boundary. No result is real farmer evidence.

## 12. Buyer persona matrix

Target seven; no browser buyer personas executed. Buyer concerns were represented only as a role in the MiroFish source pack and simulation. Browser buyer validation remains open.

## 13. FPO persona matrix

Target five; no browser FPO personas executed. Traceability and offline-state concerns were represented only in MiroFish. Browser FPO validation remains open.

## 14. Operations personas

Target three; no browser operations personas executed. The platform/operations perspective appeared in the MiroFish simulation only.

## 15. OpenUser run count

Five farmer OpenUser runs are recorded after including the continuation. One initial attempt before Chromium installation failed as setup/tooling; two historical post-setup runs exposed environment blockers; two repaired runs passed. This is still a smoke subset, not the requested approximately 30-persona matrix.

## 16. OpenUser goal-achieved/partial/blocked counts

Among the five recorded runs: three reached `goal_achieved` or passed, one was blocked by origin configuration, and one was a setup/configuration failure. The two repaired runs both passed their scoped farmer goals. Buyer, FPO, and operations counts remain zero.

## 17. OpenUser P0

No P0 finding was established. No cross-account, privacy, data-loss, or authorization exposure was observed.

## 18. OpenUser P1

The two historical P1 environment blockers are repaired for the isolated continuation path: API proxying works and login succeeds through the explicit local origin allow-list. No unresolved synthetic P1 product finding remains in the repaired farmer smoke. The full matrix still needs execution before acceptance can be closed.

## 19. OpenUser P2/P3

The correctly proxied run produced a P2-style expected-unavailable observation: the empty official dataset is communicated clearly, but there is no price comparison until a genuine observation exists. This needs real-user comprehension validation and a seeded staging fixture for positive paths.

## 20. MiroFish configuration

MiroFish ran externally with an explicit UTF-8 environment because the first Windows Codex subprocess emitted invalid UTF-8 and timed out. The successful run used three rounds and a redacted KrishiLink source pack.

## 21. MiroFish source pack

The pack contained product context, farmer/buyer/FPO flows, truth and trust rules, and pilot questions under `C:\krishilink-sim-tools\mirofish-input\krishilink`. It contained no real participants, secrets, market records, or production exports.

## 22. MiroFish farmer simulation

Synthetic farmer agents repeatedly asked whether reported prices were official, current, local, comparable, and the amount they would receive. This is a simulated question pattern only.

## 23. MiroFish buyer simulation

Synthetic buyer agents questioned whether a displayed value was an official reference or a confirmed offer and whether Sell created a binding commitment. No buyer behavior claim is made.

## 24. MiroFish FPO simulation

Synthetic FPO agents focused on separating local member records from published lots and on synchronization/audit state. No FPO throughput or traceability claim is made.

## 25. Cross-stakeholder simulation

The platform agent attempted to clarify price metadata, staged Sell, offline status, and payment evidence. The report itself warns that compressed wording can create new ambiguity.

## 26. Cross-tool convergence

Only weak thematic convergence exists: OpenUser observed a no-price state with no fabricated metadata, while MiroFish raised questions about source/date/unit and transaction meaning. This is not statistically valid convergence and does not replace real sessions.

## 27. Baseline findings

Findings are recorded in `synthetic-findings.md` as `S16-001` through `S16-004`. The baseline exposed an unsupported browser deployment path and an unexecuted authenticated Sell journey. No product fix was made before evidence capture.

## 28. Fixes implemented

No product behavior fix was implemented. The test harness was repaired with an isolated backend process on 8002, a Vite proxy on 5174, and a local-only synthetic price fixture/account. The backend origin guard remained active; no production defaults, CSP, authentication, or authorization rules were weakened. The fixture is deleted/restored after the positive run.

## 29. Tests added

No application tests were added. Existing Packet 16 research infrastructure and the existing repository test suite were reused. Synthetic evidence is deliberately excluded from the real pilot analyzer.

## 30. Re-run results

The repaired empty-price rerun passed through login to `/sell`. The positive fixture rerun displayed crop, market, date, source, and unit and also reached `/sell`. It found two P2 inconsistencies: homepage versus `/prices` result mismatch and selected crop loss after login. The exact tasks have not yet been independently repeated.

## 31. Remaining synthetic P0/P1

No P0 or unresolved P1 remains in the repaired farmer smoke. Acceptance is still open because the required buyer, FPO, operations, and repeated farmer matrix has not been run. The remaining observed product issues are P2 and require repeat testing.

## 32. Language issues requiring native review

MiroFish raised English semantic distinctions around “reported,” “official,” “queued,” “published,” “payment initiated,” and “settled.” Hindi and Marathi wording was not independently reviewed by native speakers in this packet. No claim of translation comprehension is made.

## 33. Accessibility issues requiring human review

No dedicated OpenUser accessibility audit or assistive-technology session was completed. Keyboard, screen-reader, focus, touch-target, and 200% text behavior remain real-user/manual review priorities.

## 34. Real-user validation priorities

First validate source/date/unit and non-guarantee language with farmers and buyers. Then validate the Sell commitment boundary, offline status vocabulary, payment evidence labels, and FPO traceability language with the named participant panel. Use paid, consented sessions and the existing anonymized schema.

## 35. Regression results

`python -m pytest -q` was rerun from `backend/` and exited 0 with no failed or skipped tests; the run completed with one existing pytest-asyncio deprecation warning. Packet 16’s recorded baseline remains 225 backend tests, 40 frontend unit tests, and 30 browser tests passing. No Packet 16S code change was made to regress those results. Frontend lint/build/E2E results are inherited from Packet 16 and were not rerun because this packet made no frontend changes.

## 36. Files changed

Only `docs/pilot/synthetic/` evidence files were changed. Temporary OpenUser/Vite/backend wrapper files and generated OpenUser project files are removed after the run. No application source, migration, or real Packet 16 result file is changed.

## 37. Git status

The working tree already contains extensive uncommitted Packet 00–16 work. Packet 16S adds only the synthetic evidence directory; no commit, push, tag, merge, or deployment was performed.

## 38. Final recommendation

**Synthetic usability rehearsal: FAIL — continuation environment repaired, full matrix incomplete**

**Real Packet 16 evidence: BLOCKED / INSUFFICIENT**

**Engineering RC: READY unless a supported synthetic staging rerun exposes an engineering P0/P1 that remains unresolved**

**Recommended next action: FIX AND RE-RUN SYNTHETIC TESTS** for the two P2 findings and complete the buyer/FPO/operations matrix, then proceed to the real paid/consented pilot. Do not create Packet 17 and do not treat this synthetic result as real user validation.
