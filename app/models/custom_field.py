from typing import Any

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class CustomField(TimestampMixin, Base):
    __tablename__ = "custom_fields"
    __table_args__ = (
        Index("ix_custom_fields_entity", "entity"),
        Index("ix_custom_fields_entity_code", "entity", "code", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)
    placeholder: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    field_options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
