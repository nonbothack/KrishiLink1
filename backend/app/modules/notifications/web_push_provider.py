"""Standards-based Web Push adapter. It intentionally stores no provider errors."""

import importlib.util
import json
import re
from urllib.parse import urlsplit

from app.core.config import settings

_BASE64URL = re.compile(r"^[A-Za-z0-9_-]+={0,2}$")


class PushConfigurationError(RuntimeError):
    pass


class PushDeliveryError(RuntimeError):
    def __init__(self, status_code: int | None):
        self.status_code = status_code
        super().__init__("Web Push delivery failed")


def provider_available() -> bool:
    return importlib.util.find_spec("pywebpush") is not None


def configured() -> bool:
    private_key = settings.web_push_vapid_private_key
    return bool(
        settings.web_push_enabled
        and settings.web_push_vapid_public_key
        and private_key
        and private_key.get_secret_value()
        and settings.web_push_vapid_subject
        and provider_available()
    )


def capability_status() -> tuple[str, str | None]:
    if not settings.web_push_enabled:
        return "DISABLED", None
    if not (settings.web_push_vapid_public_key and settings.web_push_vapid_private_key and settings.web_push_vapid_subject):
        return "UNCONFIGURED", None
    if not provider_available():
        return "DEPENDENCY_UNAVAILABLE", None
    return "AVAILABLE", settings.web_push_vapid_public_key


def validate_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    host = (parsed.hostname or "").lower().rstrip(".")
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Unsupported push endpoint") from None
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
        or not parsed.path
        or host in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ValueError("Unsupported push endpoint")
    allowed = settings.web_push_allowed_hosts_list
    if not any(host == allowed_host or host.endswith("." + allowed_host) for allowed_host in allowed):
        raise ValueError("Unsupported push endpoint")


def _decode_key(value: str, *, expected: int | None = None, uncompressed_point: bool = False) -> bytes:
    import base64

    if not _BASE64URL.fullmatch(value):
        raise ValueError("Invalid push key")
    raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    if expected is not None and len(raw) != expected:
        raise ValueError("Invalid push key")
    if uncompressed_point and (len(raw) != 65 or raw[0] != 4):
        raise ValueError("Invalid push key")
    return raw


def validate_keys(p256dh: str, auth: str) -> None:
    _decode_key(p256dh, uncompressed_point=True)
    _decode_key(auth, expected=16)


def send(subscription: dict, payload: dict) -> int:
    if not configured():
        raise PushConfigurationError("Web Push is not configured")
    from pywebpush import WebPushException, webpush

    try:
        response = webpush(
            subscription_info=subscription,
            data=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
            vapid_private_key=settings.web_push_vapid_private_key.get_secret_value(),
            vapid_claims={"sub": settings.web_push_vapid_subject},
            timeout=10,
        )
        return int(response.status_code)
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        raise PushDeliveryError(getattr(response, "status_code", None)) from None
    except Exception:
        # Do not retain/log exception text: HTTP clients can include the endpoint.
        raise PushDeliveryError(None) from None
