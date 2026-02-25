from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.lead import Lead
from app.models.pool_transfer_log import PoolTransferLog
from app.repositories import pool_repository


def _to_pool_item(lead: Lead) -> dict[str, Any]:
    meta = lead.dynamic_data or {}
    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "source": lead.source,
        "dropReasonType": meta.get("drop_reason_type", "超时未跟进"),
        "dropReasonDetail": meta.get("drop_reason_detail", "系统自动回收"),
        "dropTime": meta.get("drop_time")
        or (lead.updated_at.isoformat(sep=" ") if lead.updated_at else None),
        "originalOwner": meta.get("original_owner"),
    }


def _to_transfer_item(log: PoolTransferLog) -> dict[str, Any]:
    return {
        "id": log.id,
        "leadId": log.lead_id,
        "action": log.action,
        "fromOwnerId": log.from_owner_id,
        "toOwnerId": log.to_owner_id,
        "operatorStaffId": log.operator_staff_id,
        "note": log.note,
        "createdAt": log.created_at.isoformat(sep=" "),
    }


async def list_pool_leads(
    *,
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    drop_reason: str | None = None,
    previous_owner: str | None = None,
) -> dict[str, Any]:
    base_query = pool_repository.build_pool_query(
        keyword=keyword,
        drop_reason=drop_reason,
        previous_owner=previous_owner,
    )
    total = await pool_repository.count_pool_leads(session, base_query)
    leads = await pool_repository.list_pool_leads(session, base_query, page, page_size)

    return {
        "list": [_to_pool_item(lead) for lead in leads],
        "total": int(total or 0),
    }


async def claim_pool_lead(session: AsyncSession, lead_id: str, staff_id: str) -> dict[str, Any]:
    lead = await pool_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    if lead.owner_id is not None:
        raise AppException("客户不在公海池", business_code=400, status_code=409)

    previous_owner_id = lead.owner_id
    lead.owner_id = staff_id
    pool_repository.add_transfer_log(
        session,
        PoolTransferLog(
            lead_id=lead_id,
            action="claim",
            from_owner_id=previous_owner_id,
            to_owner_id=staff_id,
            operator_staff_id=staff_id,
        note="销售捞取公海客户",
        ),
    )
    await pool_repository.commit(session)
    return {"leadId": lead.id, "claimer": staff_id}


async def assign_pool_leads(
    session: AsyncSession,
    lead_ids: list[str],
    staff_id: str,
    operator_staff_id: str = "system",
) -> dict[str, Any]:
    claimed_ids: list[str] = []
    for lead_id in lead_ids:
        lead = await pool_repository.get_lead(session, lead_id)
        if lead is None or lead.owner_id is not None:
            continue
        previous_owner_id = lead.owner_id
        lead.owner_id = staff_id
        pool_repository.add_transfer_log(
            session,
            PoolTransferLog(
                lead_id=lead_id,
                action="assign",
                from_owner_id=previous_owner_id,
                to_owner_id=staff_id,
                operator_staff_id=operator_staff_id,
                note="管理员批量分配",
            ),
        )
        claimed_ids.append(lead_id)

    await pool_repository.commit(session)
    return {
        "leadIds": claimed_ids,
        "assignee": staff_id,
        "count": len(claimed_ids),
    }


async def list_pool_transfers(
    *,
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    lead_id: str | None = None,
    action: str | None = None,
) -> dict[str, Any]:
    base_query = pool_repository.build_transfer_query(lead_id=lead_id, action=action)
    total = await pool_repository.count_transfer_logs(session, base_query)
    logs = await pool_repository.list_transfer_logs(session, base_query, page, page_size)
    return {
        "list": [_to_transfer_item(log) for log in logs],
        "total": total,
    }


async def delete_pool_lead(session: AsyncSession, lead_id: str) -> dict[str, Any]:
    lead = await pool_repository.get_lead(session, lead_id)
    if lead is None:
        raise AppException("客户不存在", business_code=400, status_code=404)
    if lead.owner_id is not None:
        raise AppException("客户不在公海池", business_code=400, status_code=409)

    await pool_repository.delete_follow_ups_by_lead(session, lead_id)
    await pool_repository.delete_lead(session, lead)
    await pool_repository.commit(session)
    return {"leadId": lead_id}


async def delete_pool_leads_batch(session: AsyncSession, lead_ids: list[str]) -> dict[str, Any]:
    leads = await pool_repository.list_leads_by_ids(session, lead_ids)
    lead_map = {lead.id: lead for lead in leads}
    deleted_ids: list[str] = []
    for lead_id in lead_ids:
        lead = lead_map.get(lead_id)
        if lead is None:
            continue
        if lead.owner_id is not None:
            continue
        await pool_repository.delete_follow_ups_by_lead(session, lead_id)
        await pool_repository.delete_lead(session, lead)
        deleted_ids.append(lead_id)

    await pool_repository.commit(session)
    return {
        "leadIds": deleted_ids,
        "count": len(deleted_ids),
    }
