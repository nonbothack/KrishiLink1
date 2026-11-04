import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, status
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import AuditLog, OutboxEvent, User


def _geog(lat, lng):
    if lat is None or lng is None:
        return None
    return WKTElement(f"POINT({lng} {lat})", srid=4326, extended=True)


def register_user(db: Session, data, request: Request):
    if not data.email and not data.phone:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either phone number or email is required",
        )

    # Check for existing user
    if data.email:
        existing = db.query(User).filter(User.email == data.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please log in.",
            )
    if data.phone:
        existing = db.query(User).filter(User.phone == data.phone).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists. Please log in.",
            )

    uid = uuid.uuid4()
    latlng = {"Nashik": (19.9975, 73.7898), "Pune": (18.5204, 73.8567), "Mumbai": (19.0760, 72.8777)}.get(
        data.district or data.location or "Pune", (18.5204, 73.8567)
    )
    user = User(
        id=uid,
        email=data.email.lower() if data.email else None,
        phone=data.phone,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=data.role.lower(),
        location=data.location,
        district=data.district or data.location,
        state=data.state or "Maharashtra",
        location_geog=_geog(*latlng) if latlng else None,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(uid),
            action="user.register",
            entity="users",
            entity_id=str(uid),
            after={"email": data.email, "role": data.role},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="users",
            aggregate_id=str(uid),
            event_type="user.registered",
            payload={"user_id": str(uid), "email": data.email, "role": data.role},
        )
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email_or_phone: str, password: str, request: Request):
    login_id = email_or_phone.strip()
    clean_id = login_id.lower()

    # Disallow demo accounts in production immediately
    if (settings.env == "production" or not settings.demo_mode) and (
        clean_id == "admin@krishilink.demo"
        or clean_id.endswith("@demo.com")
        or clean_id.endswith("@krishilink.demo")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts have been disabled in production.",
        )

    user = db.query(User).filter((User.email == clean_id) | (User.phone == login_id)).first()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password. Please check your credentials.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    # Automatically grant admin role to designated authorized admin emails
    if user.email and user.email.lower() in settings.admin_emails_list and user.role != "admin":
        user.role = "admin"
        db.commit()
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.login",
            entity="users",
            entity_id=str(user.id),
            after={"login": login_id},
            request_id=rid,
        )
    )
    db.commit()
    return user


def issue_tokens(user: User):
    access = create_access_token(str(user.id), user.role)
    refresh = create_refresh_token(str(user.id))
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_ttl_min * 60,
    }


def refresh_tokens(db: Session, refresh_token: str):
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    uid = payload.get("sub")
    try:
        user = db.get(User, uuid.UUID(uid))
    except Exception:
        user = None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return issue_tokens(user)


def request_password_reset(db: Session, email: str, request: Request):
    user = db.query(User).filter(User.email == email.lower()).first()
    # Always return a generic success message to prevent account enumeration
    if not user:
        return {"message": "If an account exists with this email, password reset instructions have been generated."}

    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    reset_token = jwt.encode(
        {"sub": str(user.id), "type": "password_reset", "exp": exp},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.password_reset_request",
            entity="users",
            entity_id=str(user.id),
            after={"email": email},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="users",
            aggregate_id=str(user.id),
            event_type="user.password_reset_requested",
            payload={"user_id": str(user.id), "email": email, "token": reset_token},
        )
    )
    db.commit()
    return {
        "message": "If an account exists with this email, password reset instructions have been generated.",
        "dev_reset_token": reset_token if settings.env == "development" else None,
    }


def reset_password(db: Session, token: str, new_password: str, request: Request):
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token.")

    if payload.get("type") != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type for password reset.")

    uid = payload.get("sub")
    try:
        user = db.get(User, uuid.UUID(uid))
    except Exception:
        user = None

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found or inactive.")

    user.password_hash = hash_password(new_password)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.password_reset_complete",
            entity="users",
            entity_id=str(user.id),
            after={"status": "password_updated"},
            request_id=rid,
        )
    )
    db.commit()
    return {"message": "Password has been successfully updated. You may now log in with your new password."}
