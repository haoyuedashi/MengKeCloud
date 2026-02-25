"""align default admin display name

Revision ID: 20260222_0009
Revises: 20260222_0008
Create Date: 2026-02-22 23:30:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260222_0009"
down_revision: str | None = "20260222_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
               SET name = '老板'
             WHERE id = 'ST001'
               AND role = 'admin'
               AND name IN ('王销售', '系统管理员')
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
               SET name = '系统管理员'
             WHERE id = 'ST001'
               AND role = 'admin'
               AND name = '老板'
            """
        )
    )
