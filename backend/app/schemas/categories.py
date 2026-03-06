from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoryGroupName = Literal["spend", "charges", "rewards"]


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


class CategoryRead(BaseModel):
    id: UUID
    name: str
    slug: str
    group_name: CategoryGroupName
    is_default: bool
    is_archived: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    group_name: CategoryGroupName

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _normalize_required_text(value)

    @field_validator("group_name", mode="before")
    @classmethod
    def normalize_group_name(cls, value: str) -> str:
        return _normalize_lower_text(value)


class CategoryUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)]
    is_archived: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)
