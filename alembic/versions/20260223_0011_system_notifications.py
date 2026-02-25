"""add system notifications table

Revision ID: 20260223_0011
Revises: 20260222_0010
Create Date: 2026-02-23 15:55:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260223_0011"
down_revision: str | None = "20260222_0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("staff_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("event_key", sa.String(length=128), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["staff_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_system_notifications_staff_id", "system_notifications", ["staff_id"], unique=False)
    op.create_index("ix_system_notifications_is_read", "system_notifications", ["is_read"], unique=False)
    op.create_index("ix_system_notifications_created_at", "system_notifications", ["created_at"], unique=False)
    op.create_index("ix_system_notifications_event_key", "system_notifications", ["event_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_system_notifications_event_key", table_name="system_notifications")
    op.drop_index("ix_system_notifications_created_at", table_name="system_notifications")
    op.drop_index("ix_system_notifications_is_read", table_name="system_notifications")
    op.drop_index("ix_system_notifications_staff_id", table_name="system_notifications")
    op.drop_table("system_notifications")
