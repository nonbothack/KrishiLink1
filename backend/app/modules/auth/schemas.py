import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.modules.auth.identity import canonicalize_indian_mobile


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    password: str | None = Field(default=None, min_length=10, max_length=72)
    role: str = Field(default="farmer")
    business_name: str | None = Field(default=None, min_length=2, max_length=160)
    organization_name: str | None = Field(default=None, min_length=2, max_length=160)
    procurement_categories: list[str] = Field(default_factory=list, max_length=20)
    primary_crops: list[str] = Field(default_factory=list, max_length=20)
    verification_ticket: str | None = Field(default=None, max_length=4096)
    policy_versions: dict[str, str] = Field(default_factory=dict)
    marketing_consent: bool = False
    location: str | None = Field(default=None, max_length=200)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    state_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    subdistrict_id: uuid.UUID | None = None
    location_consent: bool = False
    latitude: float | None = Field(default=None, ge=6.0, le=37.5)
    longitude: float | None = Field(default=None, ge=68.0, le=98.0)
    coordinate_accuracy_m: float | None = Field(default=None, gt=0, le=100_000)

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) and value.strip() else None

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None or value == "":
            return None
        return canonicalize_indian_mobile(value)[1]

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role = value.strip().lower()
        if role not in {"farmer", "buyer", "fpo"}:
            raise ValueError("role must be farmer, buyer, or fpo")
        return role

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 10:
            raise ValueError("password must be at least 10 characters")
        return value

    @field_validator("procurement_categories", "primary_crops")
    @classmethod
    def clean_categories(cls, values: list[str]) -> list[str]:
        return [value.strip()[:80] for value in values if value.strip()][:20]

    @model_validator(mode="after")
    def validate_location_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        if self.coordinate_accuracy_m is not None and self.latitude is None:
            raise ValueError("coordinate accuracy requires GPS coordinates")
        if self.latitude is not None and not self.location_consent:
            raise ValueError("explicit location consent is required when sharing GPS coordinates")
        return self


class OtpRequest(BaseModel):
    phone: str = Field(min_length=1, max_length=40)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return canonicalize_indian_mobile(value)[0]


class OtpVerify(BaseModel):
    phone: str = Field(min_length=1, max_length=40)
    code: str = Field(pattern=r"^[0-9]{6}$")

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return canonicalize_indian_mobile(value)[0]


class LoginRequest(BaseModel):
    # Kept as `email` in the JSON contract for compatibility; accepts a phone too.
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=72)


class LocationUpdateRequest(BaseModel):
    latitude: float = Field(ge=6.0, le=37.5)
    longitude: float = Field(ge=68.0, le=98.0)
    accuracy_m: float | None = Field(default=None, gt=0, le=100_000)
    consent: bool

    @field_validator("consent")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("location consent is required")
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str | None
    phone: str | None
    full_name: str
    role: str
    location: str | None
    district: str | None
    state: str | None
    phone_verified_at: datetime | None = None
    email_verified_at: datetime | None = None
    is_active: bool
