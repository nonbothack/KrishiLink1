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
        assert res["success"] is False
        assert res["status"] == "DEMO"
        assert res["provider"] == "demo"
        assert "no carrier" in res["detail"]
        assert "phone" not in res
        assert "message" not in res


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
        assert res["success"] is False
        assert res["status"] == "DEMO"


def test_sms_service_send_raw_sms():
    # Demo mode test
    with patch.object(settings, "sms_enabled", False):
        res = SMSService.send_raw_sms("9820019061", "Live test from KrishiLink")
        assert res["success"] is False
        assert res["status"] == "DEMO"
        assert "phone" not in res
        assert "message" not in res

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
        assert resp.status_code == 403


def test_notifications_have_no_remote_offer_trade_or_account_action_routes():
    from app.main import app

    notification_paths = [route.path.lower() for route in app.routes if "/notifications" in route.path.lower()]
    assert notification_paths
    assert not any(
        any(action in path for action in ("inbound", "whatsapp", "voice", "/action", "/accept", "/counter", "/payment"))
        for path in notification_paths
    )


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
        assert res["success"] is False
        assert res["status"] == "DEMO"
        assert "no carrier" in res["detail"]

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
        assert res["success"] is False
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
        assert res["success"] is False
        assert res["status"] == "DEMO"
        assert "no carrier" in res["detail"]


def test_sms_service_smsgate_cloud_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "gate_msg_101", "status": "Pending"}

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "smsgate"), \
         patch.object(settings, "smsgate_base_url", "https://api.sms-gate.app"), \
         patch.object(settings, "smsgate_username", "admin"), \
         patch.object(settings, "smsgate_password", "secret"), \
         patch.object(settings, "smsgate_device_id", "phone_abc123"), \
         patch.object(settings, "smsgate_sim_number", 1), \
         patch("httpx.Client.post", return_value=mock_resp) as mock_post:

        res = SMSService.send_deal_confirmation(
            farmer_phone="+919820019061",
            farmer_name="Ramesh Patil",
            crop_name="Wheat",
            quantity=25,
            price_per_unit=2530,
            order_id="ord-9988",
        )

        assert res["success"] is True
        assert res["status"] == "SENT"
        assert res["provider"] == "smsgate"
        assert res["request_id"] == "gate_msg_101"

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.sms-gate.app/3rdparty/v1/messages"
        assert kwargs["params"] == {"skipPhoneValidation": "true"}
        assert kwargs["json"]["phoneNumbers"] == ["+919820019061"]
        assert kwargs["json"]["deviceId"] == "phone_abc123"
        assert kwargs["json"]["simNumber"] == 1
        assert "Namaste Ramesh Patil" in kwargs["json"]["textMessage"]["text"]


def test_sms_service_smsgate_local_server_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "local_msg_202"}

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "smsgate"), \
         patch.object(settings, "smsgate_base_url", "http://192.168.1.50:8080"), \
         patch.object(settings, "smsgate_username", "smsuser"), \
         patch.object(settings, "smsgate_password", "smspass"), \
         patch.object(settings, "smsgate_device_id", None), \
         patch("httpx.Client.post", return_value=mock_resp) as mock_post:

        res = SMSService.send_raw_sms(
            phone="9820019061",
            message="Direct LAN SMS via Android Gateway",
        )

        assert res["success"] is True
        assert res["status"] == "SENT"
        assert res["provider"] == "smsgate"
        assert res["request_id"] == "local_msg_202"

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://192.168.1.50:8080/message"
        assert kwargs["params"] is None
        assert kwargs["json"]["phoneNumbers"] == ["+919820019061"]
        assert "deviceId" not in kwargs["json"]
        assert kwargs["json"]["textMessage"]["text"] == "Direct LAN SMS via Android Gateway"


def test_sms_service_smsgate_missing_base_url():
    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "smsgate"), \
         patch.object(settings, "smsgate_base_url", None):

        res = SMSService.send_deal_confirmation(
            farmer_phone="9820019061",
            farmer_name="Ramesh Patil",
            crop_name="Wheat",
            quantity=10,
            price_per_unit=2500,
            order_id="ord-fail-1",
        )
        assert res["success"] is False
        assert res["status"] == "FAILED"
        assert "SMSGATE_BASE_URL is missing" in res["detail"]


def test_sms_service_smsgate_bearer_auth():
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = [{"id": "array_id_77"}]

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "smsgate"), \
         patch.object(settings, "smsgate_base_url", "https://custom-gateway.local/message"), \
         patch.object(settings, "smsgate_username", None), \
         patch.object(settings, "smsgate_password", "bearer-token-xyz"), \
         patch.object(settings, "smsgate_device_id", None), \
         patch("httpx.Client.post", return_value=mock_resp) as mock_post:

        res = SMSService.send_raw_sms("+919820019061", "Test Bearer Auth")
        assert res["success"] is True
        assert res["status"] == "SENT"
        assert res["request_id"] == "array_id_77"

        args, kwargs = mock_post.call_args
        assert args[0] == "https://custom-gateway.local/message"
        assert kwargs["headers"]["Authorization"] == "Bearer bearer-token-xyz"


def test_sms_service_smsgate_timeout():
    import httpx

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "smsgate"), \
         patch.object(settings, "smsgate_base_url", "http://192.168.1.100:8080"), \
         patch("httpx.Client.post", side_effect=httpx.TimeoutException("Connection timed out")):

        res = SMSService.send_deal_confirmation(
            farmer_phone="9820019061",
            farmer_name="Ramesh Patil",
            crop_name="Wheat",
            quantity=10,
            price_per_unit=2500,
            order_id="ord-timeout",
        )
        assert res["success"] is False
        assert res["status"] == "FAILED"
        assert "timeout" in res["detail"].lower()


def test_sms_service_smsgate_http_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.json.return_value = {"message": "Device queue limit exceeded"}

    with patch.object(settings, "sms_enabled", True), \
         patch.object(settings, "sms_provider", "smsgate"), \
         patch.object(settings, "smsgate_base_url", "https://api.sms-gate.app"), \
         patch("httpx.Client.post", return_value=mock_resp):

        res = SMSService.send_deal_confirmation(
            farmer_phone="9820019061",
            farmer_name="Ramesh Patil",
            crop_name="Wheat",
            quantity=10,
            price_per_unit=2500,
            order_id="ord-503",
        )
        assert res["success"] is False
        assert res["status"] == "FAILED"
        assert res["status_code"] == 503
        assert "Device queue limit exceeded" in res["detail"]


def test_notifications_test_sms_endpoint_with_smsgate(client, admin_auth_headers):

    smsgate_result = {
        "success": True,
        "status": "SENT",
        "provider": "smsgate",
        "request_id": "gate_test_endpoint_1",
        "detail": "SMS accepted by Android SMS Gateway",
    }

    with patch("app.modules.notifications.router.SMSService.send_raw_sms", return_value=smsgate_result):
        resp = client.post(
            "/api/v1/notifications/test-sms",
            json={"phone": "9820019061", "message": "KrishiLink live gateway test"},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "SENT"
        assert body["data"]["provider"] == "smsgate"
        assert body["data"]["request_id"] == "gate_test_endpoint_1"

