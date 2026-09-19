from decimal import Decimal
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="KrishiLink API")
    app_version: str = Field(default="2.0.0")
    env: str = Field(default="development")
    debug: bool = Field(default=True)
    demo_mode: bool = Field(default=True)

    api_v1_prefix: str = Field(default="/api/v1")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    frontend_url: str = Field(default="http://localhost:3000")
    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8000,http://localhost:8001,https://krishi-link1.vercel.app,https://krishilink.vercel.app"
    )

    database_url: str = Field(default="postgresql+psycopg://krishilink:krishilink@localhost:5432/krishilink")
    database_url_sync: str | None = Field(default=None)

    redis_url: str = Field(default="redis://localhost:6379/0")
    lot_price_deviation_warning_pct: Decimal = Field(default=Decimal("50"), ge=0, le=1000)
    # Intelligence features are independently kill-switchable. Forecasts remain
    # disabled until a governed model passes the deployment gates in Packet 11.
    intelligence_forecasts_enabled: bool = Field(default=False)
    intelligence_price_alerts_enabled: bool = Field(default=True)
    intelligence_trust_summaries_enabled: bool = Field(default=True)
    intelligence_descriptive_move_threshold_pct: Decimal = Field(default=Decimal("1.5"), ge=0, le=100)

    # Web Push is explicitly opt-in and remains unavailable until an operator
    # configures production VAPID credentials. The private key is never returned.
    web_push_enabled: bool = False
    web_push_vapid_public_key: str | None = Field(default=None, repr=False)
    web_push_vapid_private_key: SecretStr | None = Field(default=None, repr=False)
    web_push_vapid_subject: str | None = None
    web_push_allowed_hosts: str = "fcm.googleapis.com,updates.push.services.mozilla.com,web.push.apple.com"
    web_push_max_attempts: int = Field(default=4, ge=1, le=8)

    jwt_secret: str = Field(default="dev-only-change-in-production-32chars!!")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_ttl_min: int = Field(default=15)
    jwt_refresh_ttl_days: int = Field(default=7)
    otp_code_ttl_seconds: int = Field(default=300, ge=60, le=900)
    otp_resend_cooldown_seconds: int = Field(default=30, ge=15, le=300)
    otp_development_code_exposure_enabled: bool = Field(default=False)
    auth_password_min_length: int = Field(default=10, ge=10, le=72)

    s3_endpoint: str | None = Field(default=None)
    s3_bucket: str | None = Field(default=None)
    s3_access_key: str | None = Field(default=None)
    s3_secret_key: str | None = Field(default=None)

    payment_provider: str = Field(default="mock")

    sms_enabled: bool = Field(default=False)
    sms_provider: str = Field(default="fast2sms")
    sms_default_country_code: str = Field(default="+91")
    fast2sms_api_key: str | None = Field(default=None)
    msg91_auth_key: str | None = Field(default=None)
    msg91_flow_id: str | None = Field(default=None)
    twilio_account_sid: str | None = Field(default=None)
    twilio_auth_token: str | None = Field(default=None)
    twilio_from_number: str | None = Field(default=None)

    smsgate_base_url: str | None = Field(default=None)
    smsgate_username: str | None = Field(default=None)
    smsgate_password: str | None = Field(default=None)
    smsgate_device_id: str | None = Field(default=None)
    smsgate_sim_number: int = Field(default=1)
    smsgate_timeout_seconds: int = Field(default=15)

    mandi_api_key: SecretStr | None = Field(default=None, repr=False)
    agmarknet_api_key: SecretStr | None = Field(default=None, repr=False)
    mandi_api_url: str = Field(default="https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070")

    @field_validator("mandi_api_key", "agmarknet_api_key", mode="before")
    @classmethod
    def blank_provider_keys_are_unset(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value

    log_level: str = Field(default="INFO")
    trusted_proxies: str = Field(default="127.0.0.1,::1,localhost")

    @field_validator("cors_origins")
    @classmethod
    def validate_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_proxies_list(self) -> list[str]:
        return [p.strip() for p in self.trusted_proxies.split(",") if p.strip()]

    @property
    def web_push_allowed_hosts_list(self) -> list[str]:
        return [host.strip().lower() for host in self.web_push_allowed_hosts.split(",") if host.strip()]

    @property
    def database_url_effective(self) -> str:
        return self.database_url_sync or self.database_url

    def validate_prod(self) -> None:
        if self.env == "production":
            assert self.jwt_secret != "dev-only-change-in-production-32chars!!", "JWT_SECRET must be set in production"
            assert "sqlite" not in self.database_url_effective.lower(), "SQLite is not permitted in production"
            assert self.database_url_effective.startswith(("postgresql://", "postgresql+psycopg://")), "DATABASE_URL must be PostgreSQL in production"
            assert "localhost" not in self.database_url_effective and "127.0.0.1" not in self.database_url_effective, "DATABASE_URL must not be loopback in production"
            assert not self.debug, "DEBUG must be disabled in production"
            assert not self.demo_mode, "DEMO_MODE must be disabled in production"
            assert not self.otp_development_code_exposure_enabled, "OTP development disclosure must be disabled in production"
            assert self.redis_url and "localhost" not in self.redis_url and "127.0.0.1" not in self.redis_url, "REDIS_URL must point to a managed/non-loopback service in production"
            assert self.cors_origins_list and "*" not in self.cors_origins_list, "Wildcard CORS is not permitted in production"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    return s


settings = get_settings()
