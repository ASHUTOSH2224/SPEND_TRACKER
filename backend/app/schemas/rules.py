from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

RuleMatchType = Literal["description_contains", "merchant_equals", "regex"]


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


class RuleRead(BaseModel):
    id: UUID
    rule_name: str
    match_type: RuleMatchType
    match_value: str
    assigned_category_id: UUID
    priority: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RuleCreate(BaseModel):
    rule_name: Annotated[str, Field(min_length=1, max_length=255)]
    match_type: RuleMatchType
    match_value: Annotated[str, Field(min_length=1, max_length=512)]
    assigned_category_id: UUID
    priority: int = 100
    is_active: bool = True

    @field_validator("rule_name", "match_value", mode="before")
    @classmethod
    def normalize_required_text_fields(cls, value: str) -> str:
        return _normalize_required_text(value)

    @field_validator("match_type", mode="before")
    @classmethod
    def normalize_match_type(cls, value: str) -> str:
        return _normalize_lower_text(value)


class RuleUpdate(BaseModel):
    rule_name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    match_type: RuleMatchType | None = None
    match_value: Annotated[str | None, Field(default=None, min_length=1, max_length=512)]
    assigned_category_id: UUID | None = None
    priority: int | None = None
    is_active: bool | None = None

    @field_validator("rule_name", "match_value", mode="before")
    @classmethod
    def normalize_optional_text_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("match_type", mode="before")
    @classmethod
    def normalize_optional_match_type(cls, value: str | None) -> str | None:
        return _normalize_optional_lower_text(value)
