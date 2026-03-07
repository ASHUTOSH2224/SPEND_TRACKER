"""Add statements table.

Revision ID: 20260307_0006
Revises: 20260307_0005
Create Date: 2026-03-07 03:15:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0006"
down_revision: str | None = "20260307_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "statements",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_storage_key", sa.String(length=1024), nullable=False),
        sa.Column("file_type", sa.String(length=16), nullable=False),
        sa.Column("statement_period_start", sa.Date(), nullable=False),
        sa.Column("statement_period_end", sa.Date(), nullable=False),
        sa.Column("upload_status", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("extraction_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("categorization_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("transaction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
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
            "file_type IN ('pdf', 'csv', 'xls', 'xlsx')",
            name="ck_statements_file_type_allowed",
        ),
        sa.CheckConstraint(
            "upload_status IN ('uploaded', 'processing', 'completed', 'failed')",
            name="ck_statements_upload_status_allowed",
        ),
        sa.CheckConstraint(
            "extraction_status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_statements_extraction_status_allowed",
        ),
        sa.CheckConstraint(
            "categorization_status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_statements_categorization_status_allowed",
        ),
        sa.CheckConstraint(
            "statement_period_end >= statement_period_start",
            name="ck_statements_period_range_valid",
        ),
        sa.CheckConstraint(
            "transaction_count >= 0",
            name="ck_statements_transaction_count_non_negative",
        ),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], name=op.f("fk_statements_card_id_cards")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_statements_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_statements")),
    )
    op.create_index("ix_statements_upload_status_extraction_status", "statements", ["upload_status", "extraction_status"], unique=False)
    op.create_index("ix_statements_statement_period_start_statement_period_end", "statements", ["statement_period_start", "statement_period_end"], unique=False)
    op.create_index("ix_statements_user_id_card_id", "statements", ["user_id", "card_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_statements_user_id_card_id", table_name="statements")
    op.drop_index("ix_statements_statement_period_start_statement_period_end", table_name="statements")
    op.drop_index("ix_statements_upload_status_extraction_status", table_name="statements")
    op.drop_table("statements")
