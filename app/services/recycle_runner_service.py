import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.pool_transfer_log import PoolTransferLog
from app.repositories import notification_repository, recycle_repository
from app.services import settings_service


SIGNED_STATUSES = {"signed", "已签约", "invalid", "无效线索", "无效客户", "lost", "战败流失"}


@dataclass(slots=True)
class RecycleResult:
    recycled_count: int
    before_notified_count: int
    after_notified_count: int


def _normalize_level(value: str | None) -> str:
    return str(value or "").strip().upper()


def _build_event_key(prefix: str, lead_id: str, owner_id: str, date_key: str) -> str:
    return f"{prefix}:{lead_id}:{owner_id}:{date_key}"


async def _push_notification_once(
    session: AsyncSession,
    *,
    staff_id: str,
    title: str,
    content: str,
    category: str,
    event_key: str,
) -> bool:
    return await notification_repository.insert_notification_if_absent(
        session,
        staff_id=staff_id,
        title=title,
        content=content,
        category=category,
        event_key=event_key,
    )


async def run_recycle_once() -> RecycleResult:
    async with AsyncSessionLocal() as session:
        rules = await settings_service.get_recycle_rules(session)
        if not rules.get("enabled"):
            return RecycleResult(recycled_count=0, before_notified_count=0, after_notified_count=0)

        leads = await recycle_repository.list_assigned_leads(session)
        now_utc = datetime.now(timezone.utc)

        recycled = 0
        before_notified = 0
        after_notified = 0

        for lead in leads:
            if str(lead.status or "") in SIGNED_STATUSES:
                continue
            if not lead.owner_id:
                continue

            owner = await recycle_repository.get_user(session, lead.owner_id)
            if owner is None:
                continue

            followups = await recycle_repository.list_followups_for_lead(session, lead.id)
            followup_count = len(followups)
            owner_operator_keys = {owner.id, owner.name}
            owner_followup_count = sum(1 for item in followups if item.operator in owner_operator_keys)

            reason_text: str | None = None
            date_key = now_utc.strftime("%Y-%m-%d")

            # Rule 1: assigned but no follow-up in N days
            if rules["rule1"]["active"] and followup_count == 0:
                days = int(rules["rule1"]["days"] or 1)
                assigned_at = lead.created_at or lead.updated_at
                gap_days = (now_utc - assigned_at.astimezone(timezone.utc)).days
                if rules["notify"]["beforeDrop"] and gap_days == max(0, days - 1):
                    ok = await _push_notification_once(
                        session,
                        staff_id=owner.id,
            title="客户即将自动回收",
            content=f"客户 {lead.id} 将在 1 天后因未跟进被回收至公海，请及时处理。",
                        category="recycle_warning",
                        event_key=_build_event_key("before_rule1", lead.id, owner.id, date_key),
                    )
                    if ok:
                        before_notified += 1
                if gap_days >= days:
                    reason_text = "分配后未及时跟进"

            # Rule 2: no contact for N days after follow-up
            if reason_text is None and rules["rule2"]["active"] and lead.last_follow_up is not None:
                days = int(rules["rule2"]["days"] or 1)
                gap_days = (now_utc - lead.last_follow_up.astimezone(timezone.utc)).days
                is_high_intent = _normalize_level(lead.level).startswith("A")
                if rules["rule2"].get("protectHighIntent") and is_high_intent:
                    gap_days = -1
                if rules["notify"]["beforeDrop"] and gap_days == max(0, days - 1):
                    ok = await _push_notification_once(
                        session,
                        staff_id=owner.id,
            title="客户即将自动回收",
            content=f"客户 {lead.id} 将在 1 天后因长时间未联系被回收至公海。",
                        category="recycle_warning",
                        event_key=_build_event_key("before_rule2", lead.id, owner.id, date_key),
                    )
                    if ok:
                        before_notified += 1
                if gap_days >= days:
                    reason_text = "跟进后长时间无联系"

            # Rule 3: too many follow-ups but no deal
            if reason_text is None and rules["rule3"]["active"]:
                count_limit = int(rules["rule3"]["count"] or 1)
                if owner_followup_count >= count_limit:
                    reason_text = "久攻不下死单"

            if reason_text is None:
                continue

            old_owner_id = lead.owner_id
            lead.owner_id = None
            meta = dict(lead.dynamic_data or {})
            meta["drop_reason_type"] = reason_text
            meta["drop_reason_detail"] = "系统自动回收"
            meta["drop_time"] = now_utc.isoformat()
            meta["original_owner"] = owner.name
            lead.dynamic_data = meta

            recycle_repository.add_pool_transfer_log(
                session,
                PoolTransferLog(
                    lead_id=lead.id,
                    action="auto_recycle",
                    from_owner_id=old_owner_id,
                    to_owner_id=None,
                    operator_staff_id="system",
                    note=f"自动回收: {reason_text}",
                ),
            )
            recycled += 1

            if rules["notify"]["afterDrop"]:
                supervisors = await recycle_repository.list_active_supervisors(session)
                for manager in supervisors:
                    ok = await _push_notification_once(
                        session,
                        staff_id=manager.id,
            title="客户已自动回收",
            content=f"客户 {lead.id} 已从 {owner.name} 处回收到公海，原因：{reason_text}。",
                        category="recycle_summary",
                        event_key=_build_event_key("after_drop", lead.id, manager.id, date_key),
                    )
                    if ok:
                        after_notified += 1

        await recycle_repository.commit(session)
        return RecycleResult(
            recycled_count=recycled,
            before_notified_count=before_notified,
            after_notified_count=after_notified,
        )


async def recycle_worker_loop(stop_event: asyncio.Event) -> None:
    last_run_date: str | None = None
    while not stop_event.is_set():
        try:
            now = datetime.now(timezone.utc).astimezone()
            date_key = now.strftime("%Y-%m-%d")
            if now.hour == 0 and now.minute < 10 and last_run_date != date_key:
                _ = await run_recycle_once()
                last_run_date = date_key
        except Exception:
            # Worker must keep running even if one cycle fails.
            pass
        await asyncio.sleep(60)
