"""add monthly targets for departments and users

Revision ID: 20260222_0004
Revises: 20260221_0003
Create Date: 2026-02-22 13:45:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260222_0004"
down_revision: str | None = "20260221_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "departments",
        sa.Column("monthly_target", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("monthly_target", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "monthly_target")
    op.drop_column("departments", "monthly_target")
