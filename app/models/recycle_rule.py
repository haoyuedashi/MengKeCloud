from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class RecycleRule(TimestampMixin, Base):
    __tablename__ = "recycle_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rule1_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rule1_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    rule2_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rule2_days: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    rule2_protect_high_intent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rule3_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rule3_count: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    notify_before_drop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_after_drop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
