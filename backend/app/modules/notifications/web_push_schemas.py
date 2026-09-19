from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=80, max_length=200)
    auth: str = Field(min_length=16, max_length=100)


class PushSubscriptionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(min_length=20, max_length=2048)
    keys: PushKeys
    language: Literal["en", "hi", "mr"] = "en"

    @field_validator("endpoint")
    @classmethod
    def trim_endpoint(cls, value: str) -> str:
        return value.strip()


class PushEndpointInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(min_length=20, max_length=2048)

    @field_validator("endpoint")
    @classmethod
    def trim_endpoint(cls, value: str) -> str:
        return value.strip()
