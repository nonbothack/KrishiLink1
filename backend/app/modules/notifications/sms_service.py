import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def normalize_indian_phone(phone: str | None) -> dict[str, str] | None:
    """
    Normalizes diverse Indian phone number formats into standardized forms:
      - national: 10-digit number (e.g. '9820019061') for Fast2SMS
      - e164: +91 with 10 digits (e.g. '+919820019061') for international gateways
    Returns None if input is empty, malformed, or not a valid 10-digit mobile number.
    """
    if not phone:
        return None

    # Strip whitespace, hyphens, brackets, dots
    cleaned = re.sub(r"[\s\-\(\)\.]+", "", str(phone).strip())

    # Strip leading +
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # If starts with 91 and has 12 digits, strip country code
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    # If starts with 0 and has 11 digits, strip leading trunk zero
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]

    # Valid Indian mobile numbers are exactly 10 digits starting with 6, 7, 8, or 9
    if re.fullmatch(r"[6-9]\d{9}", cleaned):
        return {
            "national": cleaned,
            "e164": f"+91{cleaned}",
        }

    return None


class SMSService:
    """
    Unified SMS delivery service for KrishiLink.
    Supports Fast2SMS (Quick SMS without DLT), MSG91 Flow API, and Demo Mode.
    Ensures that business transactions commit independently of SMS delivery.
    """

    @classmethod
    def send_deal_confirmation(
        cls,
        farmer_phone: str | None,
        farmer_name: str | None,
        crop_name: str,
        quantity: float | int,
        price_per_unit: float | int,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Send deal confirmation SMS to the farmer when a buyer confirms an order.
        """
        phone_info = normalize_indian_phone(farmer_phone)
        if not phone_info:
            logger.info("SMS skipped: missing or invalid phone number '%s' for farmer '%s'", farmer_phone, farmer_name)
            return {
                "success": False,
                "status": "SKIPPED",
                "detail": f"Missing or invalid phone number: {farmer_phone}",
            }

        name_display = farmer_name.strip() if farmer_name else "Farmer"
        message_text = (
            f"Namaste {name_display}, your deal for {crop_name} ({quantity} qtl @ Rs {price_per_unit:,.0f}/qtl) "
            f"has been confirmed on KrishiLink. Order #{order_id}. Please check app for dispatch details."
        )

        # 1. Demo Mode (Zero cost, local testing, or when disabled)
        if not settings.sms_enabled or settings.sms_provider.lower() in ("demo", "mock"):
            logger.info(
                "[SMS DEMO MODE] TO: %s (%s) | MSG: %s",
                phone_info["e164"],
                name_display,
                message_text,
            )
            return {
                "success": True,
                "status": "DEMO",
                "provider": "demo",
                "phone": phone_info["e164"],
                "message": message_text,
                "detail": "SMS simulated in demo mode (no carrier charges)",
            }

        provider = settings.sms_provider.lower()

        # 2. Fast2SMS Provider (Instant Indian SMS, no DLT required for Quick SMS)
        if provider == "fast2sms":
            return cls._send_fast2sms(
                phone_10_digit=phone_info["national"],
                message=message_text,
            )

        # 3. MSG91 Flow API Provider
        if provider == "msg91":
            return cls._send_msg91(
                phone_e164=phone_info["e164"],
                farmer_name=name_display,
                crop_name=crop_name,
                quantity=quantity,
                price_per_unit=price_per_unit,
                order_id=order_id,
            )

        logger.warning("Unknown SMS provider '%s'; skipping delivery", provider)
        return {
            "success": False,
            "status": "FAILED",
            "detail": f"Unknown provider configured: {provider}",
        }

    @classmethod
    def _send_fast2sms(cls, phone_10_digit: str, message: str) -> dict[str, Any]:
        """
        Dispatches SMS via Fast2SMS Quick SMS route (route=q).
        Docs: https://www.fast2sms.com/dev/bulkV2
        """
        api_key = settings.fast2sms_api_key
        if not api_key:
            logger.error("Fast2SMS requested but FAST2SMS_API_KEY is not configured")
            return {
                "success": False,
                "status": "FAILED",
                "detail": "FAST2SMS_API_KEY is missing",
            }

        endpoint = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": api_key.strip(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "route": "q",
            "message": message,
            "language": "english",
            "numbers": phone_10_digit,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(endpoint, data=data, headers=headers)
                status_code = res.status_code
                try:
                    resp_json = res.json()
                except Exception:
                    resp_json = {"raw": res.text}

                # Fast2SMS returns {"return": true, ...} on success
                if status_code == 200 and resp_json.get("return") is True:
                    req_id = resp_json.get("request_id", "")
                    logger.info("Fast2SMS delivered to %s (request_id=%s)", phone_10_digit, req_id)
                    return {
                        "success": True,
                        "status": "SENT",
                        "provider": "fast2sms",
                        "request_id": req_id,
                        "detail": "SMS accepted by Fast2SMS carrier route",
                    }
                else:
                    msg = resp_json.get("message", "Fast2SMS rejected request")
                    if isinstance(msg, list):
                        msg = ", ".join(str(m) for m in msg)
                    logger.warning("Fast2SMS delivery failed (HTTP %s): %s", status_code, msg)
                    return {
                        "success": False,
                        "status": "FAILED",
                        "provider": "fast2sms",
                        "status_code": status_code,
                        "detail": str(msg),
                    }
        except httpx.TimeoutException:
            logger.error("Fast2SMS timeout communicating with endpoint")
            return {
                "success": False,
                "status": "FAILED",
                "provider": "fast2sms",
                "detail": "Fast2SMS gateway timeout",
            }
        except Exception as exc:
            logger.exception("Fast2SMS unexpected error: %s", exc)
            return {
                "success": False,
                "status": "FAILED",
                "provider": "fast2sms",
                "detail": str(exc),
            }

    @classmethod
    def _send_msg91(
        cls,
        phone_e164: str,
        farmer_name: str,
        crop_name: str,
        quantity: float | int,
        price_per_unit: float | int,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Dispatches SMS via MSG91 Flow API.
        Docs: https://docs.msg91.com/p/flow/
        """
        auth_key = settings.msg91_auth_key
        flow_id = settings.msg91_flow_id
        if not auth_key or not flow_id:
            logger.error("MSG91 requested but MSG91_AUTH_KEY or MSG91_FLOW_ID is not configured")
            return {
                "success": False,
                "status": "FAILED",
                "detail": "MSG91 credentials missing",
            }

        endpoint = "https://api.msg91.com/api/v5/flow/"
        headers = {
            "authkey": auth_key.strip(),
            "Content-Type": "application/json",
        }
        # MSG91 expects phone without +
        clean_mob = phone_e164.lstrip("+")
        payload = {
            "flow_id": flow_id.strip(),
            "recipients": [
                {
                    "mobiles": clean_mob,
                    "name": farmer_name,
                    "crop": crop_name,
                    "quantity": str(quantity),
                    "price": f"{price_per_unit:,.0f}",
                    "order_id": order_id,
                }
            ],
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                if res.status_code in (200, 202):
                    return {
                        "success": True,
                        "status": "SENT",
                        "provider": "msg91",
                        "detail": "Accepted by MSG91 Flow",
                    }
                return {
                    "success": False,
                    "status": "FAILED",
                    "provider": "msg91",
                    "status_code": res.status_code,
                    "detail": res.text,
                }
        except Exception as exc:
            logger.exception("MSG91 call failed: %s", exc)
            return {
                "success": False,
                "status": "FAILED",
                "provider": "msg91",
                "detail": str(exc),
            }
