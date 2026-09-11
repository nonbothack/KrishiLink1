from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.modules.notifications.sms_service import SMSService, normalize_indian_phone
from app.workers.celery_app import dispatch_deal_confirmation_sms, dispatch_offer_received_sms


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


def test_sms_service_send_raw_sms():
    # Demo mode test
    with patch.object(settings, "sms_enabled", False):
        res = SMSService.send_raw_sms("9820019061", "Live test from KrishiLink")
        assert res["success"] is True
        assert res["status"] == "DEMO"
        assert res["phone"] == "+919820019061"

    # Invalid phone test
    res = SMSService.send_raw_sms("123", "Invalid number")
    assert res["success"] is False
    assert res["status"] == "SKIPPED"

    # Fast2SMS mock test
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"return": True, "request_id": "req_raw_999"}

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "fast2sms"), \
         patch.object(settings, "fast2sms_api_key", "valid_api_key"), \
         patch("httpx.Client.post", return_value=mock_resp):
        res = SMSService.send_raw_sms("+919820019061", "Quick SMS Test")
        assert res["success"] is True
        assert res["status"] == "SENT"
        assert res["request_id"] == "req_raw_999"

    # Twilio mock test
    mock_twilio_resp = MagicMock()
    mock_twilio_resp.status_code = 201
    mock_twilio_resp.json.return_value = {"sid": "SM_test_sid_123", "status": "queued"}

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "twilio"), \
         patch.object(settings, "twilio_account_sid", "AC_test_123"), \
         patch.object(settings, "twilio_auth_token", "auth_tok_456"), \
         patch.object(settings, "twilio_from_number", "+17372508034"), \
         patch("httpx.Client.post", return_value=mock_twilio_resp):
        res = SMSService.send_raw_sms("+919820019061", "Twilio Live Test")
        assert res["success"] is True
        assert res["status"] == "SENT"
        assert res["provider"] == "twilio"
        assert res["request_id"] == "SM_test_sid_123"

    # Twilio missing credentials
    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "twilio"), \
         patch.object(settings, "twilio_account_sid", None):
        res = SMSService.send_raw_sms("+919820019061", "Twilio Fail Test")
        assert res["success"] is False
        assert res["status"] == "FAILED"


def test_notifications_test_sms_endpoint(client):
    login_resp = client.post("/api/v1/auth/login", json={"email": "ramesh@demo.com", "password": "demo123!"})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with patch.object(settings, "sms_enabled", False):
        resp = client.post(
            "/api/v1/notifications/test-sms",
            json={"phone": "9820019061", "message": "KrishiLink SIH demo test"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "DEMO"
        assert body["data"]["provider"] == "demo"


def test_sms_service_send_offer_received_sms():
    # Demo mode
    with patch.object(settings, "sms_enabled", False):
        res = SMSService.send_offer_received_sms(
            farmer_phone="9820019061",
            farmer_name="Ramesh Patil",
            crop_name="Onion",
            quantity=50,
            price_per_unit=5800,
        )
        assert res["success"] is True
        assert res["status"] == "DEMO"
        assert "Namaste Ramesh Patil" in res["message"]
        assert "50 qtl @ Rs 5,800/qtl" in res["message"]

    # Missing phone
    res_skip = SMSService.send_offer_received_sms(
        farmer_phone=None,
        farmer_name="Ramesh",
        crop_name="Onion",
        quantity=50,
        price_per_unit=5800,
    )
    assert res_skip["success"] is False
    assert res_skip["status"] == "SKIPPED"


def test_celery_dispatch_offer_received_sms_task():
    payload = {
        "farmer_phone": "9820019061",
        "farmer_name": "Ramesh",
        "crop_name": "Soybean",
        "quantity": 30,
        "price_per_unit": 4200,
    }
    with patch.object(settings, "sms_enabled", False):
        res = dispatch_offer_received_sms(payload)
        assert res["success"] is True
        assert res["status"] == "DEMO"


def test_sms_service_send_buyer_deal_confirmation():
    with patch.object(settings, "sms_enabled", False):
        res = SMSService.send_buyer_deal_confirmation(
            buyer_phone="9876543210",
            buyer_name="Mehta Traders",
            crop_name="Organic Wheat",
            quantity=50.0,
            price_per_unit=2450.0,
            order_id="TEST01",
        )
        assert res["success"] is True
        assert res["status"] == "DEMO"
        assert "Mehta Traders" in res["message"]
        assert "TEST01" in res["message"]
