from datetime import datetime

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_record import FollowUpRecord
from app.models.lead import Lead
from app.models.pool_transfer_log import PoolTransferLog
from app.models.user import User


def build_leads_query(
    keyword: str | None,
    status: str | None,
    source: str | None,
    owner_id: str | None = None,
    owner_ids: list[str] | None = None,
    exclude_pool: bool = False,
) -> Select[tuple[Lead]]:
    query = select(Lead)
    if exclude_pool:
        query = query.where(Lead.owner_id.is_not(None))
    if keyword:
        query = query.where(or_(Lead.name.ilike(f"%{keyword}%"), Lead.phone.ilike(f"%{keyword}%")))
    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
    if owner_id:
        query = query.where(Lead.owner_id == owner_id)
    if owner_ids is not None:
        if len(owner_ids) == 0:
            query = query.where(Lead.owner_id == "")
        else:
            query = query.where(Lead.owner_id.in_(owner_ids))
    return query


async def count_leads(session: AsyncSession, base_query: Select[tuple[Lead]]) -> int:
    stmt = select(func.count()).select_from(base_query.subquery())
    value = await session.scalar(stmt)
    return int(value or 0)


async def list_leads(session: AsyncSession, base_query: Select[tuple[Lead]], page: int, page_size: int) -> list[Lead]:
    stmt = base_query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_lead(session: AsyncSession, lead_id: str) -> Lead | None:
    return await session.get(Lead, lead_id)


async def list_follow_ups(session: AsyncSession, lead_id: str) -> list[FollowUpRecord]:
    stmt = (
        select(FollowUpRecord)
        .where(FollowUpRecord.lead_id == lead_id)
        .order_by(FollowUpRecord.timestamp.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_daily_leads(session: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(Lead).where(Lead.id.like(f"{prefix}%"))
    value = await session.scalar(stmt)
    return int(value or 0)


def add_lead(session: AsyncSession, lead: Lead) -> None:
    session.add(lead)


def add_follow_up(session: AsyncSession, record: FollowUpRecord) -> None:
    session.add(record)


def add_pool_transfer_log(session: AsyncSession, log: PoolTransferLog) -> None:
    session.add(log)


async def commit(session: AsyncSession) -> None:
    await session.commit()


async def refresh(session: AsyncSession, entity: Lead | FollowUpRecord) -> None:
    await session.refresh(entity)


async def delete_follow_ups_by_lead(session: AsyncSession, lead_id: str) -> None:
    await session.execute(delete(FollowUpRecord).where(FollowUpRecord.lead_id == lead_id))


async def delete_lead(session: AsyncSession, lead: Lead) -> None:
    await session.delete(lead)


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


async def list_active_users(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.active.is_(True)).order_by(User.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_active_users_by_department(session: AsyncSession, dept_name: str) -> list[User]:
    stmt = (
        select(User)
        .where(User.active.is_(True), User.dept_name == dept_name)
        .order_by(User.created_at.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_users_by_department(session: AsyncSession, dept_name: str) -> list[User]:
    stmt = select(User).where(User.dept_name == dept_name).order_by(User.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


def build_lead_id_prefix(now: datetime) -> str:
    return f"LD{now.strftime('%Y%m%d')}"
