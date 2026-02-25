from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_record import FollowUpRecord
from app.models.user import User
from app.models.lead import Lead
from app.models.platform_setting import PlatformSetting


async def count_leads_between(
    session: AsyncSession,
    *,
    start_at: datetime,
    end_at: datetime,
    owner_id: str | None = None,
    dept_name: str | None = None,
) -> int:
    stmt = select(func.count()).select_from(Lead).where(Lead.created_at >= start_at, Lead.created_at < end_at)
    if owner_id:
        stmt = stmt.where(Lead.owner_id == owner_id)
    if dept_name:
        stmt = stmt.join(User, User.id == Lead.owner_id, isouter=True).where(User.dept_name == dept_name)
    value = await session.scalar(stmt)
    return int(value or 0)


async def count_signed_leads_between(
    session: AsyncSession,
    *,
    start_at: datetime,
    end_at: datetime,
    owner_id: str | None = None,
    dept_name: str | None = None,
) -> int:
    stmt = (
        select(func.count())
        .select_from(Lead)
        .where(
            Lead.created_at >= start_at,
            Lead.created_at < end_at,
            Lead.status.in_(["signed", "已签约"]),
        )
    )
    if owner_id:
        stmt = stmt.where(Lead.owner_id == owner_id)
    if dept_name:
        stmt = stmt.join(User, User.id == Lead.owner_id, isouter=True).where(User.dept_name == dept_name)
    value = await session.scalar(stmt)
    return int(value or 0)


async def count_deposit_leads_between(
    session: AsyncSession,
    *,
    start_at: datetime,
    end_at: datetime,
    owner_id: str | None = None,
    dept_name: str | None = None,
) -> int:
    stmt = (
        select(func.count())
        .select_from(Lead)
        .where(
            Lead.created_at >= start_at,
            Lead.created_at < end_at,
            Lead.status.in_(["deposit_paid", "已定金", "已交定金"]),
        )
    )
    if owner_id:
        stmt = stmt.where(Lead.owner_id == owner_id)
    if dept_name:
        stmt = stmt.join(User, User.id == Lead.owner_id, isouter=True).where(User.dept_name == dept_name)
    value = await session.scalar(stmt)
    return int(value or 0)


async def count_followups_between(
    session: AsyncSession,
    *,
    start_at: datetime,
    end_at: datetime,
    operator_keys: list[str] | None = None,
) -> int:
    stmt = (
        select(func.count())
        .select_from(FollowUpRecord)
        .where(FollowUpRecord.timestamp >= start_at, FollowUpRecord.timestamp < end_at)
    )
    if operator_keys:
        stmt = stmt.where(FollowUpRecord.operator.in_(operator_keys))
    value = await session.scalar(stmt)
    return int(value or 0)


async def list_todo_leads(
    session: AsyncSession,
    limit: int = 4,
    owner_id: str | None = None,
    dept_name: str | None = None,
) -> list[Lead]:
    stmt = (
        select(Lead)
        .where(Lead.owner_id.is_not(None), Lead.status.not_in(["signed", "已签约", "lost", "战败流失", "invalid", "无效线索", "无效客户"]))
        .order_by(Lead.last_follow_up.asc().nullsfirst(), Lead.updated_at.asc())
        .limit(limit)
    )
    if owner_id:
        stmt = stmt.where(Lead.owner_id == owner_id)
    if dept_name:
        stmt = stmt.join(User, User.id == Lead.owner_id, isouter=True).where(User.dept_name == dept_name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_pool_warning_leads(
    session: AsyncSession,
    limit: int = 2,
    owner_id: str | None = None,
    dept_name: str | None = None,
) -> list[Lead]:
    if owner_id:
        stmt = (
            select(Lead)
            .where(
                Lead.owner_id == owner_id,
            Lead.status.not_in(["signed", "已签约", "lost", "战败流失", "invalid", "无效线索", "无效客户"]),
            )
            .order_by(Lead.last_follow_up.asc().nullsfirst(), Lead.updated_at.asc())
            .limit(limit)
        )
    elif dept_name:
        stmt = (
            select(Lead)
            .join(User, User.id == Lead.owner_id)
            .where(
                User.dept_name == dept_name,
            Lead.status.not_in(["signed", "已签约", "lost", "战败流失", "invalid", "无效线索", "无效客户"]),
            )
            .order_by(Lead.last_follow_up.asc().nullsfirst(), Lead.updated_at.asc())
            .limit(limit)
        )
    else:
        stmt = (
            select(Lead)
            .where(Lead.owner_id.is_(None))
            .order_by(Lead.updated_at.asc())
            .limit(limit)
        )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_platform_setting(session: AsyncSession) -> PlatformSetting | None:
    stmt = select(PlatformSetting).order_by(PlatformSetting.id.asc()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)
