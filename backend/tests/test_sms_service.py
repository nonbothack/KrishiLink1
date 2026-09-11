from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.modules.notifications.sms_service import SMSService, normalize_indian_phone
from app.workers.celery_app import dispatch_deal_confirmation_sms


def test_normalize_indian_phone():
    # Standard 10-digit
    assert normalize_indian_phone("9820019061") == {"national": "9820019061", "e164": "+919820019061"}

    # With +91
    assert normalize_indian_phone("+919820019061") == {"national": "9820019061", "e164": "+919820019061"}

    # With 91 prefix
    assert normalize_indian_phone("919820019061") == {"national": "9820019061", "e164": "+919820019061"}

    # With leading zero
    assert normalize_indian_phone("09820019061") == {"national": "9820019061", "e164": "+919820019061"}

    # With spaces and hyphens
    assert normalize_indian_phone("+91 98200-19061") == {"national": "9820019061", "e164": "+919820019061"}

    # Invalid cases
    assert normalize_indian_phone(None) is None
    assert normalize_indian_phone("") is None
    assert normalize_indian_phone("12345") is None  # Too short
    assert normalize_indian_phone("5123456789") is None  # Indian mobile starts with 6-9
    assert normalize_indian_phone("abcdefghij") is None


def test_sms_service_missing_phone():
    res = SMSService.send_deal_confirmation(
        farmer_phone=None,
        farmer_name="Ramesh",
        crop_name="Onion",
        quantity=50,
        price_per_unit=6200,
        order_id="c726c042",
    )
    assert res["success"] is False
    assert res["status"] == "SKIPPED"


def test_sms_service_demo_mode():
    with patch.object(settings, "sms_enabled", False):
        res = SMSService.send_deal_confirmation(
            farmer_phone="9820019061",
            farmer_name="Ramesh Patil",
            crop_name="Onion",
            quantity=100,
            price_per_unit=6125,
            order_id="c726c042",
        )
        assert res["success"] is True
        assert res["status"] == "DEMO"
        assert res["provider"] == "demo"
        assert "Namaste Ramesh Patil" in res["message"]
        assert "Onion (100 qtl @ Rs 6,125/qtl)" in res["message"]


def test_sms_service_fast2sms_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "return": True,
        "request_id": "req_abc123",
        "message": ["SMS sent successfully."],
    }

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "fast2sms"), \
         patch.object(settings, "fast2sms_api_key", "test_key_xyz"), \
         patch("httpx.Client.post", return_value=mock_resp):

        res = SMSService.send_deal_confirmation(
            farmer_phone="+919820019061",
            farmer_name="Ramesh Patil",
            crop_name="Wheat",
            quantity=25,
            price_per_unit=2530,
            order_id="ord-7788",
        )

        assert res["success"] is True
        assert res["status"] == "SENT"
        assert res["provider"] == "fast2sms"
        assert res["request_id"] == "req_abc123"


def test_sms_service_fast2sms_low_balance():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "return": False,
        "message": "Low Balance",
    }

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "fast2sms"), \
         patch.object(settings, "fast2sms_api_key", "test_key_xyz"), \
         patch("httpx.Client.post", return_value=mock_resp):

        res = SMSService.send_deal_confirmation(
            farmer_phone="9820019061",
            farmer_name="Ramesh Patil",
            crop_name="Wheat",
            quantity=25,
            price_per_unit=2530,
            order_id="ord-7788",
        )

        assert res["success"] is False
        assert res["status"] == "FAILED"
        assert "Low Balance" in res["detail"]


def test_celery_dispatch_deal_confirmation_sms_task():
    payload = {
        "farmer_phone": "9820019061",
        "farmer_name": "Ramesh",
        "crop_name": "Tomato",
        "quantity": 10,
        "price_per_unit": 2450,
        "order_id": "abc12345",
    }
    with patch.object(settings, "sms_enabled", False):
        res = dispatch_deal_confirmation_sms(payload)
        assert res["success"] is True
        assert res["status"] == "DEMO"
