from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_ctx = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(plain, hashed)
    except Exception:
        return False


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


def create_refresh_token(sub: str) -> str:
    import uuid

    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.jwt_refresh_ttl_days)
    payload = {"sub": sub, "iat": now, "exp": exp, "type": "refresh", "jti": str(uuid.uuid4())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
