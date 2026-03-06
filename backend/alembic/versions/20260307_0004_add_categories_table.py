"""Add categories table and seed default categories.

Revision ID: 20260307_0004
Revises: 20260307_0003
Create Date: 2026-03-07 02:15:00.000000
"""

from collections.abc import Sequence
import uuid

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0004"
down_revision: str | None = "20260307_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DEFAULT_CATEGORIES: tuple[dict[str, object], ...] = (
    {
        "id": uuid.UUID("9bb14591-cb35-4849-b8c9-1c6adcc2f7cf"),
        "name": "Food & Dining",
        "slug": "food-dining",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("c9561522-d509-49c7-a82c-a31a0344df30"),
        "name": "Groceries",
        "slug": "groceries",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("3ff5b00d-c50a-4685-af89-84c7181d0cc8"),
        "name": "Travel",
        "slug": "travel",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("8e461550-654d-4aab-80b0-bda4f1b0d149"),
        "name": "Shopping",
        "slug": "shopping",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("40d35e16-aa17-4a4c-8a80-a3472357138a"),
        "name": "Utilities",
        "slug": "utilities",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("bd089f1f-4c70-42ed-91c0-3ce6a56888cf"),
        "name": "Subscriptions",
        "slug": "subscriptions",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("93534d6d-9946-458a-b34e-35d6df558f8e"),
        "name": "Fuel",
        "slug": "fuel",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("7a11dc15-e822-4f16-abdc-f0920bd80a14"),
        "name": "Miscellaneous",
        "slug": "miscellaneous",
        "group_name": "spend",
    },
    {
        "id": uuid.UUID("0be3b85a-b064-40f9-ae09-b70ba5e7f0f3"),
        "name": "Annual Fee",
        "slug": "annual-fee",
        "group_name": "charges",
    },
    {
        "id": uuid.UUID("cfb4adf8-2d1d-4240-814c-80b341d2acfd"),
        "name": "Joining Fee",
        "slug": "joining-fee",
        "group_name": "charges",
    },
    {
        "id": uuid.UUID("bb198bd7-8ee7-4d7f-b313-3b1504a6af43"),
        "name": "Late Fee",
        "slug": "late-fee",
        "group_name": "charges",
    },
    {
        "id": uuid.UUID("ec6ab5f6-e0d2-4dd5-b37e-6c09481ec1f2"),
        "name": "Finance Charge",
        "slug": "finance-charge",
        "group_name": "charges",
    },
    {
        "id": uuid.UUID("0efd18d1-ae6d-49e4-9992-f41d0b91d20d"),
        "name": "Reward Points",
        "slug": "reward-points",
        "group_name": "rewards",
    },
    {
        "id": uuid.UUID("ec390ba4-e6f1-431b-a4fa-76bed149252e"),
        "name": "Cashback",
        "slug": "cashback",
        "group_name": "rewards",
    },
)


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("group_name", sa.String(length=32), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "group_name IN ('spend', 'charges', 'rewards')",
            name="ck_categories_group_name_allowed",
        ),
        sa.CheckConstraint(
            "(user_id IS NULL AND is_default = TRUE) OR "
            "(user_id IS NOT NULL AND is_default = FALSE)",
            name="ck_categories_default_scope_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_categories_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_index(
        "ix_categories_user_id_group_name_is_archived",
        "categories",
        ["user_id", "group_name", "is_archived"],
        unique=False,
    )
    op.create_index(
        "ix_categories_is_default_group_name",
        "categories",
        ["is_default", "group_name"],
        unique=False,
    )

    categories_table = sa.table(
        "categories",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("name", sa.String(length=255)),
        sa.column("slug", sa.String(length=255)),
        sa.column("group_name", sa.String(length=32)),
        sa.column("is_default", sa.Boolean()),
        sa.column("is_archived", sa.Boolean()),
    )
    op.bulk_insert(
        categories_table,
        [
            {
                **category,
                "user_id": None,
                "is_default": True,
                "is_archived": False,
            }
            for category in DEFAULT_CATEGORIES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_categories_is_default_group_name", table_name="categories")
    op.drop_index("ix_categories_user_id_group_name_is_archived", table_name="categories")
    op.drop_table("categories")
