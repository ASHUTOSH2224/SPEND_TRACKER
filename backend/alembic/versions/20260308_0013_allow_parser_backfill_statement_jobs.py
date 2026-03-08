"""Allow parser backfill statement processing jobs.

Revision ID: 20260308_0013
Revises: 20260308_0012
Create Date: 2026-03-08 08:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260308_0013"
down_revision: str | None = "20260308_0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("statement_processing_jobs") as batch_op:
        batch_op.drop_constraint(
            "ck_statement_processing_jobs_trigger_source_allowed",
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_statement_processing_jobs_trigger_source_allowed",
            "trigger_source IN ('create', 'retry', 'parser_backfill')",
        )


def downgrade() -> None:
    with op.batch_alter_table("statement_processing_jobs") as batch_op:
        batch_op.drop_constraint(
            "ck_statement_processing_jobs_trigger_source_allowed",
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_statement_processing_jobs_trigger_source_allowed",
            "trigger_source IN ('create', 'retry')",
        )
