"""add settings core tables

Revision ID: 20260221_0003
Revises: 20260221_0002
Create Date: 2026-02-21 21:55:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260221_0003"
down_revision: str | None = "20260221_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("dict_items", sa.Column("color", sa.String(length=32), nullable=True))
    op.add_column(
        "dict_items",
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_name", sa.String(length=128), nullable=False),
        sa.Column("official_phone", sa.String(length=64), nullable=False),
        sa.Column("announcement", sa.String(length=500), nullable=False),
        sa.Column("annual_target", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_targets", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("max_leads_per_rep", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("global_drop_warning_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["departments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_departments_parent_id", "departments", ["parent_id"], unique=False)

    op.create_table(
        "system_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("menu_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("data_scope", sa.String(length=32), nullable=False, server_default="self"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("field_type", sa.String(length=32), nullable=False),
        sa.Column("placeholder", sa.String(length=255), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_custom_fields_entity", "custom_fields", ["entity"], unique=False)
    op.create_index("ix_custom_fields_entity_code", "custom_fields", ["entity", "code"], unique=True)

    op.create_table(
        "recycle_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rule1_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rule1_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("rule2_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rule2_days", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("rule2_protect_high_intent", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rule3_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rule3_count", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("notify_before_drop", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notify_after_drop", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("recycle_rules")

    op.drop_index("ix_custom_fields_entity_code", table_name="custom_fields")
    op.drop_index("ix_custom_fields_entity", table_name="custom_fields")
    op.drop_table("custom_fields")

    op.drop_table("system_roles")

    op.drop_index("ix_departments_parent_id", table_name="departments")
    op.drop_table("departments")

    op.drop_table("platform_settings")

    op.drop_column("dict_items", "is_system")
    op.drop_column("dict_items", "color")
