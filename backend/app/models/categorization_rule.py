import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Uuid, true
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CategorizationRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categorization_rules"
    __table_args__ = (
        CheckConstraint(
            "match_type IN ('description_contains', 'merchant_equals', 'regex')",
            name="match_type_allowed",
        ),
        Index(
            "ix_categorization_rules_user_id_is_active_priority",
            "user_id",
            "is_active",
            "priority",
        ),
        Index(
            "ix_categorization_rules_assigned_category_id",
            "assigned_category_id",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    match_type: Mapped[str] = mapped_column(String(64), nullable=False)
    match_value: Mapped[str] = mapped_column(String(512), nullable=False)
    assigned_category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("categories.id"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default="100",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    created_from_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
    )
