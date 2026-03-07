"""Add transaction category audit table.

Revision ID: 20260307_0008
Revises: 20260307_0007
Create Date: 2026-03-07 04:25:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0008"
down_revision: str | None = "20260307_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transaction_category_audit",
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("old_category_id", sa.Uuid(), nullable=True),
        sa.Column("new_category_id", sa.Uuid(), nullable=False),
        sa.Column("changed_by", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "changed_by IN ('user', 'system')",
            name="ck_transaction_category_audit_changed_by_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["new_category_id"],
            ["categories.id"],
            name=op.f("fk_transaction_category_audit_new_category_id_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["old_category_id"],
            ["categories.id"],
            name=op.f("fk_transaction_category_audit_old_category_id_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name=op.f("fk_transaction_category_audit_transaction_id_transactions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transaction_category_audit")),
    )
    op.create_index(
        "ix_transaction_category_audit_transaction_id_created_at",
        "transaction_category_audit",
        ["transaction_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transaction_category_audit_transaction_id_created_at",
        table_name="transaction_category_audit",
    )
    op.drop_table("transaction_category_audit")
