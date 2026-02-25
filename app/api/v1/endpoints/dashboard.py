from typing import Any
import importlib

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.dashboard import DashboardOverviewData

dashboard_service = importlib.import_module("app.services.dashboard_service")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=ApiEnvelope[DashboardOverviewData])
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await dashboard_service.get_dashboard_overview(db, current_staff)
    return success_response(data=data, message="操作成功")
