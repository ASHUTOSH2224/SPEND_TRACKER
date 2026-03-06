import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "group_name IN ('spend', 'charges', 'rewards')",
            name="group_name_allowed",
        ),
        CheckConstraint(
            "(user_id IS NULL AND is_default = TRUE) OR "
            "(user_id IS NOT NULL AND is_default = FALSE)",
            name="default_scope_consistency",
        ),
        Index(
            "ix_categories_user_id_group_name_is_archived",
            "user_id",
            "group_name",
            "is_archived",
        ),
        Index(
            "ix_categories_is_default_group_name",
            "is_default",
            "group_name",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name: Mapped[str] = mapped_column(String(32), nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
