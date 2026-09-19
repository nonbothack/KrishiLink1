import logging
from typing import Any

import httpx

from app.core.config import settings
from app.modules.auth.identity import canonicalize_indian_mobile

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
    try:
        e164, national = canonicalize_indian_mobile(str(phone))
    except ValueError:
        return None
    return {"national": national, "e164": e164}


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
            logger.info("SMS skipped: missing or invalid recipient phone number")
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
            logger.info("SMS delivery simulated in demo mode; no carrier request was made")
            return {
                "success": False,
                "status": "DEMO",
                "provider": "demo",
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

        # 4. Twilio Provider
        if provider == "twilio":
            return cls._send_twilio(
                phone_e164=phone_info["e164"],
                message=message_text,
            )

        # 5. SMSGate Provider (Android SIM Gateway)
        if provider == "smsgate":
            return cls._send_smsgate(
                phone_e164=phone_info["e164"],
                message=message_text,
            )

        logger.warning("Unknown SMS provider '%s'; skipping delivery", provider)
        return {
            "success": False,
            "status": "FAILED",
            "detail": f"Unknown provider configured: {provider}",
        }

    @classmethod
    def send_offer_received_sms(
        cls,
        farmer_phone: str | None,
        farmer_name: str | None,
        crop_name: str,
        quantity: float | int,
        price_per_unit: float | int,
    ) -> dict[str, Any]:
        """
        Send SMS to the farmer when a buyer places a new purchase offer on their produce.
        """
        name_display = farmer_name.strip() if farmer_name else "Farmer"
        message_text = (
            f"Namaste {name_display}, you received a new offer on KrishiLink for {crop_name}: "
            f"{quantity} qtl @ Rs {price_per_unit:,.0f}/qtl. Please open KrishiLink app to review & accept."
        )
        return cls.send_raw_sms(phone=farmer_phone, message=message_text)

    @classmethod
    def send_buyer_deal_confirmation(
        cls,
        buyer_phone: str | None,
        buyer_name: str | None,
        crop_name: str,
        quantity: float | int,
        price_per_unit: float | int,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Send SMS to the buyer when their offer is accepted by the farmer.
        """
        name_display = buyer_name.strip() if buyer_name else "Buyer"
        message_text = (
            f"Namaste {name_display}, your offer for {crop_name} ({quantity} qtl @ Rs {price_per_unit:,.0f}/qtl) "
            f"has been accepted on KrishiLink! Order #{order_id}. Please open KrishiLink app to complete transaction."
        )
        return cls.send_raw_sms(phone=buyer_phone, message=message_text)

    @classmethod
    def send_raw_sms(cls, phone: str | None, message: str) -> dict[str, Any]:
        """
        Send an arbitrary SMS message directly to an Indian phone number.
        """
        phone_info = normalize_indian_phone(phone)
        if not phone_info:
            logger.info("SMS skipped: missing or invalid recipient phone number")
            return {
                "success": False,
                "status": "SKIPPED",
                "detail": f"Missing or invalid Indian phone number: {phone}",
            }

        if not settings.sms_enabled or settings.sms_provider.lower() in ("demo", "mock"):
            logger.info("SMS delivery simulated in demo mode; no carrier request was made")
            return {
                "success": False,
                "status": "DEMO",
                "provider": "demo",
                "detail": "SMS simulated in demo mode (no carrier charges)",
            }

        provider = settings.sms_provider.lower()
        if provider == "fast2sms":
            return cls._send_fast2sms(
                phone_10_digit=phone_info["national"],
                message=message,
            )

        if provider == "twilio":
            return cls._send_twilio(
                phone_e164=phone_info["e164"],
                message=message,
            )

        if provider == "smsgate":
            return cls._send_smsgate(
                phone_e164=phone_info["e164"],
                message=message,
            )

        return {
            "success": False,
            "status": "FAILED",
            "provider": provider,
            "detail": f"Direct custom message not supported for provider: {provider}",
        }

    @classmethod
    def _send_twilio(cls, phone_e164: str, message: str) -> dict[str, Any]:
        """
        Dispatches SMS via Twilio Messages API.
        Docs: https://www.twilio.com/docs/sms/api/message-resource
        """
        account_sid = settings.twilio_account_sid
        auth_token = settings.twilio_auth_token
        from_number = settings.twilio_from_number

        if not account_sid or not auth_token or not from_number:
            logger.error("Twilio requested but TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_FROM_NUMBER is missing")
            return {
                "success": False,
                "status": "FAILED",
                "detail": "Twilio credentials missing",
            }

        endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid.strip()}/Messages.json"
        auth = (account_sid.strip(), auth_token.strip())
        data = {
            "To": phone_e164,
            "From": from_number.strip(),
            "Body": message,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(endpoint, data=data, auth=auth)
                status_code = res.status_code
                try:
                    resp_json = res.json()
                except Exception:
                    resp_json = {"raw": res.text}

                if status_code in (200, 201):
                    sid = resp_json.get("sid", "")
                    logger.info("Twilio SMS sent to %s (sid=%s)", phone_e164, sid)
                    return {
                        "success": True,
                        "status": "SENT",
                        "provider": "twilio",
                        "request_id": sid,
                        "detail": f"Twilio SMS accepted (status: {resp_json.get('status')})",
                    }
                else:
                    msg = resp_json.get("message", "Twilio rejected request")
                    code = resp_json.get("code", status_code)
                    logger.warning("Twilio delivery failed (HTTP %s, code %s): %s", status_code, code, msg)
                    return {
                        "success": False,
                        "status": "FAILED",
                        "provider": "twilio",
                        "status_code": status_code,
                        "detail": f"Twilio error {code}: {msg}",
                    }
        except httpx.TimeoutException:
            logger.error("Twilio timeout communicating with endpoint")
            return {
                "success": False,
                "status": "FAILED",
                "provider": "twilio",
                "detail": "Twilio gateway timeout",
            }
        except Exception as exc:
            logger.exception("Twilio unexpected error: %s", exc)
            return {
                "success": False,
                "status": "FAILED",
                "provider": "twilio",
                "detail": str(exc),
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

    @classmethod
    def _send_smsgate(cls, phone_e164: str, message: str) -> dict[str, Any]:
        """
        Dispatches SMS via Android SMS Gateway (SMSGate).
        Supports both Local Server (on LAN/tunnel) and Cloud Server modes.
        Docs: https://docs.sms-gate.app/features/sending-messages/
              https://docs.sms-gate.app/getting-started/local-server/
        """
        base_url = settings.smsgate_base_url
        if not base_url:
            logger.error("SMSGate requested but SMSGATE_BASE_URL is not configured")
            return {
                "success": False,
                "status": "FAILED",
                "provider": "smsgate",
                "detail": "SMSGATE_BASE_URL is missing",
            }

        clean_base = base_url.strip().rstrip("/")
        if not clean_base.startswith("http://") and not clean_base.startswith("https://"):
            clean_base = f"http://{clean_base}"

        # Determine target endpoint
        if clean_base.endswith("/message") or clean_base.endswith("/messages"):
            endpoint = clean_base
        elif "api.sms-gate.app" in clean_base:
            endpoint = f"{clean_base}/3rdparty/v1/messages"
        else:
            endpoint = f"{clean_base}/message"

        payload: dict[str, Any] = {
            "textMessage": {
                "text": message,
            },
            "phoneNumbers": [phone_e164],
            "simNumber": settings.smsgate_sim_number,
        }
        if settings.smsgate_device_id:
            payload["deviceId"] = settings.smsgate_device_id

        # Authentication
        auth = None
        headers = {
            "Content-Type": "application/json",
        }
        if settings.smsgate_username and settings.smsgate_password:
            auth = httpx.BasicAuth(settings.smsgate_username.strip(), settings.smsgate_password.strip())
        elif settings.smsgate_password and not settings.smsgate_username:
            headers["Authorization"] = f"Bearer {settings.smsgate_password.strip()}"
        elif settings.smsgate_username and not settings.smsgate_password:
            auth = httpx.BasicAuth(settings.smsgate_username.strip(), "")

        params = {"skipPhoneValidation": "true"} if ("3rdparty" in endpoint or "api.sms-gate.app" in endpoint) else None
        timeout = float(settings.smsgate_timeout_seconds)

        try:
            with httpx.Client(timeout=timeout) as client:
                res = client.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    params=params,
                )
                status_code = res.status_code
                try:
                    resp_json = res.json()
                except Exception:
                    resp_json = {"raw": res.text}

                if status_code in (200, 201, 202):
                    msg_id = ""
                    if isinstance(resp_json, dict):
                        msg_id = resp_json.get("id") or resp_json.get("messageId") or ""
                    elif isinstance(resp_json, list) and len(resp_json) > 0 and isinstance(resp_json[0], dict):
                        msg_id = resp_json[0].get("id") or resp_json[0].get("messageId") or ""

                    logger.info("SMSGate SMS accepted for %s (id=%s)", phone_e164, msg_id)
                    return {
                        "success": True,
                        "status": "SENT",
                        "provider": "smsgate",
                        "request_id": str(msg_id) if msg_id else "",
                        "detail": "SMS accepted by Android SMS Gateway",
                    }
                else:
                    err_msg = ""
                    if isinstance(resp_json, dict):
                        err_msg = resp_json.get("message") or resp_json.get("error") or res.text
                    else:
                        err_msg = res.text
                    logger.warning(
                        "SMSGate delivery failed (HTTP %s): %s",
                        status_code,
                        err_msg,
                    )
                    return {
                        "success": False,
                        "status": "FAILED",
                        "provider": "smsgate",
                        "status_code": status_code,
                        "detail": f"SMSGate error {status_code}: {err_msg}",
                    }
        except httpx.TimeoutException:
            logger.error("SMSGate timeout communicating with endpoint %s", endpoint)
            return {
                "success": False,
                "status": "FAILED",
                "provider": "smsgate",
                "detail": f"SMSGate gateway timeout ({timeout}s)",
            }
        except Exception as exc:
            logger.exception("SMSGate unexpected error: %s", exc)
            return {
                "success": False,
                "status": "FAILED",
                "provider": "smsgate",
                "detail": str(exc),
            }
