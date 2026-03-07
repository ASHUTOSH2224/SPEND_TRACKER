import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class TransactionCategoryAudit(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transaction_category_audit"
    __table_args__ = (
        CheckConstraint(
            "changed_by IN ('user', 'system')",
            name="ck_transaction_category_audit_changed_by_allowed",
        ),
        Index(
            "ix_transaction_category_audit_transaction_id_created_at",
            "transaction_id",
            "created_at",
        ),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("transactions.id"),
        nullable=False,
    )
    old_category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("categories.id"),
        nullable=True,
    )
    new_category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("categories.id"),
        nullable=False,
    )
    changed_by: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
