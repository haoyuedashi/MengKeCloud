from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.system_notification import SystemNotification
from app.repositories import notification_repository


def _to_dict(entity: SystemNotification) -> dict[str, Any]:
    return {
        "id": entity.id,
        "title": entity.title,
        "content": entity.content,
        "category": entity.category,
        "isRead": entity.is_read,
        "createdAt": entity.created_at.isoformat(sep=" ") if entity.created_at else None,
        "readAt": entity.read_at.isoformat(sep=" ") if entity.read_at else None,
    }


async def list_notifications(
    session: AsyncSession,
    *,
    current_staff: dict[str, Any],
    unread_only: bool,
    category_prefix: str | None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    staff_id = str(current_staff.get("staffId") or "")
    if not staff_id:
        raise AppException("当前登录信息无效", business_code=400, status_code=401)

    base_query = notification_repository.build_notification_query(
        staff_id=staff_id,
        unread_only=unread_only,
        category_prefix=category_prefix,
    )
    total = await notification_repository.count_notifications(session, base_query)
    rows = await notification_repository.list_notifications(session, base_query, page, page_size)
    return {"list": [_to_dict(item) for item in rows], "total": total}


async def mark_read(session: AsyncSession, *, current_staff: dict[str, Any], notification_id: int) -> dict[str, Any]:
    staff_id = str(current_staff.get("staffId") or "")
    if not staff_id:
        raise AppException("当前登录信息无效", business_code=400, status_code=401)

    row = await notification_repository.get_notification(session, notification_id)
    if row is None:
        raise AppException("通知不存在", business_code=400, status_code=404)
    if row.staff_id != staff_id:
        raise AppException("无权限操作该通知", business_code=401, status_code=403)

    if not row.is_read:
        await notification_repository.mark_notification_read(session, row, datetime.now(timezone.utc))
        await session.commit()
        await session.refresh(row)
    return _to_dict(row)


async def mark_read_all(
    session: AsyncSession,
    *,
    current_staff: dict[str, Any],
    category_prefix: str | None,
) -> dict[str, Any]:
    staff_id = str(current_staff.get("staffId") or "")
    if not staff_id:
        raise AppException("当前登录信息无效", business_code=400, status_code=401)

    updated_count = await notification_repository.mark_notifications_read_all(
        session,
        staff_id=staff_id,
        category_prefix=category_prefix,
        read_at=datetime.now(timezone.utc),
    )
    await session.commit()
    return {"updatedCount": updated_count}
