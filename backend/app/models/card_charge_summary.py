import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CardChargeSummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "card_charge_summaries"
    __table_args__ = (
        CheckConstraint("annual_fee_amount >= 0", name="ck_card_charge_summaries_annual_fee_non_negative"),
        CheckConstraint("joining_fee_amount >= 0", name="ck_card_charge_summaries_joining_fee_non_negative"),
        CheckConstraint("late_fee_amount >= 0", name="ck_card_charge_summaries_late_fee_non_negative"),
        CheckConstraint("finance_charge_amount >= 0", name="ck_card_charge_summaries_finance_charge_non_negative"),
        CheckConstraint(
            "emi_processing_fee_amount >= 0",
            name="ck_card_charge_summaries_emi_processing_fee_non_negative",
        ),
        CheckConstraint(
            "cash_advance_fee_amount >= 0",
            name="ck_card_charge_summaries_cash_advance_fee_non_negative",
        ),
        CheckConstraint("forex_markup_amount >= 0", name="ck_card_charge_summaries_forex_markup_non_negative"),
        CheckConstraint("tax_amount >= 0", name="ck_card_charge_summaries_tax_non_negative"),
        CheckConstraint("other_charge_amount >= 0", name="ck_card_charge_summaries_other_charge_non_negative"),
        CheckConstraint("total_charge_amount >= 0", name="ck_card_charge_summaries_total_non_negative"),
        Index("ix_card_charge_summaries_user_id_card_id_period_month", "user_id", "card_id", "period_month", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("cards.id"),
        nullable=False,
    )
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    annual_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    joining_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    late_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    finance_charge_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    emi_processing_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    cash_advance_fee_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    forex_markup_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    other_charge_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    total_charge_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
