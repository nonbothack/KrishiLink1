# Provider/subprocessor inventory

| Category | Purpose/data shared | Current state | Failure truth |
|---|---|---|---|
| AGMARKNET/data.gov.in | reported market observations | key/configuration required | no new data; persisted observations can be stale |
| SMS provider | OTP/message destination and template | production credentials/approval required | OTP fails closed when unavailable |
| Redis service | rate limit, cache, broker | deployment dependency | async/limits degrade; not domain storage |
| PostgreSQL/PostGIS | application data and coordinates | deployment dependency | core service unavailable |
| Object storage | private evidence/media | configuration required | upload/read unavailable |
| Web Push service | browser endpoint delivery | opt-in VAPID/provider path | in-app remains; attempt is not receipt |
| Payment provider | future verified settlement | not connected | participant report is not bank verification |
| Assay/logistics/storage | future evidence/quotes | not connected | pending/unavailable, never fabricated |

Contracts, data-transfer terms, region, subprocessors and retention must be approved per deployment. No provider contract is inferred from a code adapter.
