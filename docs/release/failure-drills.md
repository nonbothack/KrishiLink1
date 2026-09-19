# Failure drills — Packet 15

**Status: PASS — bounded service outage/recovery checks**

In the isolated Compose project, stopping Redis returned readiness `503` and
restarting it restored `200`. Stopping PostgreSQL returned readiness `503` and
restarting it restored `200`. Celery worker/Beat remained available after
recovery, and MinIO accepted/deleted a private object while anonymous access
remained private.

External SMS/push delivery and a full dead-letter/retry-exhaustion drill remain
unverified because no external provider is configured.
