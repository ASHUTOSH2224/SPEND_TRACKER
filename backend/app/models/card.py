import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, JSON, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Card(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cards"
    __table_args__ = (
        Index("ix_cards_user_id_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    nickname: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    network: Mapped[str] = mapped_column(String(32), nullable=False)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    statement_cycle_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annual_fee_expected: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    joining_fee_expected: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    reward_program_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reward_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reward_conversion_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    reward_rule_config_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
