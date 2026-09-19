# Soak test — Packet 15

**Status: PASS WITH QUALIFICATION — 30-minute bounded run**

The 1,800-second, 5 RPS readiness soak completed with 8,997 requests. The
observed p95 was 6.28 ms and p99 13.39 ms; 46 requests errored while the
intentional Redis/PostgreSQL outage and application-container recreation drills
were performed. Docker resource samples were captured during the run; no
unbounded memory growth was observed in the single sample.

Because the run included planned fault injection and used one local Docker
host, it does not establish production availability, RPO/RTO, district/state
capacity or a contractual SLA. Raw output: `evidence/load-30m.json`.
