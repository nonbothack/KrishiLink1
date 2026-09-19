# OpenUser runs

## Tool and daemon

- Repository: https://github.com/manalkaff/openuser
- Package: `openuser-cli` 0.1.1
- Daemon: `http://127.0.0.1:8737` (localhost only)
- Configuration: project base URL first `http://localhost:5173`, then patched for test execution to `http://localhost:5174`; no production configuration was changed.
- Browser: Playwright Chromium installed locally by `npx playwright install chromium`.
- Credentials were used only in the local demo/test database; they are not recorded here.

## Runs

| Run | Base URL | Scenario | Result | Evidence |
|---|---|---|---|---|
| `run_KNWrj60n_VaW` | 5173 | first-time farmer checks price and Sell | failed; price API was same-origin SPA because the static preview had no API proxy; CSP inline-script errors were also reported | OpenUser artifact under `C:\Users\a\.openuser\artifacts\run_KNWrj60n_VaW` |
| `run_SdrbfNqzHXmX` | 5174 | farmer checks price and Sell through Vite proxy | `goal_achieved`; truthful empty state was observed, login fixture was rejected with HTTP 401 | OpenUser artifact under `C:\Users\a\.openuser\artifacts\run_SdrbfNqzHXmX` |
| `run_GJQ_ufntLyry` | 5174 | farmer checks price, uses synthetic account, reaches Sell | blocked; backend rejected temporary 5174 browser origin with HTTP 403 | OpenUser artifact under `C:\Users\a\.openuser\artifacts\run_GJQ_ufntLyry` |
| `run_PThKmMh9IUjq` | 5174 → isolated 8002 backend | repaired empty-price smoke: price state, Sell entry, login, sell form | passed; no findings | OpenUser artifact under `C:\Users\a\.openuser\artifacts\run_PThKmMh9IUjq` |
| `run_buhIFmwBFPJJ` | 5174 → isolated 8002 backend | positive synthetic price provenance, Sell entry, login, sell form | passed; two medium UX findings | OpenUser artifact under `C:\Users\a\.openuser\artifacts\run_buhIFmwBFPJJ` |

The first run's `critical` OpenUser label is retained as tool evidence. After inspection, its price failure is triaged to the incorrectly configured static preview and empty official dataset, not to permission to fabricate a price. The repaired 5174 → 8002 runs show the app's honest `No prices reported for these filters` state, preserve the sell destination through login, and reach `/sell`. A separate local-only fixture exposed the price source/date/unit correctly, while also revealing two P2 UX inconsistencies recorded in `synthetic-findings.md`. No security control was weakened to force the run through.

The requested approximately-30 matrix is still not complete: five farmer runs are recorded here, with no browser buyer, FPO, or operations runs. This continuation therefore proves environment repair and the farmer smoke paths; it does not claim full matrix completion.
