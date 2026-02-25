from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_notification import SystemNotification


def add_notification(session: AsyncSession, entity: SystemNotification) -> None:
    session.add(entity)


async def insert_notification_if_absent(
    session: AsyncSession,
    *,
    staff_id: str,
    title: str,
    content: str,
    category: str,
    event_key: str,
) -> bool:
    stmt = (
        insert(SystemNotification)
        .values(
            staff_id=staff_id,
            title=title,
            content=content,
            category=category,
            event_key=event_key,
            is_read=False,
        )
        .on_conflict_do_nothing(index_elements=[SystemNotification.event_key])
        .returning(SystemNotification.id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_notification_by_event_key(session: AsyncSession, event_key: str) -> SystemNotification | None:
    result = await session.execute(select(SystemNotification).where(SystemNotification.event_key == event_key))
    return result.scalar_one_or_none()


async def get_notification(session: AsyncSession, notification_id: int) -> SystemNotification | None:
    return await session.get(SystemNotification, notification_id)


def build_notification_query(
    staff_id: str,
    unread_only: bool,
    category_prefix: str | None,
) -> Select[tuple[SystemNotification]]:
    stmt: Select[tuple[SystemNotification]] = select(SystemNotification).where(SystemNotification.staff_id == staff_id)
    if unread_only:
        stmt = stmt.where(SystemNotification.is_read.is_(False))
    if category_prefix:
        stmt = stmt.where(SystemNotification.category.like(f"{category_prefix}%"))
    return stmt


async def count_notifications(session: AsyncSession, base_query: Select[tuple[SystemNotification]]) -> int:
    stmt = select(func.count()).select_from(base_query.subquery())
    value = await session.scalar(stmt)
    return int(value or 0)


async def list_notifications(
    session: AsyncSession,
    base_query: Select[tuple[SystemNotification]],
    page: int,
    page_size: int,
) -> list[SystemNotification]:
    stmt = (
        base_query
        .order_by(SystemNotification.created_at.desc(), SystemNotification.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_notification_read(session: AsyncSession, entity: SystemNotification, read_at: datetime) -> None:
    entity.is_read = True
    entity.read_at = read_at


async def mark_notifications_read_all(
    session: AsyncSession,
    *,
    staff_id: str,
    category_prefix: str | None,
    read_at: datetime,
) -> int:
    stmt = (
        update(SystemNotification)
        .where(SystemNotification.staff_id == staff_id, SystemNotification.is_read.is_(False))
        .values(is_read=True, read_at=read_at)
    )
    if category_prefix:
        stmt = stmt.where(SystemNotification.category.like(f"{category_prefix}%"))
    result = await session.execute(stmt)
    return int(result.rowcount or 0)
