# Capacity and cost model

These are planning scenarios, not load-test results or a claim of national scale.

| Scenario | Users | Daily logins | Price reads | Lots/offers/trades | Upload assumption |
|---|---:|---:|---:|---:|---:|
| Pilot | 1,000 | 300 | 5,000 | 100 / 200 / 50 | 1 GB/month |
| District | 25,000 | 7,500 | 125,000 | 2,500 / 5,000 / 1,250 | 25 GB/month |
| State planning | 250,000 | 75,000 | 1,250,000 | 25,000 / 50,000 / 12,500 | 250 GB/month |

Assumptions must be replaced by observed traffic. Growth candidates are price observations, TradeEvents, AuditLogs, notifications/outbox, push attempts and FPO intakes. Object growth depends on actual image/evidence size and retention. Cost categories are compute, PostgreSQL/PostGIS, Redis, workers, object storage, egress, SMS, push, monitoring and backups. No exact bill or “crore farmers” claim is made.
