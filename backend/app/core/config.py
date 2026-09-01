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
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8000,http://localhost:8001")

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
