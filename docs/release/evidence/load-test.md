# Packet 15 load and soak evidence

Two runs are retained separately.

## CLEAN_STEADY_STATE_RUN — Packet 15B

Evidence: `load-30m-clean.json`.

- Duration: 1,800 seconds at target 5 RPS
- Requests: 8,997
- Responses: 8,997 HTTP 200; errors: 0
- P50/P95/P99: 6.59 / 8.89 / 12.92 ms
- Maximum: 112.23 ms
- No planned outages or container recreation occurred during this run.
- Backend memory: 244.9 MiB → 246.5 MiB
- Worker memory: 464.7 MiB → 527 MiB
- PostgreSQL connections: 10 → 11
- Redis used memory: 2,226,352 → 2,350,160 bytes
- Outbox pending: 0 → 0

The run met the frozen clean-run criterion of zero HTTP 5xx/request errors. Resource values are local Docker measurements, not production capacity limits.

## QUALIFIED_OUTAGE_OVERLAP_RUN — Packet 15A

The earlier `load-30m.json` remains unchanged: 8,997 requests, 8,951 HTTP 200, 46 errors overlapping deliberate outage/recreation drills, P50 3.53 ms, P95 6.28 ms, P99 13.39 ms and max 2,041 ms. It is qualified resilience evidence, not a clean steady-state SLO result.
