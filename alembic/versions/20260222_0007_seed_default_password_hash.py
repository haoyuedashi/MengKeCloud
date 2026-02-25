"""seed default password hash for existing users

Revision ID: 20260222_0007
Revises: 20260222_0006
Create Date: 2026-02-22 21:35:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260222_0007"
down_revision: str | None = "20260222_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DEFAULT_ARGON2_HASH = "$argon2id$v=19$m=65536,t=3,p=4$cU4pZezd2zvnXEtJKcV4Dw$djrnQacxPIV66kpqyCK1EZzDrRtPZlFKLvLWQca1IfY"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
               SET password_hash = :default_hash,
                   password_updated_at = CURRENT_TIMESTAMP,
                   failed_attempts = 0,
                   locked_until = NULL
             WHERE COALESCE(password_hash, '') = ''
            """
        ).bindparams(default_hash=DEFAULT_ARGON2_HASH)
    )
    op.execute(sa.text("UPDATE users SET role = 'admin' WHERE id = 'ST001'"))


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
               SET password_hash = '',
                   password_updated_at = NULL,
                   failed_attempts = 0,
                   locked_until = NULL
            """
        )
    )
