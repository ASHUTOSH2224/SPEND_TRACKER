import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RewardLedger(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reward_ledgers"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('earned', 'redeemed', 'expired', 'adjusted', 'cashback')",
            name="ck_reward_ledgers_event_type_allowed",
        ),
        CheckConstraint(
            "source IN ('manual', 'extracted', 'estimated')",
            name="ck_reward_ledgers_source_allowed",
        ),
        Index("ix_reward_ledgers_user_id_card_id_event_date", "user_id", "card_id", "event_date"),
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
    statement_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("statements.id"),
        nullable=True,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reward_points: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    reward_value_estimate: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
