from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class PlatformSetting(TimestampMixin, Base):
    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(128), nullable=False)
    official_phone: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    announcement: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    annual_target: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_targets: Mapped[list[int]] = mapped_column(JSONB, nullable=False, default=list)
    max_leads_per_rep: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    global_drop_warning_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    ai_enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    ai_api_key: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    ai_base_url: Mapped[str] = mapped_column(String(255), nullable=False, default="https://api.openai.com/v1")
    ai_model: Mapped[str] = mapped_column(String(128), nullable=False, default="gpt-4o-mini")
    ai_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
