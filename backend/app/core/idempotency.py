from fastapi import Request
from sqlalchemy.orm import Session

from app.models import IdempotencyKey


def _build_scoped_key(request: Request, user=None) -> str | None:
    raw_key = request.headers.get("Idempotency-Key")
    if not raw_key:
        return None
    if user is not None:
        uid = str(getattr(user, "id", user))
    else:
        uid = str(getattr(getattr(request, "state", None), "user_id", "anon"))
    path = getattr(getattr(request, "url", None), "path", "/unknown")
    method = getattr(request, "method", "POST")
    return f"{uid}:{method}:{path}:{raw_key}"


def check_idempotency(request: Request, db: Session, user=None):
    scoped_key = _build_scoped_key(request, user)
    if not scoped_key:
        return None
    existing = db.get(IdempotencyKey, scoped_key)
    if existing and existing.response_body is not None:
        return existing
    return None


def save_idempotency(request: Request, db: Session, status: int, body: dict, user=None):
    scoped_key = _build_scoped_key(request, user)
    if not scoped_key:
        return
    existing = db.get(IdempotencyKey, scoped_key)
    if existing:
        existing.response_status = status
        existing.response_body = body
    else:
        db.add(IdempotencyKey(key=scoped_key, response_status=status, response_body=body))
    db.commit()
