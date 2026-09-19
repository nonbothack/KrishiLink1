# Packet 16S findings

## S16-001 — price surface depends on test environment and data availability

- **SOURCE:** OPENUSER
- **ROLE:** FARMER
- **SCENARIO:** SF-SMOKE / run_KNWrj60n_VaW
- **BUILD:** local static preview on `localhost:5173`
- **EVIDENCE:** OpenUser critical finding `fnd__ZmQZDwRKDiP`; same-origin `/api` returned the SPA shell; backend `/api/v1/prices` was reachable directly but contained zero observations; CSP inline-script errors were recorded.
- **FREQUENCY:** one baseline run
- **SEVERITY:** P1 environmental test blocker (OpenUser tool label: critical)
- **TYPE:** TRUTH / WORKFLOW
- **RECOMMENDATION:** run browser rehearsal only against a supported frontend/backend deployment with an explicit API proxy and a known empty-data fixture; preserve the truthful empty state when observations are absent.
- **DECISION:** TEST_MORE; no product fix or fabricated price was introduced.
- **REAL_USER_VALIDATION_REQUIRED:** YES

## S16-002 — truthful no-price state is understandable but prevents price comparison when the registry is empty

- **SOURCE:** OPENUSER
- **ROLE:** FARMER
- **SCENARIO:** SF-ENV / run_SdrbfNqzHXmX
- **BUILD:** Vite dev server on `localhost:5174` proxying to backend 8001
- **EVIDENCE:** run summary and screenshots show `No prices reported for these filters. Try another crop or market.` No price, source, date, or unit was fabricated.
- **FREQUENCY:** one correctly proxied run; not repeated three times
- **SEVERITY:** P2 / EXPECTED_UNAVAILABLE
- **TYPE:** CONTENT / TRUST
- **RECOMMENDATION:** validate the empty state with real farmers and add a deterministic staging fixture for positive price journeys. Keep the unavailable state when official observations do not exist.
- **DECISION:** TEST_MORE
- **REAL_USER_VALIDATION_REQUIRED:** YES

## S16-003 — login could not be tested through the temporary 5174 origin

- **SOURCE:** OPENUSER
- **ROLE:** FARMER
- **SCENARIO:** SF-LOGIN / run_GJQ_ufntLyry
- **BUILD:** Vite dev server on `localhost:5174`; backend active origin policy
- **EVIDENCE:** HTTP 403 `Unrecognized browser origin` from `/api/v1/auth/login`. The backend origin guard correctly rejected the temporary test origin.
- **FREQUENCY:** one run
- **SEVERITY:** P1 environmental test blocker
- **TYPE:** SECURITY / WORKFLOW
- **RECOMMENDATION:** provide a supported staging URL or explicitly allow the test origin in an isolated test process; do not weaken production origin checks.
- **DECISION:** TEST_MORE
- **REAL_USER_VALIDATION_REQUIRED:** YES

## S16-004 — semantic metadata needs direct comprehension validation

- **SOURCE:** MIROFISH
- **ROLE:** FARMER / BUYER / FPO
- **SCENARIO:** three-round multi-stakeholder trust-and-state simulation
- **BUILD:** external MiroFish commit above, redacted KrishiLink source pack
- **EVIDENCE:** report themes repeatedly ask whether price is official/current, whether Sell is binding, whether queued lots are buyer-visible, and whether payment is provider-confirmed.
- **FREQUENCY:** repeated across the simulated round-0 discourse; no real-user frequency claim
- **SEVERITY:** P2
- **TYPE:** TRUST / CONTENT / OFFLINE
- **RECOMMENDATION:** run comprehension tasks with real participants using source/date/unit, Sell, offline, and payment labels.
- **DECISION:** TEST_MORE
- **REAL_USER_VALIDATION_REQUIRED:** YES

## S16-005 — repaired empty-price smoke reaches Sell

- **SOURCE:** OPENUSER
- **ROLE:** FARMER
- **SCENARIO:** SF-LOGIN / run_PThKmMh9IUjq
- **BUILD:** Vite 5174 proxying isolated local backend 8002; origin explicitly allow-listed for local test only
- **EVIDENCE:** run passed; login returned successfully, sell destination was preserved, and `/sell` opened. The backend continued to report an empty official observation set.
- **FREQUENCY:** one repaired smoke run
- **SEVERITY:** P2 / SUCCESS
- **TYPE:** WORKFLOW / EXPECTED_UNAVAILABLE
- **RECOMMENDATION:** retain this as the regression smoke path and repeat with real participants later.
- **DECISION:** KEEP
- **REAL_USER_VALIDATION_REQUIRED:** YES

## S16-006 — homepage and Market prices page disagree under the same synthetic fixture

- **SOURCE:** OPENUSER
- **ROLE:** FARMER
- **SCENARIO:** SF-LOGIN / run_buhIFmwBFPJJ
- **BUILD:** Vite 5174 proxying isolated local backend 8002
- **EVIDENCE:** homepage search showed no Chilli price, while `/prices` showed the clearly labelled synthetic fixture. The run recorded the mismatch in `fnd_BIzaUWgmdnNH`.
- **FREQUENCY:** one positive fixture run; not independently repeated
- **SEVERITY:** P2
- **TYPE:** UX_CONFUSION / DATA_CONSISTENCY
- **RECOMMENDATION:** investigate request timing/cache/filter differences and rerun the exact task before changing product logic.
- **DECISION:** TEST_MORE
- **REAL_USER_VALIDATION_REQUIRED:** YES

## S16-007 — selected crop is lost after login even though the sell destination is preserved

- **SOURCE:** OPENUSER
- **ROLE:** FARMER
- **SCENARIO:** SF-LOGIN / run_buhIFmwBFPJJ
- **BUILD:** Vite 5174 proxying isolated local backend 8002
- **EVIDENCE:** `/sell?crop=Chilli&price=2400.00...` opened after login, but the Crop field remained `Choose a crop`; the run recorded `fnd_uHhr3b19x_wg`.
- **FREQUENCY:** one positive fixture run; not independently repeated
- **SEVERITY:** P2
- **TYPE:** UX_CONFUSION / WORKFLOW
- **RECOMMENDATION:** verify query-to-form hydration and rerun the exact task; preserve backend price authority.
- **DECISION:** TEST_MORE
- **REAL_USER_VALIDATION_REQUIRED:** YES
