"""add pool transfer logs

Revision ID: 20260221_0002
Revises: 20260221_0001
Create Date: 2026-02-21 17:35:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260221_0002"
down_revision: str | None = "20260221_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pool_transfer_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("from_owner_id", sa.String(length=32), nullable=True),
        sa.Column("to_owner_id", sa.String(length=32), nullable=True),
        sa.Column("operator_staff_id", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pool_transfer_logs_lead_id", "pool_transfer_logs", ["lead_id"], unique=False)
    op.create_index("ix_pool_transfer_logs_action", "pool_transfer_logs", ["action"], unique=False)
    op.create_index("ix_pool_transfer_logs_created_at", "pool_transfer_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pool_transfer_logs_created_at", table_name="pool_transfer_logs")
    op.drop_index("ix_pool_transfer_logs_action", table_name="pool_transfer_logs")
    op.drop_index("ix_pool_transfer_logs_lead_id", table_name="pool_transfer_logs")
    op.drop_table("pool_transfer_logs")
