from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.transactions import SortOrder, TransactionSortBy


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


class AnalyticsFilterQuery(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    card_id: UUID | None = None
    category_id: UUID | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "AnalyticsFilterQuery":
        if self.from_date is not None and self.to_date is not None and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self


class SummaryFilterQuery(AnalyticsFilterQuery):
    @model_validator(mode="after")
    def validate_summary_period(self) -> "SummaryFilterQuery":
        if (self.from_date is None) != (self.to_date is None):
            raise ValueError("from_date and to_date must be provided together")
        return self


class CardAnalyticsFilterQuery(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    category_id: UUID | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "CardAnalyticsFilterQuery":
        if self.from_date is not None and self.to_date is not None and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self


class CardSummaryQuery(CardAnalyticsFilterQuery):
    @model_validator(mode="after")
    def validate_summary_period(self) -> "CardSummaryQuery":
        if (self.from_date is None) != (self.to_date is None):
            raise ValueError("from_date and to_date must be provided together")
        return self


class DashboardSummaryCategoryRead(BaseModel):
    category_id: UUID | None = None
    name: str
    amount: Decimal


class DashboardSummaryCardRead(BaseModel):
    card_id: UUID
    name: str
    amount: Decimal


class DashboardSummaryRead(BaseModel):
    total_spend: Decimal
    previous_period_spend: Decimal
    spend_change_pct: Decimal
    total_rewards_value: Decimal
    total_charges: Decimal
    net_card_value: Decimal
    transaction_count: int
    needs_review_count: int
    top_category: DashboardSummaryCategoryRead | None = None
    top_card: DashboardSummaryCardRead | None = None


class SpendByCategoryRead(BaseModel):
    category_id: UUID | None = None
    category_name: str
    amount: Decimal
    transaction_count: int


class SpendByCardRead(BaseModel):
    card_id: UUID
    card_name: str
    amount: Decimal
    transaction_count: int


class RewardVsChargesRead(BaseModel):
    card_id: UUID
    card_name: str
    total_spend: Decimal
    reward_value: Decimal
    charges: Decimal
    net_value: Decimal


class MonthlyTrendRead(BaseModel):
    month: date
    total_spend: Decimal
    reward_value: Decimal
    charges: Decimal
    net_value: Decimal


class TopMerchantRead(BaseModel):
    merchant_name: str
    amount: Decimal
    transaction_count: int


class CardSummaryCardRead(BaseModel):
    id: UUID
    nickname: str
    last4: str
    issuer_name: str


class CardSummaryRead(BaseModel):
    card: CardSummaryCardRead
    total_spend: Decimal
    eligible_spend: Decimal
    reward_points: Decimal
    reward_value: Decimal
    charges: Decimal
    annual_fee: Decimal
    joining_fee: Decimal
    other_charges: Decimal
    net_value: Decimal


class CardTransactionListQuery(BaseModel):
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
    def validate_date_range(self) -> "CardTransactionListQuery":
        if self.from_date is not None and self.to_date is not None and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self
