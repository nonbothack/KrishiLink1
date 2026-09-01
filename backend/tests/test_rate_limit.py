import pytest
from unittest.mock import Mock, patch
from app.core.rate_limit import get_redis, rate_limit
import app.core.rate_limit as rl_module

@patch("app.core.rate_limit.Redis")
def test_get_redis(mock_redis_class):
    mock_client = Mock()
    mock_redis_class.return_value = mock_client
    
    orig = rl_module.redis_client
    try:
        rl_module.redis_client = None
        client = get_redis()
        assert client is mock_client
        mock_redis_class.assert_called_once()
    finally:
        rl_module.redis_client = orig

@patch("app.core.rate_limit.get_redis")
def test_rate_limit_decorator(mock_get_redis):
    mock_redis = Mock()
    mock_pipe = Mock()
    mock_redis.pipeline.return_value = mock_pipe
    mock_pipe.execute.return_value = [None, None, 5, None]  # 5 requests
    mock_get_redis.return_value = mock_redis
    
    @rate_limit(max_requests=10, window_seconds=60)
    async def dummy_endpoint(request):
        return {"ok": True}
    
    request = Mock()
    request.client.host = "127.0.0.1"
    request.url.path = "/test"
    
    import asyncio
    result = asyncio.run(dummy_endpoint(request))
    assert result == {"ok": True}

@patch("app.core.rate_limit.get_redis")
def test_rate_limit_exceeded(mock_get_redis):
    mock_redis = Mock()
    mock_pipe = Mock()
    mock_redis.pipeline.return_value = mock_pipe
    mock_pipe.execute.return_value = [None, None, 15, None]  # 15 requests > limit 10
    mock_get_redis.return_value = mock_redis
    
    @rate_limit(max_requests=10, window_seconds=60)
    async def dummy_endpoint(request):
        return {"ok": True}
    
    request = Mock()
    import asyncio
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dummy_endpoint(request))
    assert exc.value.status_code == 429


def test_trusted_proxy_ip_extraction():
    from app.core.rate_limit import _get_client_ip

    # Trusted proxy scenario (127.0.0.1 is in default trusted proxies)
    req_trusted = Mock()
    req_trusted.client.host = "127.0.0.1"
    req_trusted.headers = {"x-forwarded-for": "203.0.113.195, 10.0.0.1"}
    assert _get_client_ip(req_trusted) == "203.0.113.195"

    # Untrusted direct client attempting to spoof X-Forwarded-For
    req_untrusted = Mock()
    req_untrusted.client.host = "198.51.100.42"
    req_untrusted.headers = {"x-forwarded-for": "10.0.0.99"}
    # Must ignore spoofed header and return direct IP
    assert _get_client_ip(req_untrusted) == "198.51.100.42"