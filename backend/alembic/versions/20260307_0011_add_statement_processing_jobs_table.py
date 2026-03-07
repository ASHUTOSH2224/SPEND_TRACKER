"""Add statement processing jobs table.

Revision ID: 20260307_0011
Revises: 20260307_0010
Create Date: 2026-03-07 06:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260307_0011"
down_revision: str | None = "20260307_0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "statement_processing_jobs",
        sa.Column("statement_id", sa.Uuid(), nullable=False),
        sa.Column("trigger_source", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="queued",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "queued_at",
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
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_statement_processing_jobs_status_allowed",
        ),
        sa.CheckConstraint(
            "trigger_source IN ('create', 'retry')",
            name="ck_statement_processing_jobs_trigger_source_allowed",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_statement_processing_jobs_attempt_count_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["statement_id"],
            ["statements.id"],
            name=op.f("fk_statement_processing_jobs_statement_id_statements"),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_statement_processing_jobs"),
        ),
    )
    op.create_index(
        "ix_statement_processing_jobs_status_created_at",
        "statement_processing_jobs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_statement_processing_jobs_statement_id_created_at",
        "statement_processing_jobs",
        ["statement_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_statement_processing_jobs_statement_id_created_at",
        table_name="statement_processing_jobs",
    )
    op.drop_index(
        "ix_statement_processing_jobs_status_created_at",
        table_name="statement_processing_jobs",
    )
    op.drop_table("statement_processing_jobs")
