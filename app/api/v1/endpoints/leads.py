from typing import Any
import importlib

from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.core.exceptions import AppException
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.lead import (
    AssignableStaffData,
    FollowUpAiSuggestionData,
    FollowUpAiSuggestionRequest,
    LeadAssignData,
    LeadAssignRequest,
    FollowUpCreate,
    FollowUpRecordOut,
    LeadCreate,
    LeadDeleteData,
    LeadDetailData,
    LeadListData,
    LeadImportData,
    LeadOut,
    LeadToPoolData,
    LeadToPoolRequest,
    LeadUpdate,
)
leads_service = importlib.import_module("app.services.leads_service")

router = APIRouter(tags=["leads"])


@router.get("/leads", response_model=ApiEnvelope[LeadListData])
async def get_leads(
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    source: str | None = Query(default=None),
) -> dict[str, Any]:
    data = await leads_service.list_leads(
        db,
        current_staff=current_staff,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        source=source,
    )
    return success_response(data=data, message="操作成功")


@router.get("/leads/assignable-staff", response_model=ApiEnvelope[AssignableStaffData])
async def get_assignable_staff(
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager")),
) -> dict[str, Any]:
    data = await leads_service.list_assignable_staff(db, current_staff)
    return success_response(data=data, message="操作成功")


@router.post("/leads", response_model=ApiEnvelope[LeadOut])
async def create_lead(
    payload: LeadCreate,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await leads_service.create_lead(db, payload, current_staff)
    return success_response(data=data, message="操作成功")


@router.post("/leads/assign", response_model=ApiEnvelope[LeadAssignData])
async def assign_leads(
    payload: LeadAssignRequest,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager")),
) -> dict[str, Any]:
    data = await leads_service.assign_leads(db, payload.leadIds, payload.staffId, current_staff)
    return success_response(data=data, message="操作成功")


@router.post("/leads/to-pool", response_model=ApiEnvelope[LeadToPoolData])
async def transfer_leads_to_pool(
    payload: LeadToPoolRequest,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await leads_service.transfer_leads_to_pool(db, payload.leadIds, current_staff)
    return success_response(data=data, message="操作成功")


@router.get("/leads/export")
async def export_leads_csv(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    source: str | None = Query(default=None),
) -> StreamingResponse:
    content = await leads_service.export_leads_csv(
        db,
        keyword=keyword,
        status=status,
        source=source,
    )
    filename = f"leads-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/leads/import", response_model=ApiEnvelope[LeadImportData])
async def import_leads_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise AppException("仅支持 CSV 文件导入", business_code=400, status_code=400)
    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw_bytes.decode("gbk")
        except UnicodeDecodeError as exc:
            raise AppException("文件编码不支持，请使用 UTF-8 或 GBK 编码的 CSV", business_code=400, status_code=400) from exc
    data = await leads_service.import_leads_csv(db, csv_content=text, current_staff=current_staff)
    return success_response(data=data, message="操作成功")


@router.get("/leads/{lead_id}", response_model=ApiEnvelope[LeadDetailData])
async def get_lead_detail(
    lead_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await leads_service.get_lead_detail(db, lead_id, current_staff)
    return success_response(data=data, message="操作成功")


@router.put("/leads/{lead_id}", response_model=ApiEnvelope[LeadOut])
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await leads_service.update_lead(db, lead_id, payload, current_staff)
    return success_response(data=data, message="操作成功")


@router.delete("/leads/{lead_id}", response_model=ApiEnvelope[LeadDeleteData])
async def delete_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager")),
) -> dict[str, Any]:
    await leads_service.delete_lead(db, lead_id, current_staff)
    return success_response(data={"leadId": lead_id}, message="操作成功")


@router.post("/leads/{lead_id}/follow-up", response_model=ApiEnvelope[FollowUpRecordOut])
async def create_follow_up(
    lead_id: str,
    payload: FollowUpCreate,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await leads_service.create_follow_up(db, lead_id, payload, current_staff)
    return success_response(data=data, message="操作成功")


@router.post("/leads/{lead_id}/ai-suggestion", response_model=ApiEnvelope[FollowUpAiSuggestionData])
async def generate_ai_follow_up_suggestion(
    lead_id: str,
    payload: FollowUpAiSuggestionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await leads_service.generate_ai_follow_up_suggestion(
        db,
        lead_id,
        current_staff=current_staff,
        user_goal=payload.user_goal,
    )
    return success_response(data=data, message="操作成功")
