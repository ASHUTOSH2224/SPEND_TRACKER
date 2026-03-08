"""Add payment transaction type.

Revision ID: 20260308_0014
Revises: 20260308_0013
Create Date: 2026-03-08 09:15:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260308_0014"
down_revision: str | None = "20260308_0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint(
            "ck_transactions_txn_type_allowed",
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_transactions_txn_type_allowed",
            "txn_type IN ('spend', 'refund', 'payment', 'charge', 'reward', 'manual_adjustment')",
        )


def downgrade() -> None:
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint(
            "ck_transactions_txn_type_allowed",
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_transactions_txn_type_allowed",
            "txn_type IN ('spend', 'refund', 'charge', 'reward', 'manual_adjustment')",
        )
