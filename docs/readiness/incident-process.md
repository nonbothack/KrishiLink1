# Deployment incident process

Use the Packet 13 incident record and runbooks. Do not name individual employees in repository documentation.

1. **DETECT** — alert, provider report, support report or audit anomaly; preserve request/correlation IDs.
2. **TRIAGE** — assign severity, incident commander, technical owner and communication owner; establish affected capability and timeline.
3. **CONTAIN** — disable the affected feature flag/provider path, restrict access or isolate the component. Do not mutate trade/payment history to hide impact.
4. **ERADICATE** — remove the cause, rotate/revoke compromised secrets, patch and preserve evidence.
5. **RECOVER** — restore service/data through the approved runbook, validate invariants and communicate degraded states honestly.
6. **REVIEW** — record root cause, evidence, timeline, customer impact, corrective actions and retest/postmortem owner.

Severity is operational (LOW/MEDIUM/HIGH/CRITICAL) and is not a legal conclusion. Legal/security leadership decides notification responsibilities, retention and reporting timelines.
