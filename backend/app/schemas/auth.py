from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("Email is required")
    return normalized


def _normalize_full_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Full name is required")
    return normalized


class UserRead(BaseModel):
    id: UUID
    email: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class SignupRequest(BaseModel):
    email: Annotated[str, Field(pattern=EMAIL_PATTERN, max_length=320)]
    password: Annotated[str, Field(min_length=8, max_length=256)]
    full_name: Annotated[str, Field(min_length=1, max_length=255)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        return _normalize_full_name(value)


class LoginRequest(BaseModel):
    email: Annotated[str, Field(pattern=EMAIL_PATTERN, max_length=320)]
    password: Annotated[str, Field(min_length=1, max_length=256)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class AuthResponse(BaseModel):
    user: UserRead
    token: str
