from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_session import RefreshSession
from app.models.user import User


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    result = await session.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


def add_refresh_session(session: AsyncSession, entity: RefreshSession) -> None:
    session.add(entity)


async def get_refresh_session(session: AsyncSession, session_id: str) -> RefreshSession | None:
    return await session.get(RefreshSession, session_id)


async def revoke_refresh_session(session: AsyncSession, entity: RefreshSession) -> None:
    entity.revoked = True
    entity.revoked_at = datetime.now(timezone.utc)


async def revoke_refresh_sessions_by_user(session: AsyncSession, user_id: str) -> None:
    result = await session.execute(
        select(RefreshSession).where(RefreshSession.user_id == user_id, RefreshSession.revoked.is_(False))
    )
    sessions = result.scalars().all()
    now = datetime.now(timezone.utc)
    for item in sessions:
        item.revoked = True
        item.revoked_at = now


async def commit(session: AsyncSession) -> None:
    await session.commit()
