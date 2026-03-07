"""Add card charge summaries table.

Revision ID: 20260307_0010
Revises: 20260307_0009
Create Date: 2026-03-07 05:25:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0010"
down_revision: str | None = "20260307_0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_charge_summaries",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("period_month", sa.Date(), nullable=False),
        sa.Column("annual_fee_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("joining_fee_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("late_fee_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("finance_charge_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("emi_processing_fee_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("cash_advance_fee_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("forex_markup_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("other_charge_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("total_charge_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
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
        sa.CheckConstraint("annual_fee_amount >= 0", name="ck_card_charge_summaries_annual_fee_non_negative"),
        sa.CheckConstraint("joining_fee_amount >= 0", name="ck_card_charge_summaries_joining_fee_non_negative"),
        sa.CheckConstraint("late_fee_amount >= 0", name="ck_card_charge_summaries_late_fee_non_negative"),
        sa.CheckConstraint(
            "finance_charge_amount >= 0",
            name="ck_card_charge_summaries_finance_charge_non_negative",
        ),
        sa.CheckConstraint(
            "emi_processing_fee_amount >= 0",
            name="ck_card_charge_summaries_emi_processing_fee_non_negative",
        ),
        sa.CheckConstraint(
            "cash_advance_fee_amount >= 0",
            name="ck_card_charge_summaries_cash_advance_fee_non_negative",
        ),
        sa.CheckConstraint(
            "forex_markup_amount >= 0",
            name="ck_card_charge_summaries_forex_markup_non_negative",
        ),
        sa.CheckConstraint("tax_amount >= 0", name="ck_card_charge_summaries_tax_non_negative"),
        sa.CheckConstraint(
            "other_charge_amount >= 0",
            name="ck_card_charge_summaries_other_charge_non_negative",
        ),
        sa.CheckConstraint(
            "total_charge_amount >= 0",
            name="ck_card_charge_summaries_total_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["cards.id"],
            name=op.f("fk_card_charge_summaries_card_id_cards"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_card_charge_summaries_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_card_charge_summaries")),
    )
    op.create_index(
        "ix_card_charge_summaries_user_id_card_id_period_month",
        "card_charge_summaries",
        ["user_id", "card_id", "period_month"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_card_charge_summaries_user_id_card_id_period_month",
        table_name="card_charge_summaries",
    )
    op.drop_table("card_charge_summaries")
