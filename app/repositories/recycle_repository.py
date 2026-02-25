from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_record import FollowUpRecord
from app.models.lead import Lead
from app.models.pool_transfer_log import PoolTransferLog
from app.models.user import User


def build_assigned_leads_query() -> Select[tuple[Lead]]:
    return select(Lead).where(Lead.owner_id.is_not(None))


async def list_assigned_leads(session: AsyncSession) -> list[Lead]:
    result = await session.execute(build_assigned_leads_query())
    return list(result.scalars().all())


async def list_followups_for_lead(session: AsyncSession, lead_id: str) -> list[FollowUpRecord]:
    stmt = select(FollowUpRecord).where(FollowUpRecord.lead_id == lead_id).order_by(FollowUpRecord.timestamp.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user(session: AsyncSession, staff_id: str) -> User | None:
    return await session.get(User, staff_id)


async def list_active_managers(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.active.is_(True), User.role == "manager")
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_active_supervisors(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.active.is_(True), User.role.in_(["admin", "manager"]))
    result = await session.execute(stmt)
    return list(result.scalars().all())


def add_pool_transfer_log(session: AsyncSession, log: PoolTransferLog) -> None:
    session.add(log)


async def commit(session: AsyncSession) -> None:
    await session.commit()
