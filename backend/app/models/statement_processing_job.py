import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StatementProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "statement_processing_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_statement_processing_jobs_status_allowed",
        ),
        CheckConstraint(
            "trigger_source IN ('create', 'retry')",
            name="ck_statement_processing_jobs_trigger_source_allowed",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_statement_processing_jobs_attempt_count_non_negative",
        ),
        Index(
            "ix_statement_processing_jobs_status_created_at",
            "status",
            "created_at",
        ),
        Index(
            "ix_statement_processing_jobs_statement_id_created_at",
            "statement_id",
            "created_at",
        ),
    )

    statement_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("statements.id"),
        nullable=False,
    )
    trigger_source: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="queued",
        server_default="queued",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
