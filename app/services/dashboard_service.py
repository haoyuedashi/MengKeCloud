from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import normalize_role
from app.models.lead import Lead
from app.repositories import dashboard_repository, settings_repository


def _compute_trend(current: int, previous: int) -> float:
    if previous <= 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def _summary_from_lead(lead: Lead) -> str:
    meta = lead.dynamic_data or {}
    return str(meta.get("next_action") or "请尽快联系客户并完善本次跟进记录")


def _days_overdue(lead: Lead, now_utc: datetime) -> int:
    drop_time_raw = (lead.dynamic_data or {}).get("drop_time")
    if isinstance(drop_time_raw, str):
        try:
            drop_time = datetime.fromisoformat(drop_time_raw.replace("Z", "+00:00"))
            return max(0, (now_utc - drop_time.astimezone(timezone.utc)).days)
        except ValueError:
            pass
    if lead.updated_at:
        return max(0, (now_utc - lead.updated_at.astimezone(timezone.utc)).days)
    return 0


def _to_percent(current: int, target: int) -> int:
    if target <= 0:
        return 0
    return max(0, min(100, int(round((current / target) * 100))))


async def get_dashboard_overview(session: AsyncSession, current_staff: dict[str, Any]) -> dict[str, Any]:
    now_utc = datetime.now(timezone.utc)

    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    week_start = (today_start - timedelta(days=today_start.weekday()))
    prev_week_start = week_start - timedelta(days=7)

    month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = month_start
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    staff_id = str(current_staff.get("staffId") or "")
    staff_role = normalize_role(str(current_staff.get("role") or ""))
    staff_user = await dashboard_repository.get_user(session, staff_id) if staff_id else None

    scope_owner_id: str | None = None
    scope_dept_name: str | None = None
    operator_keys: list[str] | None = None

    if staff_role == "sales":
        scope_owner_id = staff_id or None
        if staff_user is not None:
            operator_keys = [staff_user.id, staff_user.name]
    elif staff_role == "manager" and staff_user is not None and staff_user.dept_name:
        scope_dept_name = staff_user.dept_name
        operator_keys = [staff_user.name]

    today_new = await dashboard_repository.count_leads_between(
        session,
        start_at=today_start,
        end_at=now_utc,
        owner_id=scope_owner_id,
        dept_name=scope_dept_name,
    )
    yesterday_new = await dashboard_repository.count_leads_between(
        session,
        start_at=yesterday_start,
        end_at=today_start,
        owner_id=scope_owner_id,
        dept_name=scope_dept_name,
    )

    week_followups = await dashboard_repository.count_followups_between(
        session,
        start_at=week_start,
        end_at=now_utc,
        operator_keys=operator_keys,
    )
    prev_week_followups = await dashboard_repository.count_followups_between(
        session,
        start_at=prev_week_start,
        end_at=week_start,
        operator_keys=operator_keys,
    )

    month_signed = await dashboard_repository.count_signed_leads_between(
        session,
        start_at=month_start,
        end_at=now_utc,
        owner_id=scope_owner_id,
        dept_name=scope_dept_name,
    )
    prev_month_signed = await dashboard_repository.count_signed_leads_between(
        session,
        start_at=prev_month_start,
        end_at=prev_month_end,
        owner_id=scope_owner_id,
        dept_name=scope_dept_name,
    )

    todo_leads = await dashboard_repository.list_todo_leads(
        session,
        limit=4,
        owner_id=scope_owner_id,
        dept_name=scope_dept_name,
    )
    pool_leads = await dashboard_repository.list_pool_warning_leads(
        session,
        limit=2,
        owner_id=scope_owner_id,
        dept_name=scope_dept_name,
    )

    platform = await dashboard_repository.get_platform_setting(session)
    followup_target = int(platform.max_leads_per_rep) if platform else 200
    signed_target = int((platform.annual_target / 12)) if platform and platform.annual_target > 0 else 10
    announcement = (platform.announcement or "").strip() if platform else ""

    personal_signed_target = int(staff_user.monthly_target) if staff_user is not None else 0
    personal_signed_current = await dashboard_repository.count_signed_leads_between(
        session,
        start_at=month_start,
        end_at=now_utc,
        owner_id=staff_id or None,
    )

    department_signed_target = 0
    department_signed_current = 0
    if staff_user is not None and staff_user.dept_name:
        if staff_role in {"admin", "manager"}:
            department_signed_current = await dashboard_repository.count_signed_leads_between(
                session,
                start_at=month_start,
                end_at=now_utc,
                dept_name=staff_user.dept_name,
            )
            department = await settings_repository.get_department_by_name(session, staff_user.dept_name)
            if department is not None:
                department_signed_target = int(department.monthly_target)

    if staff_role == "sales":
        if personal_signed_target > 0:
            signed_target = personal_signed_target
        elif signed_target <= 0:
            signed_target = 10

    return {
        "stats": {
            "todayNewLeads": {"value": today_new, "trend": _compute_trend(today_new, yesterday_new)},
            "weekFollowUps": {"value": week_followups, "trend": _compute_trend(week_followups, prev_week_followups)},
            "monthSigned": {"value": month_signed, "trend": _compute_trend(month_signed, prev_month_signed)},
        },
        "todoList": [
            {
                "leadId": lead.id,
                "name": lead.name,
                "level": lead.level,
                "summary": _summary_from_lead(lead),
            }
            for lead in todo_leads
        ],
        "poolWarnings": [
            {
                "leadId": lead.id,
                "name": lead.name,
                "daysOverdue": _days_overdue(lead, now_utc),
            }
            for lead in pool_leads
        ],
        "performance": {
            "followUp": {
                "current": week_followups,
                "target": followup_target,
                "percent": _to_percent(week_followups, followup_target),
            },
            "signed": {
                "current": month_signed,
                "target": signed_target,
                "percent": _to_percent(month_signed, signed_target),
            },
            "personalSigned": {
                "current": personal_signed_current,
                "target": personal_signed_target,
                "percent": _to_percent(personal_signed_current, personal_signed_target),
            },
            "departmentSigned": {
                "current": department_signed_current,
                "target": department_signed_target,
                "percent": _to_percent(department_signed_current, department_signed_target),
            },
        },
        "announcement": announcement,
    }
