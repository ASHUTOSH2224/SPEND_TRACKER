import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, JSON, Numeric, String, Text, Uuid, false
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "txn_direction IN ('debit', 'credit')",
            name="ck_transactions_txn_direction_allowed",
        ),
        CheckConstraint(
            "txn_type IN ('spend', 'refund', 'charge', 'reward', 'manual_adjustment')",
            name="ck_transactions_txn_type_allowed",
        ),
        CheckConstraint(
            "category_source IS NULL OR category_source IN ('rule', 'history', 'llm', 'manual')",
            name="ck_transactions_category_source_allowed",
        ),
        CheckConstraint(
            "category_confidence IS NULL OR "
            "(category_confidence >= 0 AND category_confidence <= 1)",
            name="ck_transactions_category_confidence_range",
        ),
        CheckConstraint(
            "amount >= 0",
            name="ck_transactions_amount_non_negative",
        ),
        Index("ix_transactions_user_id_txn_date", "user_id", "txn_date"),
        Index("ix_transactions_user_id_card_id_txn_date", "user_id", "card_id", "txn_date"),
        Index(
            "ix_transactions_user_id_category_id_txn_date",
            "user_id",
            "category_id",
            "txn_date",
        ),
        Index("ix_transactions_statement_id", "statement_id"),
        Index("ix_transactions_user_id_source_hash", "user_id", "source_hash"),
        Index("ix_transactions_review_required", "review_required"),
        Index("ix_transactions_is_card_charge_charge_type", "is_card_charge", "charge_type"),
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
    statement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("statements.id"),
        nullable=False,
    )
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    posted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_merchant: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
        server_default="INR",
    )
    txn_direction: Mapped[str] = mapped_column(String(16), nullable=False)
    txn_type: Mapped[str] = mapped_column(String(32), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("categories.id"),
        nullable=True,
    )
    category_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    category_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    duplicate_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    is_card_charge: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    charge_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_reward_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    reward_points_delta: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    cashback_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    source_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )
