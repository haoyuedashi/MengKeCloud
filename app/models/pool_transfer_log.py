from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PoolTransferLog(Base):
    __tablename__ = "pool_transfer_logs"
    __table_args__ = (
        Index("ix_pool_transfer_logs_lead_id", "lead_id"),
        Index("ix_pool_transfer_logs_action", "action"),
        Index("ix_pool_transfer_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_owner_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_owner_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    operator_staff_id: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
