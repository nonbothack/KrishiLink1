import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^[0-9]{10}$")
    password: str = Field(min_length=6, max_length=72)
    role: str = Field(default="farmer")
    location: str | None = None
    district: str | None = None
    state: str | None = "Maharashtra"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.lower()
        if v not in ("farmer", "buyer", "fpo", "admin", "operator"):
            raise ValueError("role must be farmer, buyer, or fpo")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str | None = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=72)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("new password must be at least 6 characters")
        return v

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
    is_verified: bool
    is_active: bool
