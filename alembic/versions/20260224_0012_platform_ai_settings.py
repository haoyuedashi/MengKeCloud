"""add ai settings columns to platform_settings

Revision ID: 20260224_0012
Revises: 20260223_0011
Create Date: 2026-02-24 20:30:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260224_0012"
down_revision: str | None = "20260223_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "platform_settings",
        sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "platform_settings",
        sa.Column("ai_api_key", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "platform_settings",
        sa.Column(
            "ai_base_url",
            sa.String(length=255),
            nullable=False,
            server_default="https://api.openai.com/v1",
        ),
    )
    op.add_column(
        "platform_settings",
        sa.Column("ai_model", sa.String(length=128), nullable=False, server_default="gpt-4o-mini"),
    )
    op.add_column(
        "platform_settings",
        sa.Column("ai_timeout_seconds", sa.Integer(), nullable=False, server_default="12"),
    )


def downgrade() -> None:
    op.drop_column("platform_settings", "ai_timeout_seconds")
    op.drop_column("platform_settings", "ai_model")
    op.drop_column("platform_settings", "ai_base_url")
    op.drop_column("platform_settings", "ai_api_key")
    op.drop_column("platform_settings", "ai_enabled")
