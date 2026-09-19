from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


def _production(**overrides):
    values = {
        "env": "production",
        "jwt_secret": "a" * 48,
        "database_url": "postgresql+psycopg://user:pass@db.internal:5432/krishilink",
        "database_url_sync": None,
        "redis_url": "redis://redis.internal:6379/0",
        "debug": False,
        "demo_mode": False,
        "otp_development_code_exposure_enabled": False,
        "cors_origins": "https://app.example.test",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_settings_reject_sqlite_and_insecure_defaults():
    for field, value in (
        ("database_url", "sqlite:///tmp/app.db"),
        ("redis_url", "redis://localhost:6379/0"),
        ("debug", True),
        ("demo_mode", True),
        ("otp_development_code_exposure_enabled", True),
        ("cors_origins", "*"),
    ):
        settings = _production(**{field: value})
        try:
            settings.validate_prod()
        except AssertionError:
            continue
        raise AssertionError(f"production validation accepted unsafe {field}")


def test_production_settings_accept_only_explicit_safe_profile():
    _production().validate_prod()


def test_readiness_is_distinct_and_fails_closed_when_redis_is_unavailable():
    response = TestClient(app).get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert "ready" in body["data"]
    assert "checks" in body["data"]
    if body["data"]["checks"]["redis"] == "DOWN":
        assert response.status_code == 503
