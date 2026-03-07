from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.rules import RuleMatchType

TransactionSortBy = Literal["txn_date", "posted_date", "amount", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]


def _normalize_required_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Value is required")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _normalize_optional_lower_text(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    return normalized.lower()


class TransactionCategorySummary(BaseModel):
    id: UUID
    name: str


class TransactionRead(BaseModel):
    id: UUID
    txn_date: date
    posted_date: date | None = None
    card_id: UUID
    card_name: str
    statement_id: UUID
    raw_description: str
    normalized_merchant: str
    amount: Decimal
    currency: str
    txn_direction: str
    txn_type: str
    category: TransactionCategorySummary | None = None
    category_source: str | None = None
    category_confidence: Decimal | None = None
    category_explanation: str | None = None
    review_required: bool
    duplicate_flag: bool
    is_card_charge: bool
    charge_type: str | None = None
    is_reward_related: bool
    reward_points_delta: Decimal | None = None
    cashback_amount: Decimal | None = None
    source_hash: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListQuery(BaseModel):
    card_id: UUID | None = None
    category_id: UUID | None = None
    statement_id: UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    search: str | None = None
    review_required: bool | None = None
    is_card_charge: bool | None = None
    charge_type: Annotated[str | None, Field(default=None, max_length=64)] = None
    page: Annotated[int, Field(default=1, ge=1)]
    page_size: Annotated[int, Field(default=50, ge=1, le=100)]
    sort_by: TransactionSortBy = "txn_date"
    sort_order: SortOrder = "desc"

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("charge_type", mode="before")
    @classmethod
    def normalize_charge_type(cls, value: str | None) -> str | None:
        return _normalize_optional_lower_text(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "TransactionListQuery":
        if self.from_date is not None and self.to_date is not None and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self


class TransactionUpdate(BaseModel):
    category_id: UUID | None = None
    review_required: bool | None = None
    create_rule: bool = False
    rule_match_type: RuleMatchType | None = None
    rule_match_value: Annotated[str | None, Field(default=None, min_length=1, max_length=512)] = None

    @field_validator("rule_match_type", mode="before")
    @classmethod
    def normalize_rule_match_type(cls, value: str | None) -> str | None:
        return _normalize_optional_lower_text(value)

    @field_validator("rule_match_value", mode="before")
    @classmethod
    def normalize_rule_match_value(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_update(self) -> "TransactionUpdate":
        if not self.create_rule and self.category_id is None and self.review_required is None:
            raise ValueError("At least one update field is required")

        if self.create_rule:
            if self.category_id is None:
                raise ValueError("category_id is required when create_rule=true")
            if self.rule_match_type is None or self.rule_match_value is None:
                raise ValueError(
                    "rule_match_type and rule_match_value are required when create_rule=true"
                )
        elif self.rule_match_type is not None or self.rule_match_value is not None:
            raise ValueError("Rule fields require create_rule=true")

        return self


class TransactionBulkUpdate(BaseModel):
    transaction_ids: Annotated[list[UUID], Field(min_length=1)]
    category_id: UUID | None = None
    review_required: bool | None = None

    @field_validator("transaction_ids")
    @classmethod
    def deduplicate_transaction_ids(cls, value: list[UUID]) -> list[UUID]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_update(self) -> "TransactionBulkUpdate":
        if self.category_id is None and self.review_required is None:
            raise ValueError("At least one update field is required")
        return self


class TransactionBulkUpdateResult(BaseModel):
    updated_count: int
    audit_count: int
