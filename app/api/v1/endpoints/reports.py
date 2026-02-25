from typing import Any
import importlib

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.reports import ReportsOverviewData

reports_service = importlib.import_module("app.services.reports_service")

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/overview", response_model=ApiEnvelope[ReportsOverviewData])
async def get_reports_overview(
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
    trend_window: str = Query(default="7days", pattern="^(7days|30days)$"),
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    dept_name: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
) -> dict[str, Any]:
    data = await reports_service.get_reports_overview(
        db,
        trend_window,
        start_date,
        end_date,
        dept_name,
        owner_id,
        current_staff,
    )
    return success_response(data=data, message="操作成功")
