"""add custom field options jsonb

Revision ID: 20260222_0005
Revises: 20260222_0004
Create Date: 2026-02-22 16:10:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260222_0005"
down_revision: str | None = "20260222_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "custom_fields",
        sa.Column(
            "field_options",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("custom_fields", "field_options")
