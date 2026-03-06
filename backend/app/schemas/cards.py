from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CardStatus = Literal["active", "archived"]
RewardType = Literal["points", "cashback", "miles"]


def _normalize_required_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Value is required")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    return _normalize_required_text(value)


def _normalize_lower_text(value: str) -> str:
    return _normalize_required_text(value).lower()


def _normalize_optional_lower_text(value: str | None) -> str | None:
    if value is None:
        return None
    return _normalize_lower_text(value)


def _normalize_last4(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if len(normalized) != 4 or not normalized.isdigit():
        raise ValueError("last4 must be exactly 4 digits")
    return normalized


class CardRead(BaseModel):
    id: UUID
    nickname: str
    issuer_name: str
    network: str
    last4: str
    statement_cycle_day: int | None = None
    annual_fee_expected: Decimal | None = None
    joining_fee_expected: Decimal | None = None
    reward_program_name: str | None = None
    reward_type: RewardType
    reward_conversion_rate: Decimal | None = None
    reward_rule_config_json: dict[str, Any] | None = None
    status: CardStatus

    model_config = ConfigDict(from_attributes=True)


class CardCreate(BaseModel):
    nickname: Annotated[str, Field(min_length=1, max_length=255)]
    issuer_name: Annotated[str, Field(min_length=1, max_length=255)]
    network: Annotated[str, Field(min_length=1, max_length=32)]
    last4: Annotated[str, Field(min_length=4, max_length=4)]
    statement_cycle_day: Annotated[int | None, Field(default=None, ge=1, le=31)]
    annual_fee_expected: Annotated[
        Decimal | None,
        Field(default=None, ge=0, max_digits=12, decimal_places=2),
    ]
    joining_fee_expected: Annotated[
        Decimal | None,
        Field(default=None, ge=0, max_digits=12, decimal_places=2),
    ]
    reward_program_name: Annotated[str | None, Field(default=None, max_length=255)]
    reward_type: RewardType
    reward_conversion_rate: Annotated[
        Decimal | None,
        Field(default=None, ge=0, max_digits=12, decimal_places=4),
    ]
    reward_rule_config_json: dict[str, Any] | None = None

    @field_validator("nickname", "issuer_name", mode="before")
    @classmethod
    def normalize_required_text_fields(cls, value: str) -> str:
        return _normalize_required_text(value)

    @field_validator("network", "reward_type", mode="before")
    @classmethod
    def normalize_lower_text_fields(cls, value: str) -> str:
        return _normalize_lower_text(value)

    @field_validator("reward_program_name", mode="before")
    @classmethod
    def normalize_optional_text_field(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("last4", mode="before")
    @classmethod
    def validate_last4(cls, value: str) -> str:
        normalized = _normalize_last4(value)
        if normalized is None:
            raise ValueError("last4 must be exactly 4 digits")
        return normalized


class CardUpdate(BaseModel):
    nickname: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    issuer_name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    network: Annotated[str | None, Field(default=None, min_length=1, max_length=32)]
    last4: Annotated[str | None, Field(default=None, min_length=4, max_length=4)]
    statement_cycle_day: Annotated[int | None, Field(default=None, ge=1, le=31)]
    annual_fee_expected: Annotated[
        Decimal | None,
        Field(default=None, ge=0, max_digits=12, decimal_places=2),
    ]
    joining_fee_expected: Annotated[
        Decimal | None,
        Field(default=None, ge=0, max_digits=12, decimal_places=2),
    ]
    reward_program_name: Annotated[str | None, Field(default=None, max_length=255)]
    reward_type: RewardType | None = None
    reward_conversion_rate: Annotated[
        Decimal | None,
        Field(default=None, ge=0, max_digits=12, decimal_places=4),
    ]
    reward_rule_config_json: dict[str, Any] | None = None

    @field_validator("nickname", "issuer_name", mode="before")
    @classmethod
    def normalize_optional_required_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("network", "reward_type", mode="before")
    @classmethod
    def normalize_optional_lower_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_lower_text(value)

    @field_validator("reward_program_name", mode="before")
    @classmethod
    def normalize_optional_text_field(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("last4", mode="before")
    @classmethod
    def validate_last4(cls, value: str | None) -> str | None:
        return _normalize_last4(value)
