"""Add categorization rules table.

Revision ID: 20260307_0005
Revises: 20260307_0004
Create Date: 2026-03-07 02:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0005"
down_revision: str | None = "20260307_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categorization_rules",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("match_type", sa.String(length=64), nullable=False),
        sa.Column("match_value", sa.String(length=512), nullable=False),
        sa.Column("assigned_category_id", sa.Uuid(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_from_transaction_id", sa.Uuid(), nullable=True),
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
            "match_type IN ('description_contains', 'merchant_equals', 'regex')",
            name="ck_categorization_rules_match_type_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_category_id"],
            ["categories.id"],
            name=op.f(
                "fk_categorization_rules_assigned_category_id_categories"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_categorization_rules_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categorization_rules")),
    )
    op.create_index(
        "ix_categorization_rules_assigned_category_id",
        "categorization_rules",
        ["assigned_category_id"],
        unique=False,
    )
    op.create_index(
        "ix_categorization_rules_user_id_is_active_priority",
        "categorization_rules",
        ["user_id", "is_active", "priority"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_categorization_rules_user_id_is_active_priority",
        table_name="categorization_rules",
    )
    op.drop_index(
        "ix_categorization_rules_assigned_category_id",
        table_name="categorization_rules",
    )
    op.drop_table("categorization_rules")
