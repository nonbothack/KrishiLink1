import uuid

from sqlalchemy.orm import Session

from app.models import Notification, OutboxEvent


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        user_id: uuid.UUID | str,
        type_: str,
        title: str,
        message: str,
        related_id: uuid.UUID | str | None = None,
        outbox: bool = True,
        metadata: dict | None = None,
    ) -> Notification:
        u_id = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        r_id = related_id if (related_id is None or isinstance(related_id, uuid.UUID)) else uuid.UUID(str(related_id))

        notif = Notification(
            id=uuid.uuid4(), user_id=u_id, type=type_, title=title, message=message,
            related_id=r_id, is_read=False, metadata_json=metadata,
        )
        db.add(notif)

        if outbox:
            event = OutboxEvent(
                id=uuid.uuid4(),
                aggregate="notification",
                aggregate_id=str(notif.id),
                event_type=f"NOTIFICATION_{type_.upper()}",
                payload={
                    "user_id": str(u_id),
                    "title": title,
                    "message": message,
                    "type": type_,
                    "related_id": str(r_id) if r_id else None,
                    "metadata": metadata,
                },
                status="PENDING",
            )
            db.add(event)

        return notif
