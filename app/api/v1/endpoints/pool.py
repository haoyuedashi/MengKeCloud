from typing import Any
import importlib

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_staff, require_roles
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.pool import (
    PoolAssignData,
    PoolAssignRequest,
    PoolBatchDeleteData,
    PoolBatchDeleteRequest,
    PoolClaimData,
    PoolClaimRequest,
    PoolDeleteData,
    PoolListData,
    PoolTransferListData,
)

pool_service = importlib.import_module("app.services.pool_service")

router = APIRouter(prefix="/pool", tags=["public-pool"])


@router.get("/leads", response_model=ApiEnvelope[PoolListData])
async def get_pool_leads(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    drop_reason: str | None = Query(default=None),
    previous_owner: str | None = Query(default=None),
) -> dict[str, Any]:
    data = await pool_service.list_pool_leads(
        session=db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        drop_reason=drop_reason,
        previous_owner=previous_owner,
    )
    return success_response(data=data, message="操作成功")


@router.post("/leads/{lead_id}/claim", response_model=ApiEnvelope[PoolClaimData])
async def claim_pool_lead(
    lead_id: str,
    payload: PoolClaimRequest,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(get_current_staff),
    _: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    staff_id = payload.staff_id or current_staff.get("staffId")
    data = await pool_service.claim_pool_lead(db, lead_id, staff_id)
    return success_response(data=data, message="操作成功")


@router.post("/leads/assign", response_model=ApiEnvelope[PoolAssignData])
async def assign_pool_leads(
    payload: PoolAssignRequest,
    db: AsyncSession = Depends(get_db_session),
    current_staff: dict[str, Any] = Depends(require_roles("admin", "manager")),
) -> dict[str, Any]:
    data = await pool_service.assign_pool_leads(
        db,
        payload.lead_ids,
        payload.staff_id,
        operator_staff_id=str(current_staff.get("staffId", "system")),
    )
    return success_response(data=data, message="操作成功")


@router.get("/transfers", response_model=ApiEnvelope[PoolTransferListData])
async def get_pool_transfers(
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    lead_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    _: dict[str, Any] = Depends(require_roles("admin", "manager")),
) -> dict[str, Any]:
    data = await pool_service.list_pool_transfers(
        session=db,
        page=page,
        page_size=page_size,
        lead_id=lead_id,
        action=action,
    )
    return success_response(data=data, message="操作成功")


@router.delete("/leads/{lead_id}", response_model=ApiEnvelope[PoolDeleteData])
async def delete_pool_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await pool_service.delete_pool_lead(db, lead_id)
    return success_response(data=data, message="操作成功")


@router.post("/leads/delete-batch", response_model=ApiEnvelope[PoolBatchDeleteData])
async def delete_pool_leads_batch(
    payload: PoolBatchDeleteRequest,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await pool_service.delete_pool_leads_batch(db, payload.lead_ids)
    return success_response(data=data, message="操作成功")
