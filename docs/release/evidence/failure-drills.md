# Failure-drill evidence

**Status: PASS — bounded service outage/recovery checks.**

In the isolated Compose project:

- stopping Redis made `/api/v1/health/ready` return `503`; restarting it
  restored `200` with database and Redis healthy;
- stopping PostgreSQL made readiness return `503`; restarting it restored
  `200`;
- Celery worker and Beat remained running and the outbox poller executed after
  recovery;
- MinIO accepted and removed a private test object; anonymous access remained
  private.

Provider delivery, external SMS/push and a full dead-letter/retry exhaustion
 drill remain unverified because no external provider is configured.
