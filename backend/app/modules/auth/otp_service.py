"""Short-lived, hashed OTP challenges for phone login and registration."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import get_redis
from app.models import AuditLog, OtpChallenge, PhoneIdentityConflict, User, VerificationRecord
from app.modules.auth.identity import (
    DevelopmentOtpProvider,
    SmsOtpDeliveryProvider,
    canonicalize_indian_mobile,
    current_policy_versions,
    generate_otp,
    otp_hash,
    phone_hash,
    verify_otp_hash,
)
from app.modules.auth.session_service import create_session_tokens

GENERIC_OTP_MESSAGE = "If this number can receive a KrishiLink code, one will arrive shortly."
GENERIC_OTP_ERROR = "The code is invalid or expired. Request a new code and try again."
_RESERVE_PHONE_OTP_WINDOW = """
local remaining = redis.call('TTL', KEYS[1])
if remaining > 0 then return -remaining end
local count = redis.call('INCR', KEYS[2])
if count == 1 then redis.call('EXPIRE', KEYS[2], 3600) end
if count > 5 then return -1000 end
redis.call('SET', KEYS[1], '1', 'EX', ARGV[1])
return count
"""


def _audit(db: Session, action: str, outcome: str, request_id: str | None = None, challenge_id=None):
    db.add(
        AuditLog(
            actor_id=None,
            action=action,
            entity="otp_challenge",
            entity_id=str(challenge_id) if challenge_id else None,
            after={"outcome": outcome},
            request_id=request_id,
        )
    )


def _provider():
    if settings.env == "development" and settings.otp_development_code_exposure_enabled:
        return DevelopmentOtpProvider(), True
    return SmsOtpDeliveryProvider(), False


def request_otp(db: Session, phone_e164: str, request) -> dict:
    phone_e164, _ = canonicalize_indian_mobile(phone_e164)
    phone_key = phone_hash(phone_e164)
    now = datetime.now(timezone.utc)
    generic = {"message": GENERIC_OTP_MESSAGE, "resend_after_seconds": settings.otp_resend_cooldown_seconds}
    redis = get_redis()
    if settings.env == "production" and redis is None:
        raise HTTPException(503, "Abuse protection is temporarily unavailable")
    if redis is not None:
        try:
            reservation = int(
                redis.eval(
                    _RESERVE_PHONE_OTP_WINDOW,
                    2,
                    f"auth:otp:cooldown:{phone_key}",
                    f"auth:otp:hourly:{phone_key}",
                    settings.otp_resend_cooldown_seconds,
                )
            )
        except RedisError as exc:
            if settings.env == "production":
                raise HTTPException(503, "Abuse protection is temporarily unavailable") from exc
            redis = None
        else:
            if reservation == -1000:
                _audit(db, "auth.otp_request_throttled", "phone_hourly_limit", getattr(request.state, "request_id", None))
                db.commit()
                raise HTTPException(429, GENERIC_OTP_MESSAGE)
            if reservation < 0:
                _audit(db, "auth.otp_request_throttled", "cooldown", getattr(request.state, "request_id", None))
                db.commit()
                return {**generic, "resend_after_seconds": abs(reservation)}

    recent_count = 0
    if redis is None:
        recent_count = db.query(OtpChallenge).filter(
            OtpChallenge.phone_hash == phone_key,
            OtpChallenge.created_at >= now - timedelta(hours=1),
        ).count()
    previous = (
        db.query(OtpChallenge)
        .filter(OtpChallenge.phone_hash == phone_key)
        .order_by(OtpChallenge.created_at.desc())
        .first()
    )
    if previous and previous.created_at:
        previous_created = previous.created_at.replace(tzinfo=timezone.utc) if previous.created_at.tzinfo is None else previous.created_at
        elapsed = (now - previous_created).total_seconds()
        if redis is None and elapsed < settings.otp_resend_cooldown_seconds:
            _audit(db, "auth.otp_request_throttled", "cooldown", getattr(request.state, "request_id", None))
            db.commit()
            return {**generic, "resend_after_seconds": max(1, int(settings.otp_resend_cooldown_seconds - elapsed))}
    if redis is None and recent_count >= 5:
        _audit(db, "auth.otp_request_throttled", "phone_hourly_limit", getattr(request.state, "request_id", None))
        db.commit()
        raise HTTPException(429, GENERIC_OTP_MESSAGE)

    provider, development = _provider()
    if not development and not provider.configured():
        _audit(db, "auth.otp_request_unavailable", "provider_unconfigured", getattr(request.state, "request_id", None))
        db.commit()
        raise HTTPException(503, "Phone code delivery is temporarily unavailable")

    code = generate_otp()
    challenge = OtpChallenge(
        id=uuid.uuid4(),
        phone_hash=phone_key,
        code_hash=otp_hash(phone_e164, code),
        created_at=now,
        expires_at=now + timedelta(seconds=settings.otp_code_ttl_seconds),
        max_attempts=3,
        request_ip_hash=phone_hash("ip:" + str(getattr(getattr(request, "client", None), "host", "unknown"))),
        delivery_provider="development_only" if development else settings.sms_provider.lower(),
    )
    if previous and previous.consumed_at is None and previous.revoked_at is None:
        previous.revoked_at = now
    db.add(challenge)
    db.flush()
    try:
        delivery = provider.send(phone_e164, code)
    except Exception:
        delivery = None
    if not delivery or not delivery.accepted:
        challenge.revoked_at = datetime.now(timezone.utc)
        _audit(db, "auth.otp_request_failed", "delivery_failed", getattr(request.state, "request_id", None), challenge.id)
        db.commit()
        raise HTTPException(503, "Phone code delivery is temporarily unavailable")
    challenge.delivery_provider = delivery.provider
    _audit(db, "auth.otp_requested", "accepted", getattr(request.state, "request_id", None), challenge.id)
    db.commit()
    if development:
        return {**generic, "development_code": code}
    return generic


def verify_otp(db: Session, phone_e164: str, code: str, request) -> dict:
    phone_e164, _ = canonicalize_indian_mobile(phone_e164)
    phone_key = phone_hash(phone_e164)
    now = datetime.now(timezone.utc)
    challenge = (
        db.query(OtpChallenge)
        .filter(
            OtpChallenge.phone_hash == phone_key,
            OtpChallenge.consumed_at.is_(None),
            OtpChallenge.revoked_at.is_(None),
        )
        .order_by(OtpChallenge.created_at.desc())
        .with_for_update()
        .first()
    )
    if not challenge:
        _audit(db, "auth.otp_verify_failed", "invalid_or_missing", getattr(request.state, "request_id", None))
        db.commit()
        raise HTTPException(401, GENERIC_OTP_ERROR)

    expires = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge.expires_at.tzinfo is None else challenge.expires_at
    if expires <= now or challenge.attempt_count >= challenge.max_attempts:
        challenge.revoked_at = now
        _audit(db, "auth.otp_verify_failed", "expired_or_exhausted", getattr(request.state, "request_id", None), challenge.id)
        db.commit()
        raise HTTPException(401, GENERIC_OTP_ERROR)
    if not verify_otp_hash(phone_e164, code, challenge.code_hash):
        challenge.attempt_count += 1
        if challenge.attempt_count >= challenge.max_attempts:
            challenge.revoked_at = now
        _audit(db, "auth.otp_verify_failed", "invalid_code", getattr(request.state, "request_id", None), challenge.id)
        db.commit()
        raise HTTPException(401, GENERIC_OTP_ERROR)

    challenge.consumed_at = now
    conflict = db.get(PhoneIdentityConflict, phone_e164)
    if conflict:
        _audit(db, "auth.otp_verify_failed", "identity_review_required", getattr(request.state, "request_id", None), challenge.id)
        db.commit()
        raise HTTPException(409, "This mobile number needs account review before it can be used")

    user = db.query(User).filter(User.phone_canonical == phone_e164).first()
    if user:
        if not user.is_active:
            _audit(db, "auth.otp_verify_failed", "account_unavailable", getattr(request.state, "request_id", None), challenge.id)
            db.commit()
            raise HTTPException(401, GENERIC_OTP_ERROR)
        user.phone_verified_at = now
        db.add(
            VerificationRecord(
                user_id=user.id,
                dimension="phone",
                status="VERIFIED",
                method="sms_otp",
                provider=challenge.delivery_provider,
                checked_at=now,
                evidence_metadata={"challenge_id": str(challenge.id)},
            )
        )
        _audit(db, "auth.otp_verify_succeeded", "account_login", getattr(request.state, "request_id", None), challenge.id)
        db.commit()
        tokens = create_session_tokens(db, user, request.headers.get("user-agent"))
        return {"account_exists": True, "user": user, **tokens}

    ticket = jwt.encode(
        {
            "sub": phone_e164,
            "phone": phone_e164,
            "provider": challenge.delivery_provider,
            "type": "registration_ticket",
            "jti": str(uuid.uuid4()),
            "exp": now + timedelta(minutes=15),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    _audit(db, "auth.otp_verify_succeeded", "registration_ticket", getattr(request.state, "request_id", None), challenge.id)
    db.commit()
    return {
        "account_exists": False,
        "registration_ticket": ticket,
        "phone": canonicalize_indian_mobile(phone_e164)[1],
        "policy_versions": current_policy_versions(),
    }
