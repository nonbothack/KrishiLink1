# Packet 15B clean soak

**PASS — CLEAN_STEADY_STATE_RUN**

The clean run used RC_B, the isolated PostgreSQL/PostGIS + Redis + Celery + MinIO + FastAPI + nginx stack, with no deliberate outage or restart. It ran for 30 minutes at approximately 5 requests/second against the readiness endpoint and recorded 8,997 successful responses with no errors. The complete JSON, including endpoint latency and start/end resource snapshots, is in `load-30m-clean.json`.

The earlier outage-overlap run remains available as a separate qualified rehearsal in `load-30m.json`; its errors are not mixed into this result.
