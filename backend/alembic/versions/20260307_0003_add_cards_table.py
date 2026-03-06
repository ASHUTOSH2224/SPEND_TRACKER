"""Add cards table.

Revision ID: 20260307_0003
Revises: 20260307_0002
Create Date: 2026-03-07 01:15:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260307_0003"
down_revision: str | None = "20260307_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("nickname", sa.String(length=255), nullable=False),
        sa.Column("issuer_name", sa.String(length=255), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=False),
        sa.Column("last4", sa.String(length=4), nullable=False),
        sa.Column("statement_cycle_day", sa.Integer(), nullable=True),
        sa.Column("annual_fee_expected", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("joining_fee_expected", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reward_program_name", sa.String(length=255), nullable=True),
        sa.Column("reward_type", sa.String(length=32), nullable=False),
        sa.Column("reward_conversion_rate", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column(
            "reward_rule_config_json",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_cards_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cards")),
    )
    op.create_index("ix_cards_user_id_status", "cards", ["user_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cards_user_id_status", table_name="cards")
    op.drop_table("cards")
