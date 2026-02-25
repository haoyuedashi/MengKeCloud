"""add department leader and org user password fields

Revision ID: 20260222_0008
Revises: 20260222_0007
Create Date: 2026-02-22 23:10:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260222_0008"
down_revision: str | None = "20260222_0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("leader_staff_id", sa.String(length=32), nullable=True))
    op.execute(sa.text("UPDATE departments SET leader_staff_id = 'ST001' WHERE leader_staff_id IS NULL"))
    op.alter_column("departments", "leader_staff_id", nullable=False)


def downgrade() -> None:
    op.drop_column("departments", "leader_staff_id")
