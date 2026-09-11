from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "krishilink",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "outbox.poller": {
            "task": "outbox.process_pending",
            "schedule": 5.0,
        },
        "reservations.expire": {
            "task": "reservations.expire",
            "schedule": 60.0,
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])


@celery_app.task(name="health.ping")
def ping():
    return "pong"


@celery_app.task(name="reservations.expire")
def expire_reservations():
    from datetime import datetime, timezone

    from app.core.database import SessionLocal
    from app.models import Reservation

    db = SessionLocal()
    try:
        expired = (
            db.query(Reservation)
            .filter(Reservation.status == "ACTIVE", Reservation.expires_at < datetime.now(timezone.utc))
            .update({"status": "EXPIRED"})
        )
        db.commit()
        return {"expired": expired}
    finally:
        db.close()


@celery_app.task(name="notifications.dispatch_deal_confirmation_sms", bind=True, max_retries=3, default_retry_delay=15)
def dispatch_deal_confirmation_sms(self, payload: dict):
    """
    Asynchronously delivers deal confirmation SMS to the farmer.
    Safe from transaction rollbacks.
    """
    from app.modules.notifications.sms_service import SMSService

    try:
        return SMSService.send_deal_confirmation(
            farmer_phone=payload.get("farmer_phone"),
            farmer_name=payload.get("farmer_name"),
            crop_name=payload.get("crop_name", "Produce"),
            quantity=payload.get("quantity", 0),
            price_per_unit=payload.get("price_per_unit", 0),
            order_id=payload.get("order_id", ""),
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="outbox.process_pending", bind=True, max_retries=3, default_retry_delay=10)
def process_outbox(self):
    from urllib.parse import urlparse

    import redis

    from app.core.database import SessionLocal
    from app.models import OutboxEvent

    db = SessionLocal()
    try:
        # Use row locking with skip_locked to support safe multi-worker concurrency
        pending = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "PENDING")
            .order_by(OutboxEvent.created_at)
            .with_for_update(skip_locked=True)
            .limit(100)
            .all()
        )

        if not pending:
            return {"processed": 0}

        # Get Redis client for stream publishing
        parsed = urlparse(settings.redis_url)
        r = redis.Redis(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            password=parsed.password or None,
            db=int(parsed.path.lstrip("/")) if parsed.path else 0,
            decode_responses=True,
        )

        processed = 0
        for event in pending:
            try:
                stream_key = f"events:{event.aggregate}"
                r.xadd(
                    stream_key,
                    {
                        "event_id": str(event.id),
                        "aggregate": event.aggregate,
                        "aggregate_id": event.aggregate_id,
                        "event_type": event.event_type,
                        "payload": str(event.payload),
                    },
                )

                # Dispatch dedicated SMS task if event is deal.confirmed.sms
                if event.event_type == "deal.confirmed.sms" and isinstance(event.payload, dict):
                    try:
                        dispatch_deal_confirmation_sms.delay(event.payload)
                    except Exception:
                        dispatch_deal_confirmation_sms(event.payload)

                event.status = "COMPLETED"
                processed += 1
            except Exception:
                event.retry_count += 1
                if event.retry_count >= 3:
                    event.status = "FAILED"
                # Log error, continue with next event

        db.commit()
        return {"processed": processed, "total_pending": len(pending)}
    finally:
        db.close()
