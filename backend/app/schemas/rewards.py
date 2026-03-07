from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RewardEventType = Literal["earned", "redeemed", "expired", "adjusted", "cashback"]
RewardLedgerSource = Literal["manual", "extracted", "estimated"]


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


class RewardLedgerRead(BaseModel):
    id: UUID
    card_id: UUID
    statement_id: UUID | None = None
    event_date: date
    event_type: RewardEventType
    reward_points: Decimal | None = None
    reward_value_estimate: Decimal | None = None
    source: RewardLedgerSource
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RewardLedgerCreate(BaseModel):
    card_id: UUID
    statement_id: UUID | None = None
    event_date: date
    event_type: RewardEventType
    reward_points: Annotated[
        Decimal | None,
        Field(default=None, max_digits=12, decimal_places=2),
    ] = None
    reward_value_estimate: Annotated[
        Decimal | None,
        Field(default=None, max_digits=12, decimal_places=2),
    ] = None
    source: RewardLedgerSource = "manual"
    notes: Annotated[str | None, Field(default=None, max_length=2000)] = None

    @field_validator("event_type", "source", mode="before")
    @classmethod
    def normalize_lower_enums(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_amounts(self) -> "RewardLedgerCreate":
        if self.reward_points is None and self.reward_value_estimate is None:
            raise ValueError("At least one of reward_points or reward_value_estimate is required")
        return self


class RewardLedgerUpdate(BaseModel):
    statement_id: UUID | None = None
    event_date: date | None = None
    event_type: RewardEventType | None = None
    reward_points: Annotated[
        Decimal | None,
        Field(default=None, max_digits=12, decimal_places=2),
    ] = None
    reward_value_estimate: Annotated[
        Decimal | None,
        Field(default=None, max_digits=12, decimal_places=2),
    ] = None
    source: RewardLedgerSource | None = None
    notes: Annotated[str | None, Field(default=None, max_length=2000)] = None

    @field_validator("event_type", "source", mode="before")
    @classmethod
    def normalize_optional_lower_enums(cls, value: str | None) -> str | None:
        return _normalize_optional_lower_text(value)

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_update(self) -> "RewardLedgerUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one update field is required")
        return self


class RewardLedgerListQuery(BaseModel):
    card_id: UUID | None = None
    event_type: RewardEventType | None = None
    from_date: date | None = None
    to_date: date | None = None

    @field_validator("event_type", mode="before")
    @classmethod
    def normalize_event_type(cls, value: str | None) -> str | None:
        return _normalize_optional_lower_text(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "RewardLedgerListQuery":
        if self.from_date is not None and self.to_date is not None and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self


class CardRewardSummaryRead(BaseModel):
    card_id: UUID
    reward_type: str
    total_points_earned: Decimal
    total_points_redeemed: Decimal
    total_points_expired: Decimal
    estimated_reward_value: Decimal
    current_balance: Decimal


class CardChargeSummaryRead(BaseModel):
    card_id: UUID
    source: str
    summary_period_count: int
    annual_fee_amount: Decimal
    joining_fee_amount: Decimal
    late_fee_amount: Decimal
    finance_charge_amount: Decimal
    emi_processing_fee_amount: Decimal
    cash_advance_fee_amount: Decimal
    forex_markup_amount: Decimal
    tax_amount: Decimal
    other_charge_amount: Decimal
    total_charge_amount: Decimal
