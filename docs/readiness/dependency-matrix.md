# Dependency and failure matrix

| Dependency | Required for | Failure behavior | User impact | Operator action |
|---|---|---|---|---|
| PostgreSQL/PostGIS | all persisted domain state | API degraded/down | reads/writes unavailable | database recovery |
| Redis | distributed limits, broker/cache | fail-closed/degraded features | login/async delays | restore/inspect |
| Celery | ingestion, outbox/push jobs | queued work pauses | stale notifications/data | restart/drain |
| Object storage | evidence/media | upload/read unavailable | evidence pending | provider recovery |
| Official price provider | fresh observations | latest persisted/stale | price freshness reduced | source health/runbook |
| SMS | production OTP | fail closed | cannot start OTP login | provider escalation |
| Web Push | optional push | in-app remains | no browser push | inspect attempts |
| Payment/assay/logistics | later provider facts | pending/unavailable | no verified settlement/quality/logistics | manual/provider review |
