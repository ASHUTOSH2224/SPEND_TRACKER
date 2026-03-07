"""Add transactions table.

Revision ID: 20260307_0007
Revises: 20260307_0006
Create Date: 2026-03-07 04:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260307_0007"
down_revision: str | None = "20260307_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=False),
        sa.Column("txn_date", sa.Date(), nullable=False),
        sa.Column("posted_date", sa.Date(), nullable=True),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column("normalized_merchant", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("txn_direction", sa.String(length=16), nullable=False),
        sa.Column("txn_type", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("category_source", sa.String(length=32), nullable=True),
        sa.Column("category_confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("category_explanation", sa.Text(), nullable=True),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("duplicate_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_card_charge", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("charge_type", sa.String(length=64), nullable=True),
        sa.Column("is_reward_related", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reward_points_delta", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("cashback_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("source_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata_json",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
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
            "txn_direction IN ('debit', 'credit')",
            name="ck_transactions_txn_direction_allowed",
        ),
        sa.CheckConstraint(
            "txn_type IN ('spend', 'refund', 'charge', 'reward', 'manual_adjustment')",
            name="ck_transactions_txn_type_allowed",
        ),
        sa.CheckConstraint(
            "category_source IS NULL OR category_source IN ('rule', 'history', 'llm', 'manual')",
            name="ck_transactions_category_source_allowed",
        ),
        sa.CheckConstraint(
            "category_confidence IS NULL OR "
            "(category_confidence >= 0 AND category_confidence <= 1)",
            name="ck_transactions_category_confidence_range",
        ),
        sa.CheckConstraint(
            "amount >= 0",
            name="ck_transactions_amount_non_negative",
        ),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], name=op.f("fk_transactions_card_id_cards")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_transactions_category_id_categories"),
        ),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["statements.id"],
            name=op.f("fk_transactions_statement_id_statements"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_transactions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index("ix_transactions_is_card_charge_charge_type", "transactions", ["is_card_charge", "charge_type"], unique=False)
    op.create_index("ix_transactions_review_required", "transactions", ["review_required"], unique=False)
    op.create_index("ix_transactions_statement_id", "transactions", ["statement_id"], unique=False)
    op.create_index("ix_transactions_user_id_card_id_txn_date", "transactions", ["user_id", "card_id", "txn_date"], unique=False)
    op.create_index("ix_transactions_user_id_category_id_txn_date", "transactions", ["user_id", "category_id", "txn_date"], unique=False)
    op.create_index("ix_transactions_user_id_source_hash", "transactions", ["user_id", "source_hash"], unique=False)
    op.create_index("ix_transactions_user_id_txn_date", "transactions", ["user_id", "txn_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_user_id_txn_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id_source_hash", table_name="transactions")
    op.drop_index("ix_transactions_user_id_category_id_txn_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id_card_id_txn_date", table_name="transactions")
    op.drop_index("ix_transactions_statement_id", table_name="transactions")
    op.drop_index("ix_transactions_review_required", table_name="transactions")
    op.drop_index("ix_transactions_is_card_charge_charge_type", table_name="transactions")
    op.drop_table("transactions")
