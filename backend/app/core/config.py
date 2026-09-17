from functools import lru_cache

from pydantic import Field, field_validator
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

    jwt_secret: str = Field(default="dev-only-change-in-production-32chars!!")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_ttl_min: int = Field(default=15)
    jwt_refresh_ttl_days: int = Field(default=7)

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

    mandi_api_key: str | None = Field(default=None)
    agmarknet_api_key: str | None = Field(default=None)
    mandi_api_url: str = Field(default="https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070")

    log_level: str = Field(default="INFO")

    @field_validator("cors_origins")
    @classmethod
    def validate_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url_effective(self) -> str:
        return self.database_url_sync or self.database_url

    def validate_prod(self) -> None:
        if self.env == "production":
            assert self.jwt_secret != "dev-only-change-in-production-32chars!!", "JWT_SECRET must be set in production"
            assert "localhost" not in self.database_url, "DATABASE_URL must not be localhost in production"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    return s


settings = get_settings()
