from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_record import FollowUpRecord
from app.models.lead import Lead
from app.models.pool_transfer_log import PoolTransferLog


def build_pool_query(
    *,
    keyword: str | None,
    drop_reason: str | None,
    previous_owner: str | None,
) -> Select[tuple[Lead]]:
    query: Select[tuple[Lead]] = select(Lead).where(Lead.owner_id.is_(None))
    if keyword:
        query = query.where(or_(Lead.name.ilike(f"%{keyword}%"), Lead.phone.ilike(f"%{keyword}%")))
    if drop_reason:
        query = query.where(Lead.dynamic_data.op("->>")("drop_reason_type") == drop_reason)
    if previous_owner:
        query = query.where(Lead.dynamic_data.op("->>")("original_owner") == previous_owner)
    return query


async def count_pool_leads(session: AsyncSession, base_query: Select[tuple[Lead]]) -> int:
    stmt = select(func.count()).select_from(base_query.subquery())
    value = await session.scalar(stmt)
    return int(value or 0)


async def list_pool_leads(session: AsyncSession, base_query: Select[tuple[Lead]], page: int, page_size: int) -> list[Lead]:
    stmt = base_query.order_by(Lead.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_lead(session: AsyncSession, lead_id: str) -> Lead | None:
    return await session.get(Lead, lead_id)


async def delete_follow_ups_by_lead(session: AsyncSession, lead_id: str) -> None:
    await session.execute(delete(FollowUpRecord).where(FollowUpRecord.lead_id == lead_id))


async def delete_lead(session: AsyncSession, lead: Lead) -> None:
    await session.delete(lead)


async def list_leads_by_ids(session: AsyncSession, lead_ids: list[str]) -> list[Lead]:
    if not lead_ids:
        return []
    stmt = select(Lead).where(Lead.id.in_(lead_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def commit(session: AsyncSession) -> None:
    await session.commit()


def add_transfer_log(session: AsyncSession, log: PoolTransferLog) -> None:
    session.add(log)


def build_transfer_query(lead_id: str | None = None, action: str | None = None) -> Select[tuple[PoolTransferLog]]:
    stmt: Select[tuple[PoolTransferLog]] = select(PoolTransferLog)
    if lead_id:
        stmt = stmt.where(PoolTransferLog.lead_id == lead_id)
    if action:
        stmt = stmt.where(PoolTransferLog.action == action)
    return stmt


async def count_transfer_logs(session: AsyncSession, base_query: Select[tuple[PoolTransferLog]]) -> int:
    stmt = select(func.count()).select_from(base_query.subquery())
    value = await session.scalar(stmt)
    return int(value or 0)


async def list_transfer_logs(
    session: AsyncSession,
    base_query: Select[tuple[PoolTransferLog]],
    page: int,
    page_size: int,
) -> list[PoolTransferLog]:
    stmt = base_query.order_by(PoolTransferLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    return list(result.scalars().all())
