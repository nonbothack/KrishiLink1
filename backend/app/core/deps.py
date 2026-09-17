import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import AuditLog, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    sid = payload.get("sid")
    if sid and db.query(AuditLog).filter(AuditLog.action == "session.revoked", AuditLog.entity_id == sid).first():
        raise HTTPException(401, "Session ended")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = None
    try:
        import uuid

        uid = uuid.UUID(user_id)
        user = db.get(User, uid)
    except Exception:
        user = db.query(User).filter(User.email == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    request.state.user = user
    request.state.user_role = payload.get("role")
    return user


def get_optional_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    try:
        return get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_role(*allowed: str):
    allowed_set = {r.lower() for r in allowed}

    def checker(user: User = Depends(get_current_user)):
        if user.role.lower() not in allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role {user.role} not allowed")
        return user

    return checker


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", request.headers.get("X-Request-ID", ""))
