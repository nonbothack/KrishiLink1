# Load test — Packet 15

**Status: PASS WITH QUALIFICATION — isolated 30-minute run**

Target: `5 RPS` against `GET /api/v1/health` on the immutable-code FastAPI
stack; duration `1,800 s`.

- Requests: `8,997`
- HTTP 200: `8,951`
- client/network errors: `46`
- measured success: `99.4887%`
- P50: `3.53 ms`
- P95: `6.28 ms`
- P99: `13.39 ms`
- maximum: `2,041.00 ms`

The errors overlap the intentional Redis/PostgreSQL outage and container
recreation drills during this run, so this is not a clean steady-state SLO
measurement. It is a bounded local pilot smoke/load result, not district/state
capacity evidence. Raw output is retained in `evidence/load-30m.json`.
