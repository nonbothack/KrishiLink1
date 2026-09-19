import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    decode_token,
    hash_password,
    revoke_token,
    verify_password,
)
from app.models import (
    AuditLog,
    BuyerProfile,
    ConsentRecord,
    District,
    FarmerProfile,
    FPOProfile,
    OutboxEvent,
    PasswordResetGrant,
    PhoneIdentityConflict,
    State,
    Subdistrict,
    User,
    VerificationRecord,
)
from app.modules.auth.identity import CURRENT_POLICIES, canonicalize_indian_mobile
from app.modules.auth.session_service import (
    issue_tokens as _issue_tokens,
)
from app.modules.auth.session_service import (
    refresh_session,
    revoke_session,
    revoke_user_sessions,
)


def normalize_phone(value):
    return canonicalize_indian_mobile(value)[1]


def _consent_record(user_id, policy_type: str, version: str, request: Request, source: str):
    return ConsentRecord(
        user_id=user_id,
        policy_type=policy_type,
        policy_version=version,
        source=source,
        user_agent=request.headers.get("user-agent", "")[:500] or None,
    )


def register_user(db: Session, data, request: Request):
    if not data.email and not data.phone:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either phone number or email is required",
        )

    phone_e164 = canonicalize_indian_mobile(data.phone)[0] if data.phone else None
    ticket = None
    if settings.env == "production":
        if not data.verification_ticket or not phone_e164:
            raise HTTPException(403, "Verify your mobile number before creating an account")
        if any(
            CURRENT_POLICIES[name]["status"] != "APPROVED"
            for name in ("terms", "privacy_notice")
        ):
            raise HTTPException(503, "Registration is paused while legal policy review is pending")
        if not data.policy_versions.get("terms") or not data.policy_versions.get("privacy_notice"):
            raise HTTPException(422, "Please acknowledge the current terms and privacy notice")
        if data.role == "buyer" and not data.business_name:
            raise HTTPException(422, "Business name is required for buyer onboarding")
        if data.role == "fpo" and not data.organization_name:
            raise HTTPException(422, "Organization name is required for FPO onboarding")
        try:
            ticket = decode_token(data.verification_ticket)
        except Exception:
            raise HTTPException(403, "Mobile verification is invalid or expired")
        if ticket.get("type") != "registration_ticket" or ticket.get("phone") != phone_e164:
            raise HTTPException(403, "Mobile verification is invalid or expired")
    elif data.verification_ticket:
        try:
            ticket = decode_token(data.verification_ticket)
        except Exception:
            raise HTTPException(403, "Mobile verification is invalid or expired")
        if ticket.get("type") != "registration_ticket" or ticket.get("phone") != phone_e164:
            raise HTTPException(403, "Mobile verification is invalid or expired")

    # Email remains optional for farmers; canonical phone identity is unique.
    if data.email:
        existing = db.query(User).filter(User.email == data.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please log in.",
            )
    if phone_e164:
        if db.get(PhoneIdentityConflict, phone_e164):
            raise HTTPException(409, "This mobile number needs account review before it can be used")
        existing = db.query(User).filter(
            (User.phone_canonical == phone_e164) | (User.phone == data.phone)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists. Please log in.",
            )

    state = db.get(State, data.state_id) if getattr(data, "state_id", None) else None
    district = db.get(District, data.district_id) if getattr(data, "district_id", None) else None
    subdistrict = db.get(Subdistrict, data.subdistrict_id) if getattr(data, "subdistrict_id", None) else None
    if data.state_id and not state:
        raise HTTPException(422, "Unknown state identifier")
    if data.district_id and not district:
        raise HTTPException(422, "Unknown district identifier")
    if data.subdistrict_id and not subdistrict:
        raise HTTPException(422, "Unknown subdistrict identifier")
    if district and state and district.state_id != state.id:
        raise HTTPException(422, "District does not belong to the selected state")
    if subdistrict and district and subdistrict.district_id != district.id:
        raise HTTPException(422, "Subdistrict does not belong to the selected district")
    if subdistrict and not district:
        raise HTTPException(422, "A district is required with a subdistrict")
    if district and not state:
        state = db.get(State, district.state_id)

    uid = uuid.uuid4()
    user = User(
        id=uid,
        email=data.email.lower() if data.email else None,
        phone=data.phone,
        phone_canonical=phone_e164,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password) if data.password else None,
        role=data.role.lower(),
        location=data.location,
        district=district.name if district else data.district,
        state=state.name if state else data.state,
        state_id=state.id if state else None,
        district_id=district.id if district else None,
        subdistrict_id=subdistrict.id if subdistrict else None,
        location_geog=None,
        coordinate_source=None,
        coordinate_confidence=None,
        coordinate_accuracy_m=data.coordinate_accuracy_m,
        is_verified=False,
        is_active=True,
    )
    if data.latitude is not None and data.longitude is not None and data.location_consent:
        from geoalchemy2 import WKTElement

        user.location_geog = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
        user.coordinate_source = "explicit_gps"
    if data.verification_ticket:
        user.phone_verified_at = datetime.now(timezone.utc)
    db.add(user)
    # Profiles, verification evidence and consent rows reference this identity.
    # Flush first because these models intentionally do not declare ORM relationships.
    db.flush()
    if data.latitude is not None and data.longitude is not None and data.location_consent:
        db.add(
            _consent_record(
                uid,
                "location_gps",
                CURRENT_POLICIES["privacy_notice"]["version"],
                request,
                "web_registration",
            )
        )
    if data.role == "farmer" and data.primary_crops:
        db.add(FarmerProfile(user_id=uid, primary_crops=data.primary_crops))
    elif data.role == "buyer" and data.business_name:
        db.add(
            BuyerProfile(
                user_id=uid,
                business_name=data.business_name.strip(),
                crops_interested=data.procurement_categories or None,
                business_verification_status="UNVERIFIED",
            )
        )
    elif data.role == "fpo" and data.organization_name:
        db.add(
            FPOProfile(
                user_id=uid,
                organization_name=data.organization_name.strip(),
                organization_verification_status="UNVERIFIED",
            )
        )
    if data.verification_ticket:
        db.add(
            VerificationRecord(
                user_id=uid,
                dimension="phone",
                status="VERIFIED",
                method="sms_otp",
                provider=ticket.get("provider") if ticket else None,
                checked_at=datetime.now(timezone.utc),
                evidence_metadata={"evidence": "one_time_phone_challenge"},
            )
        )
    elif data.phone:
        db.add(VerificationRecord(user_id=uid, dimension="phone", status="UNVERIFIED"))
    if data.email:
        db.add(VerificationRecord(user_id=uid, dimension="email", status="UNVERIFIED"))
    if data.role == "buyer":
        db.add(VerificationRecord(user_id=uid, dimension="business", status="UNVERIFIED"))
        db.add(VerificationRecord(user_id=uid, dimension="gst", status="UNVERIFIED"))
    if data.role == "fpo":
        db.add(VerificationRecord(user_id=uid, dimension="organization", status="UNVERIFIED"))

    required_policies = ("terms", "privacy_notice")
    if settings.env == "production" or data.policy_versions:
        for policy_type in required_policies:
            accepted_version = data.policy_versions.get(policy_type)
            current = CURRENT_POLICIES[policy_type]
            if accepted_version != current["version"]:
                raise HTTPException(422, "Please review and accept the current policy versions")
            db.add(_consent_record(user.id, policy_type, accepted_version, request, "web_registration"))
        if data.marketing_consent:
            current = CURRENT_POLICIES["marketing"]
            accepted_version = data.policy_versions.get("marketing", current["version"])
            if accepted_version != current["version"]:
                raise HTTPException(422, "Marketing consent version is outdated")
            db.add(_consent_record(user.id, "marketing", accepted_version, request, "web_registration"))
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(uid),
            action="user.register",
            entity="users",
            entity_id=str(uid),
            after={"role": data.role, "signup_path": "otp" if data.verification_ticket else "development_legacy"},
            request_id=rid,
        )
    )
    db.add(
        OutboxEvent(
            aggregate="users",
            aggregate_id=str(uid),
            event_type="user.registered",
            payload={"user_id": str(uid), "role": data.role},
        )
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return user


def authenticate_user(db: Session, email_or_phone: str, password: str, request: Request):
    login_id = email_or_phone.strip()
    user = None
    identifier_type = "email" if "@" in email_or_phone else "phone"
    if identifier_type == "email":
        user = db.query(User).filter(User.email == login_id.lower()).first()
    else:
        try:
            phone_e164, national = canonicalize_indian_mobile(email_or_phone)
        except ValueError:
            phone_e164, national = "", ""
        if phone_e164 and not db.get(PhoneIdentityConflict, phone_e164):
            matches = db.query(User).filter(
                (User.phone_canonical == phone_e164) | (User.phone == national)
            ).limit(2).all()
            user = matches[0] if len(matches) == 1 else None
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        db.add(
            AuditLog(
                actor_id=str(user.id) if user else None,
                action="auth.password_login_failed",
                entity="authentication",
                entity_id=None,
                after={"outcome": "invalid_credentials", "identifier_type": identifier_type},
                request_id=getattr(request.state, "request_id", None),
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sign-in details",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sign-in details")
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.login",
            entity="users",
            entity_id=str(user.id),
            after={"outcome": "success", "identifier_type": identifier_type},
            request_id=rid,
        )
    )
    db.commit()
    return user


def issue_tokens(user: User, session_id: str | None = None):
    return _issue_tokens(user, session_id)


def refresh_tokens(db: Session, refresh_token: str):
    return refresh_session(db, refresh_token)


def logout_user(
    db: Session,
    access_token: str | None,
    refresh_token: str | None,
    user: User,
    request: Request,
    session_id: str | None = None,
):
    if access_token:
        revoke_token(access_token)
    if refresh_token:
        revoke_token(refresh_token)
    revoke_session(db, session_id, user)
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="user.logout",
            entity="users",
            entity_id=str(user.id),
            after={"status": "logged_out", "revoked_tokens": bool(access_token or refresh_token)},
            request_id=rid,
        )
    )
    db.commit()
    return {"message": "Logged out successfully; session tokens invalidated."}


def request_password_reset(db: Session, email: str, request: Request):
    user = db.query(User).filter(User.email == email.lower()).first()
    # Keep the response independent of account existence. Production email
    # delivery is intentionally unavailable until a secure sender is configured.
    reset_token = None
    if user and settings.env == "development":
        exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        reset_token = jwt.encode(
            {"sub": str(user.id), "type": "password_reset", "jti": str(uuid.uuid4()), "exp": exp},
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        db.add(
            PasswordResetGrant(
                user_id=user.id,
                token_hash=hashlib.sha256(reset_token.encode()).hexdigest(),
                expires_at=exp,
            )
        )
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id) if user else None,
            action="auth.password_reset_requested",
            entity="authentication",
            entity_id=None,
            after={"outcome": "accepted"},
            request_id=rid,
        )
    )
    if user:
        db.add(
            OutboxEvent(
                aggregate="users",
                aggregate_id=str(user.id),
                event_type="user.password_reset_requested",
                payload={"user_id": str(user.id)},
            )
        )
    db.commit()
    return {
        "message": "If an account exists and recovery delivery is available, instructions will be sent.",
        "dev_reset_token": reset_token,
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

    if len(new_password) < settings.auth_password_min_length:
        raise HTTPException(status_code=422, detail="Password must be at least 10 characters")
    grant = db.query(PasswordResetGrant).filter(
        PasswordResetGrant.token_hash == hashlib.sha256(token.encode()).hexdigest(),
        PasswordResetGrant.consumed_at.is_(None),
    ).with_for_update().first()
    if not grant or grant.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token")
    uid = payload.get("sub")
    try:
        user = db.get(User, uuid.UUID(uid))
    except Exception:
        user = None

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found or inactive.")

    user.password_hash = hash_password(new_password)
    user.auth_token_version = int(user.auth_token_version or 0) + 1
    grant.consumed_at = datetime.now(timezone.utc)
    revoke_user_sessions(db, user, "password_reset")
    rid = getattr(request.state, "request_id", str(uuid.uuid4()))
    db.add(
        AuditLog(
            actor_id=str(user.id),
            action="auth.password_reset_completed",
            entity="users",
            entity_id=str(user.id),
            after={"outcome": "password_updated"},
            request_id=rid,
        )
    )
    db.commit()
    return {"message": "Password has been successfully updated. You may now log in with your new password."}
