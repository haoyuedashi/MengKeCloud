from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FollowUpRecord(Base):
    __tablename__ = "follow_up_records"
    __table_args__ = (
        Index("ix_follow_up_records_lead_id", "lead_id"),
        Index("ix_follow_up_records_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ai_analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
