from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.notification import NotificationItem, NotificationReadAllData, NotificationsData, RecycleRunResult
from app.services import notification_service, recycle_runner_service


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=ApiEnvelope[NotificationsData])
async def list_notifications(
    unread_only: bool = Query(default=False, alias="unreadOnly"),
    category_prefix: str | None = Query(default=None, alias="categoryPrefix"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await notification_service.list_notifications(
        db,
        current_staff=current_staff,
        unread_only=unread_only,
        category_prefix=category_prefix,
        page=page,
        page_size=page_size,
    )
    return success_response(data=data, message="操作成功")


@router.put("/{notification_id}/read", response_model=ApiEnvelope[NotificationItem])
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await notification_service.mark_read(
        db,
        current_staff=current_staff,
        notification_id=notification_id,
    )
    return success_response(data=data, message="操作成功")


@router.put("/read-all", response_model=ApiEnvelope[NotificationReadAllData])
async def mark_notifications_read_all(
    category_prefix: str | None = Query(default=None, alias="categoryPrefix"),
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await notification_service.mark_read_all(
        db,
        current_staff=current_staff,
        category_prefix=category_prefix,
    )
    return success_response(data=data, message="操作成功")


@router.post("/recycle/run-now", response_model=ApiEnvelope[RecycleRunResult])
async def run_recycle_now(
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    result = await recycle_runner_service.run_recycle_once()
    data = {
        "recycledCount": result.recycled_count,
        "beforeNotifiedCount": result.before_notified_count,
        "afterNotifiedCount": result.after_notified_count,
    }
    return success_response(data=data, message="操作成功")
