# Disaster recovery and business continuity

The current stack is a single-region/single-deployment design unless the deployment owner adds managed redundancy. There is no verified active-active or multi-region replication.

| Failure | Known behavior/fallback | Operator action |
|---|---|---|
| PostgreSQL/PostGIS down | Core API and writes fail; no shadow ledger is authorized | restore/failover and reconcile |
| Redis down | distributed rate-limit/broker/cache features degrade or fail closed; domain data is not Redis-only | restore Redis, inspect outbox/worker health |
| Celery/beat down | asynchronous sync/notifications/alerts pause; in-request domain writes remain where supported | restart one worker/beat, drain safely |
| Object storage down | evidence/upload paths unavailable | keep references/status truthful; restore provider |
| SMS down | production OTP delivery fails closed | provider escalation/manual support path |
| Web Push down | in-app notifications remain | inspect attempts; no false delivery claim |
| Price provider down | persisted observations remain with actual freshness | mark stale/unavailable; do not fabricate |
| Forecast disabled | descriptive price history remains | retain kill-switch audit |

Drill checklist: database loss, Redis loss, worker loss, object-storage failure, provider outage and bad application deployment. Record RPO/RTO, evidence, issues and retest. Manual continuity must preserve an auditable reference and later reconciliation; it must not become an unaudited shadow system.
