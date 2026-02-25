from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_record import FollowUpRecord
from app.models.department import Department
from app.models.lead import Lead
from app.models.user import User


async def list_leads_between(
    session: AsyncSession,
    *,
    start_at: datetime,
    end_at: datetime,
    owner_id: str | None = None,
    dept_name: str | None = None,
) -> list[Lead]:
    stmt = select(Lead).where(Lead.created_at >= start_at, Lead.created_at < end_at)
    if owner_id:
        stmt = stmt.where(Lead.owner_id == owner_id)
    if dept_name:
        stmt = stmt.join(User, User.id == Lead.owner_id, isouter=True).where(User.dept_name == dept_name)
    stmt = stmt.order_by(Lead.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_followups_between(
    session: AsyncSession,
    *,
    start_at: datetime,
    end_at: datetime,
    operator_keys: list[str] | None = None,
) -> list[FollowUpRecord]:
    stmt = select(FollowUpRecord).where(
        FollowUpRecord.timestamp >= start_at,
        FollowUpRecord.timestamp < end_at,
    )
    if operator_keys:
        stmt = stmt.where(FollowUpRecord.operator.in_(operator_keys))
    stmt = stmt.order_by(FollowUpRecord.timestamp.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_active_users(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.active.is_(True)).order_by(User.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_active_departments(session: AsyncSession) -> list[Department]:
    stmt = select(Department).where(Department.active.is_(True)).order_by(Department.sort_order.asc(), Department.id.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
