# SLO/SLA readiness

SLOs are proposed internal engineering targets; they are not measured achievements or contractual SLAs.

| Service | Metric | Initial target | Window/exclusions | Measurement gap |
|---|---|---:|---|---|
| API/auth | availability and error rate | 99.5% monthly pilot target | planned maintenance/provider outage separated | no production time series |
| Public price lookup | successful response latency | p95 ≤1.5 s in staging | cache/provider wait documented | local only |
| Core trade API | successful non-5xx requests | 99.5% monthly | dependency outages excluded only by approved policy | no load test |
| Outbox/notifications | oldest pending age | <15 min target | provider outage separated | worker metrics need deployment |
| Price ingestion | scheduled attempt completion | daily attempt by configured cadence | source publication is separate | no live provider |
| Admin operations | queue response/error | p95 ≤2 s staging | bounded page sizes | no production telemetry |

An SLA template must be contractually approved and include support hours, severity response targets, maintenance, backups, DR, exclusions and provider dependency inheritance. Do not promise uptime or price freshness beyond upstream evidence.

## Support model template

L1 handles user/account and workflow questions; L2 handles deployment, data and provider operations; L3 handles engineering defects and vendor escalation. Staffing, hours and response targets are contract decisions, not implied by this repository.
