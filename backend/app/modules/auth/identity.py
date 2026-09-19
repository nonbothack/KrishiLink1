"""Identity primitives shared by authentication and messaging adapters."""

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings

_MOBILE_RE = re.compile(r"[6-9][0-9]{9}\Z")
_SEPARATORS_RE = re.compile(r"[\s().-]")


def canonicalize_indian_mobile(value: str) -> tuple[str, str]:
    """Return (E.164, national) for supported Indian mobile forms only."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Enter a valid Indian mobile number")
    cleaned = _SEPARATORS_RE.sub("", value.strip())
    had_plus = cleaned.startswith("+")
    if had_plus:
        cleaned = cleaned[1:]
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    elif had_plus and not cleaned.startswith("91"):
        raise ValueError("Only Indian mobile numbers are supported")
    if not _MOBILE_RE.fullmatch(cleaned):
        raise ValueError("Enter a valid Indian mobile number")
    return f"+91{cleaned}", cleaned


def phone_hash(phone_e164: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), phone_e164.encode(), hashlib.sha256).hexdigest()


def otp_hash(phone_e164: str, code: str) -> str:
    material = f"otp:{phone_e164}:{code}".encode()
    return hmac.new(settings.jwt_secret.encode(), material, hashlib.sha256).hexdigest()


def verify_otp_hash(phone_e164: str, code: str, expected_hash: str) -> bool:
    return hmac.compare_digest(otp_hash(phone_e164, code), expected_hash)


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


@dataclass(frozen=True)
class OtpDeliveryResult:
    accepted: bool
    provider: str | None


class OtpDeliveryProvider(Protocol):
    def send(self, phone_e164: str, code: str) -> OtpDeliveryResult: ...


class DevelopmentOtpProvider:
    """Non-production provider selected only by the development-only route gate."""

    def send(self, phone_e164: str, code: str) -> OtpDeliveryResult:
        del phone_e164, code
        return OtpDeliveryResult(accepted=True, provider="development_only")


class SmsOtpDeliveryProvider:
    """Thin adapter over the existing SMS gateway; never selects its demo mode."""

    @staticmethod
    def configured() -> bool:
        if not settings.sms_enabled:
            return False
        provider = settings.sms_provider.lower()
        return bool(
            (provider == "fast2sms" and settings.fast2sms_api_key)
            or (
                provider == "twilio"
                and settings.twilio_account_sid
                and settings.twilio_auth_token
                and settings.twilio_from_number
            )
            or (provider == "smsgate" and settings.smsgate_base_url)
        )

    def send(self, phone_e164: str, code: str) -> OtpDeliveryResult:
        if not self.configured():
            return OtpDeliveryResult(accepted=False, provider=None)
        # Configured adapters take the non-demo path in SMSService. Do not log
        # the body, provider response body, or code in this adapter.
        from app.modules.notifications.sms_service import SMSService

        result = SMSService.send_raw_sms(
            phone=phone_e164,
            message=(
                f"Your KrishiLink code is {code}. It expires in "
                f"{settings.otp_code_ttl_seconds} seconds. Do not share it."
            ),
        )
        if result.get("success") and result.get("status") == "SENT":
            return OtpDeliveryResult(accepted=True, provider=str(result.get("provider") or settings.sms_provider))
        return OtpDeliveryResult(accepted=False, provider=str(result.get("provider") or settings.sms_provider))


CURRENT_POLICIES = {
    "terms": {
        "version": "terms-2026-09-17-draft.1",
        "effective_date": None,
        "draft_date": "2026-09-17",
        "status": "DRAFT_PENDING_LEGAL_REVIEW",
    },
    "privacy_notice": {
        "version": "privacy-2026-09-17-draft.1",
        "effective_date": None,
        "draft_date": "2026-09-17",
        "status": "DRAFT_PENDING_LEGAL_REVIEW",
    },
    "marketing": {
        "version": "marketing-2026-09-17.1",
        "effective_date": "2026-09-17",
        "status": "ACTIVE_OPTIONAL",
    },
}


def current_policy_versions() -> dict[str, dict[str, str]]:
    return {key: dict(value) for key, value in CURRENT_POLICIES.items()}
