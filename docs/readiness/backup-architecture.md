# Backup architecture (design target)

Backups must cover PostgreSQL/PostGIS, private object storage, deployment configuration and critical metadata. Use encrypted full plus incremental/WAL strategy where the chosen PostgreSQL service supports it, with an offsite/separate-failure-domain copy, access audit and periodic restore verification. Object storage needs versioning/lifecycle policy and a separate backup decision. Secrets are re-created from the approved secret manager, never copied into repository backups.

Targets below are proposals, not measurements:

| Tier | RPO target | RTO target | Evidence required |
|---|---:|---:|---|
| Core API/database | ≤24 h initially | ≤8 h initially | PostgreSQL restore drill |
| Object evidence | ≤24 h initially | ≤12 h initially | object restore/sample integrity |
| Redis/cache | Best effort; domain data is not Redis-only | ≤4 h | rebuild/failover test |

No live PostgreSQL backup or restore drill was available for Packet 14. SQLite is not a substitute and must not be presented as PostgreSQL evidence.
