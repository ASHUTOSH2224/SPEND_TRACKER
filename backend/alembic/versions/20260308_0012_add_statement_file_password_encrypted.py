"""Add encrypted statement file password column.

Revision ID: 20260308_0012
Revises: 20260307_0011
Create Date: 2026-03-08 05:35:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260308_0012"
down_revision: str | None = "20260307_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "statements",
        sa.Column("file_password_encrypted", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("statements", "file_password_encrypted")
