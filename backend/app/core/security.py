from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_ctx = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(sub: str, role: str, extra: dict[str, Any] | None = None) -> str:
    import uuid

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_access_ttl_min)
    payload: dict[str, Any] = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": exp,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(sub: str, session_id: str | None = None) -> str:
    import uuid

    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.jwt_refresh_ttl_days)
    payload = {"sub": sub, "iat": now, "exp": exp, "type": "refresh", "jti": str(uuid.uuid4())}
    if session_id:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


import hashlib
import logging

logger = logging.getLogger("krishilink.security")
_in_memory_revoked_tokens: set[str] = set()


def _token_identifier(token: str, payload: dict[str, Any] | None = None) -> str:
    if payload and "jti" in payload:
        return f"jti:{payload['jti']}"
    h = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def revoke_token(token: str, payload: dict[str, Any] | None = None) -> None:
    if not token:
        return
    if payload is None:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
        except Exception:
            payload = None

    ident = _token_identifier(token, payload)
    ttl = settings.jwt_access_ttl_min * 60
    if payload and "exp" in payload:
        exp_ts = payload["exp"]
        now_ts = datetime.now(timezone.utc).timestamp()
        remaining = int(exp_ts - now_ts)
        if remaining > 0:
            ttl = remaining
    elif payload and payload.get("type") == "refresh":
        ttl = settings.jwt_refresh_ttl_days * 86400

    from app.core.rate_limit import get_redis
    r = get_redis()
    if r is not None:
        try:
            r.setex(f"bl:{ident}", ttl, "revoked")
            return
        except Exception as e:
            logger.warning("Redis error setting token blacklist: %s. Falling back to in-memory (dev-only).", e)

    _in_memory_revoked_tokens.add(ident)
    logger.info("Token %s added to node-local in-memory blacklist (development-only).", ident)


def is_token_revoked(token: str, payload: dict[str, Any] | None = None) -> bool:
    if not token:
        return False
    if payload is None:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
        except Exception:
            payload = None

    ident = _token_identifier(token, payload)
    from app.core.rate_limit import get_redis
    r = get_redis()
    if r is not None:
        try:
            return bool(r.exists(f"bl:{ident}"))
        except Exception as e:
            logger.warning("Redis error checking token blacklist: %s. Falling back to in-memory (dev-only).", e)

    return ident in _in_memory_revoked_tokens


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
