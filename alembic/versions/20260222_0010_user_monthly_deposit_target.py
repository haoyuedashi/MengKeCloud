"""add user monthly deposit target

Revision ID: 20260222_0010
Revises: 20260222_0009
Create Date: 2026-02-22 23:50:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260222_0010"
down_revision: str | None = "20260222_0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("monthly_deposit_target", sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE users SET monthly_deposit_target = 0 WHERE monthly_deposit_target IS NULL"))
    op.alter_column("users", "monthly_deposit_target", nullable=False)


def downgrade() -> None:
    op.drop_column("users", "monthly_deposit_target")
