import uuid
from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Statement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statements"
    __table_args__ = (
        CheckConstraint(
            "file_type IN ('pdf', 'csv', 'xls', 'xlsx')",
            name="ck_statements_file_type_allowed",
        ),
        CheckConstraint(
            "upload_status IN ('uploaded', 'processing', 'completed', 'failed')",
            name="ck_statements_upload_status_allowed",
        ),
        CheckConstraint(
            "extraction_status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_statements_extraction_status_allowed",
        ),
        CheckConstraint(
            "categorization_status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_statements_categorization_status_allowed",
        ),
        CheckConstraint(
            "statement_period_end >= statement_period_start",
            name="ck_statements_period_range_valid",
        ),
        CheckConstraint(
            "transaction_count >= 0",
            name="ck_statements_transaction_count_non_negative",
        ),
        Index("ix_statements_user_id_card_id", "user_id", "card_id"),
        Index(
            "ix_statements_statement_period_start_statement_period_end",
            "statement_period_start",
            "statement_period_end",
        ),
        Index(
            "ix_statements_upload_status_extraction_status",
            "upload_status",
            "extraction_status",
        ),
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
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    statement_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    statement_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    upload_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
    )
    extraction_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    categorization_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    transaction_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
