from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class SystemRole(TimestampMixin, Base):
    __tablename__ = "system_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    menu_keys: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    data_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="self")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
