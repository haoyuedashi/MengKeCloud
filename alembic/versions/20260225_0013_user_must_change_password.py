"""add must_change_password flag to users

Revision ID: 20260225_0013
Revises: 20260224_0012
Create Date: 2026-02-25 15:35:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260225_0013"
down_revision: str | None = "20260224_0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
