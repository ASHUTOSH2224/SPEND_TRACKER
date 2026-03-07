"""Add reward ledgers table.

Revision ID: 20260307_0009
Revises: 20260307_0008
Create Date: 2026-03-07 05:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0009"
down_revision: str | None = "20260307_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reward_ledgers",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("card_id", sa.Uuid(), nullable=False),
        sa.Column("statement_id", sa.Uuid(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("reward_points", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("reward_value_estimate", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
            "event_type IN ('earned', 'redeemed', 'expired', 'adjusted', 'cashback')",
            name="ck_reward_ledgers_event_type_allowed",
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'extracted', 'estimated')",
            name="ck_reward_ledgers_source_allowed",
        ),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"], name=op.f("fk_reward_ledgers_card_id_cards")),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["statements.id"],
            name=op.f("fk_reward_ledgers_statement_id_statements"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_reward_ledgers_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reward_ledgers")),
    )
    op.create_index(
        "ix_reward_ledgers_user_id_card_id_event_date",
        "reward_ledgers",
        ["user_id", "card_id", "event_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reward_ledgers_user_id_card_id_event_date", table_name="reward_ledgers")
    op.drop_table("reward_ledgers")
