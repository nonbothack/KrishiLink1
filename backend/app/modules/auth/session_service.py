"""Database-backed refresh-token rotation and session-family revocation."""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, is_token_revoked, revoke_token
from app.models import AuditLog, AuthSession, User


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_ttl_days)


def issue_tokens(user: User, session_id: str | None = None) -> dict[str, str | int]:
    sid = session_id or str(uuid.uuid4())
    version = int(getattr(user, "auth_token_version", 0) or 0)
    access = create_access_token(str(user.id), user.role, {"sid": sid, "ver": version})
    refresh = create_refresh_token(str(user.id), sid, version)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_ttl_min * 60,
    }


def create_session_tokens(db: Session, user: User, user_agent: str | None = None) -> dict[str, str | int]:
    sid = str(uuid.uuid4())
    tokens = issue_tokens(user, sid)
    db.add(
        AuthSession(
            id=sid,
            family_id=sid,
            user_id=user.id,
            refresh_token_hash=_digest(str(tokens["refresh_token"])),
            expires_at=_expiry(),
            user_agent=user_agent[:500] if user_agent else None,
        )
    )
    db.commit()
    return tokens


def _revoke_family(db: Session, session: AuthSession, reason: str) -> None:
    now = datetime.now(timezone.utc)
    db.query(AuthSession).filter(
        AuthSession.family_id == session.family_id,
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: now, AuthSession.revoked_reason: reason}, synchronize_session=False)
    db.add(
        AuditLog(
            actor_id=str(session.user_id),
            action="auth.session_family_revoked",
            entity="session_family",
            entity_id=session.family_id,
            after={"reason": reason},
        )
    )
    db.commit()


def refresh_session(db: Session, refresh_token: str) -> dict[str, str | int]:
    try:
        payload = decode_token(refresh_token)
    except (jwt.InvalidTokenError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")
    if payload.get("type") != "refresh" or not payload.get("sid"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")

    sid = str(payload["sid"])
    session = db.query(AuthSession).filter(AuthSession.id == sid).with_for_update().first()
    # Sessions created before this migration have no row. Exchange one legacy
    # refresh token into a managed family without invalidating the account.
    if session is None:
        try:
            user = db.get(User, uuid.UUID(str(payload.get("sub"))))
        except (ValueError, TypeError):
            user = None
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")
        if int(payload.get("ver", 0)) != int(getattr(user, "auth_token_version", 0) or 0):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended")
        expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc)
        if is_token_revoked(refresh_token, payload) or db.query(AuditLog).filter(
            AuditLog.action == "session.revoked", AuditLog.entity_id == sid
        ).first():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended")
        session = AuthSession(
            id=sid,
            family_id=sid,
            user_id=user.id,
            refresh_token_hash=_digest(refresh_token),
            expires_at=expires_at,
        )
        db.add(session)
        try:
            db.flush()
            db.commit()
        except IntegrityError:
            db.rollback()
            session = db.query(AuthSession).filter(AuthSession.id == sid).with_for_update().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")
    if session.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended")

    if not hmac.compare_digest(session.refresh_token_hash, _digest(refresh_token)):
        _revoke_family(db, session, "refresh_reuse_detected")
        revoke_token(refresh_token, payload)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended")

    if is_token_revoked(refresh_token, payload):
        _revoke_family(db, session, "refresh_token_revoked")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended")

    if _utc(session.expires_at) <= datetime.now(timezone.utc):
        _revoke_family(db, session, "expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        _revoke_family(db, session, "account_unavailable")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")
    if int(payload.get("ver", 0)) != int(getattr(user, "auth_token_version", 0) or 0):
        _revoke_family(db, session, "credential_version_changed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session ended")

    tokens = issue_tokens(user, sid)
    session.refresh_token_hash = _digest(str(tokens["refresh_token"]))
    session.expires_at = _expiry()
    session.last_used_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="auth.session_refreshed",
            entity="session",
            entity_id=sid,
            after={"outcome": "rotated"},
        )
    )
    db.commit()
    return tokens


def revoke_session(db: Session, session_id: str | None, user: User, reason: str = "logout") -> None:
    if not session_id:
        return
    session = db.get(AuthSession, session_id)
    if session and session.user_id == user.id and session.revoked_at is None:
        _revoke_family(db, session, reason)


def revoke_user_sessions(db: Session, user: User, reason: str) -> None:
    now = datetime.now(timezone.utc)
    db.query(AuthSession).filter(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None)).update(
        {AuthSession.revoked_at: now, AuthSession.revoked_reason: reason}, synchronize_session=False
    )


def session_is_revoked(db: Session, session_id: str) -> bool:
    row = db.get(AuthSession, session_id)
    return bool(row and row.revoked_at is not None)
