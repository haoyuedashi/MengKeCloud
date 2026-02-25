from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow_up_record import FollowUpRecord
from app.models.department import Department
from app.models.lead import Lead
from app.models.user import User
from app.repositories import reports_repository
from app.core.rbac import normalize_role


def _month_range(now_utc: datetime) -> tuple[datetime, datetime, datetime, datetime]:
    month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = month_start
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    return month_start, now_utc, prev_month_start, prev_month_end


def _parse_iso_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _resolve_current_period(
    now_utc: datetime,
    start_date: str | None,
    end_date: str | None,
) -> tuple[datetime, datetime]:
    if start_date and end_date:
        start_at = _parse_iso_date(start_date)
        end_at = _parse_iso_date(end_date) + timedelta(days=1)
        if end_at <= start_at:
            return _month_range(now_utc)[:2]
        return start_at, end_at
    return _month_range(now_utc)[:2]


def _previous_period(start_at: datetime, end_at: datetime) -> tuple[datetime, datetime]:
    delta = end_at - start_at
    prev_end = start_at
    prev_start = prev_end - delta
    return prev_start, prev_end


def _compute_trend(current: int, previous: int) -> float:
    if previous <= 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def _is_signed(status: str) -> bool:
    return status in {"signed", "已签约"}


def _is_invited_or_visited(status: str) -> bool:
    return status in {"invited", "visited", "已邀约", "已到访"}


def _is_invited(status: str) -> bool:
    return status in {"invited", "已邀约"}


def _is_visited(status: str) -> bool:
    return status in {"visited", "已到访"}


def _is_lost(status: str) -> bool:
    return status in {"lost", "战败流失", "无效线索", "无效客户", "invalid"}


def _lead_loss_reason(lead: Lead) -> str:
    meta = lead.dynamic_data or {}
    return (
        str(meta.get("loss_reason") or "").strip()
        or str(meta.get("drop_reason_type") or "").strip()
        or "其他原因"
    )


def _normalize_dept_name(name: str | None) -> str:
    return (name or "").strip()


def _build_department_filters(
    departments: list[Department],
    allowed_names: set[str] | None = None,
) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    seen: set[str] = set()

    for department in departments:
        dept_name = _normalize_dept_name(department.name)
        if not dept_name or dept_name in seen:
            continue
        if allowed_names is not None and dept_name not in allowed_names:
            continue
        seen.add(dept_name)
        options.append({"label": dept_name, "value": dept_name})

    return options


def _build_trend_series(leads: list[Lead], now_utc: datetime, trend_window: str) -> dict[str, Any]:
    days = 7 if trend_window == "7days" else 30
    start_day = (now_utc - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count: dict[str, int] = {}
    for offset in range(days):
        day = start_day + timedelta(days=offset)
        key = day.strftime("%m-%d")
        daily_count[key] = 0

    for lead in leads:
        if not lead.created_at:
            continue
        key = lead.created_at.astimezone(timezone.utc).strftime("%m-%d")
        if key in daily_count:
            daily_count[key] += 1

    x_axis = list(daily_count.keys())
    series = [daily_count[key] for key in x_axis]
    return {"window": trend_window, "xAxis": x_axis, "series": series}


def _build_funnel(month_leads: list[Lead], month_followups: list[FollowUpRecord]) -> list[dict[str, Any]]:
    followed_ids = {record.lead_id for record in month_followups}
    interested_ids = {
        lead.id for lead in month_leads if lead.level in {"A", "B", "A级 (近期可成交)", "B级 (持续跟进)"}
    }
    invited_ids = {lead.id for lead in month_leads if _is_invited_or_visited(lead.status)}
    signed_ids = {lead.id for lead in month_leads if _is_signed(lead.status)}

    return [
        {"name": "新增客户", "value": len(month_leads)},
        {"name": "初次建联", "value": len(followed_ids)},
        {"name": "产生意向", "value": len(interested_ids)},
        {"name": "邀约看铺/探店", "value": len(invited_ids)},
        {"name": "成功签约", "value": len(signed_ids)},
    ]


def _build_loss_distribution(month_leads: list[Lead]) -> list[dict[str, Any]]:
    counter: dict[str, int] = {}
    for lead in month_leads:
        if not _is_lost(lead.status):
            continue
        reason = _lead_loss_reason(lead)
        counter[reason] = counter.get(reason, 0) + 1

    if not counter:
        return [{"name": "暂无战败数据", "value": 0}]

    items = sorted(counter.items(), key=lambda item: item[1], reverse=True)
    return [{"name": name, "value": value} for name, value in items[:8]]


def _build_staff_ranking(month_leads: list[Lead], month_followups: list[FollowUpRecord], users: list[User]) -> list[dict[str, Any]]:
    by_owner: dict[str, dict[str, int]] = {}
    user_map = {user.id: user for user in users}
    operator_to_user: dict[str, str] = {}
    for user in users:
        operator_to_user[user.name] = user.id
        operator_to_user[user.id] = user.id

    for lead in month_leads:
        owner_id = lead.owner_id
        if not owner_id:
            continue
        if owner_id not in by_owner:
            by_owner[owner_id] = {"newLeads": 0, "signed": 0, "followUps": 0}
        by_owner[owner_id]["newLeads"] += 1
        if _is_signed(lead.status):
            by_owner[owner_id]["signed"] += 1

    for record in month_followups:
        owner_id = operator_to_user.get(record.operator)
        if not owner_id:
            continue
        if owner_id not in by_owner:
            by_owner[owner_id] = {"newLeads": 0, "signed": 0, "followUps": 0}
        by_owner[owner_id]["followUps"] += 1

    ranking: list[dict[str, Any]] = []
    for owner_id, values in by_owner.items():
        user = user_map.get(owner_id)
        if user is None:
            continue
        new_leads = values["newLeads"]
        signed = values["signed"]
        conversion = round((signed / new_leads) * 100, 1) if new_leads > 0 else 0.0
        ranking.append(
            {
                "staffId": owner_id,
                "name": user.name,
                "newLeads": new_leads,
                "followUps": values["followUps"],
                "signed": signed,
                "conversion": conversion,
            }
        )

    ranking.sort(key=lambda item: (item["signed"], item["followUps"], item["newLeads"]), reverse=True)
    return ranking[:10]


def _to_percent(current: int, target: int) -> int:
    if target <= 0:
        return 0
    value = int(round((current / target) * 100))
    return max(0, min(100, value))


async def get_reports_overview(
    session: AsyncSession,
    trend_window: str,
    start_date: str | None,
    end_date: str | None,
    dept_name: str | None,
    owner_id: str | None,
    current_staff: dict[str, Any],
) -> dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    month_start, month_end = _resolve_current_period(now_utc, start_date, end_date)
    prev_month_start, prev_month_end = _previous_period(month_start, month_end)
    trend_days = 7 if trend_window == "7days" else 30
    trend_start = (now_utc - timedelta(days=trend_days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    role = normalize_role(str(current_staff.get("role") or ""))
    actor_staff_id = str(current_staff.get("staffId") or "")

    users = await reports_repository.list_active_users(session)
    if role == "sales":
        users = [user for user in users if user.id == actor_staff_id]
        owner_id = actor_staff_id
        dept_name = None
    elif role == "manager":
        actor = next((user for user in users if user.id == actor_staff_id), None)
        actor_dept = actor.dept_name if actor else None
        if not actor_dept:
            return {
                "summary": {
                    "newLeads": {"value": 0, "trend": 0.0},
                    "assignedLeads": {"value": 0, "trend": 0.0},
                    "followUps": {"value": 0, "trend": 0.0},
                    "signedLeads": {"value": 0, "trend": 0.0},
                },
                "trend": {"window": trend_window, "xAxis": [], "series": []},
                "funnel": [],
                "loss": [],
                "staffRanking": [],
                "filtersMeta": {"departments": [], "staffs": []},
            }
        dept_name = actor_dept
        owner_id = None
    departments = await reports_repository.list_active_departments(session)
    department_scope: set[str] | None = None
    if role == "manager" and dept_name:
        department_scope = {dept_name}
    if role == "sales":
        current_user = next((user for user in users if user.id == actor_staff_id), None)
        if current_user and current_user.dept_name:
            department_scope = {_normalize_dept_name(current_user.dept_name)}
    filtered_users = users
    if dept_name:
        filtered_users = [user for user in filtered_users if user.dept_name == dept_name]
    if owner_id:
        filtered_users = [user for user in filtered_users if user.id == owner_id]
    operator_keys = list({key for user in filtered_users for key in (user.name, user.id)})

    query_owner_id = owner_id
    query_dept_name = dept_name
    if owner_id:
        query_dept_name = None

    month_leads = await reports_repository.list_leads_between(
        session,
        start_at=month_start,
        end_at=month_end,
        owner_id=query_owner_id,
        dept_name=query_dept_name,
    )
    prev_month_leads = await reports_repository.list_leads_between(
        session,
        start_at=prev_month_start,
        end_at=prev_month_end,
        owner_id=query_owner_id,
        dept_name=query_dept_name,
    )
    month_followups = await reports_repository.list_followups_between(
        session,
        start_at=month_start,
        end_at=month_end,
        operator_keys=operator_keys,
    )
    prev_month_followups = await reports_repository.list_followups_between(
        session,
        start_at=prev_month_start,
        end_at=prev_month_end,
        operator_keys=operator_keys,
    )
    trend_leads = await reports_repository.list_leads_between(
        session,
        start_at=trend_start,
        end_at=month_end,
        owner_id=query_owner_id,
        dept_name=query_dept_name,
    )

    current_new = len(month_leads)
    previous_new = len(prev_month_leads)

    current_assigned = sum(1 for lead in month_leads if lead.owner_id)
    previous_assigned = sum(1 for lead in prev_month_leads if lead.owner_id)

    current_followups = len(month_followups)
    previous_followups = len(prev_month_followups)

    current_signed = sum(1 for lead in month_leads if _is_signed(lead.status))
    previous_signed = sum(1 for lead in prev_month_leads if _is_signed(lead.status))

    current_invited = sum(1 for lead in month_leads if _is_invited(lead.status))
    previous_invited = sum(1 for lead in prev_month_leads if _is_invited(lead.status))
    current_visited = sum(1 for lead in month_leads if _is_visited(lead.status))
    previous_visited = sum(1 for lead in prev_month_leads if _is_visited(lead.status))

    current_invitation_rate = int(round((current_invited / current_new) * 100)) if current_new > 0 else 0
    previous_invitation_rate = int(round((previous_invited / previous_new) * 100)) if previous_new > 0 else 0
    current_visit_rate = int(round((current_visited / current_new) * 100)) if current_new > 0 else 0
    previous_visit_rate = int(round((previous_visited / previous_new) * 100)) if previous_new > 0 else 0

    personal_goal: dict[str, Any] | None = None
    if role == "sales":
        sales_user = next((user for user in users if user.id == actor_staff_id), None)
        signed_target = int(sales_user.monthly_target) if sales_user is not None else 0
        if signed_target <= 0:
            signed_target = 10
        personal_goal = {
            "signedCurrent": current_signed,
            "signedTarget": signed_target,
            "signedPercent": _to_percent(current_signed, signed_target),
        }

    return {
        "summary": {
            "newLeads": {"value": current_new, "trend": _compute_trend(current_new, previous_new)},
            "assignedLeads": {
                "value": current_assigned,
                "trend": _compute_trend(current_assigned, previous_assigned),
            },
            "followUps": {
                "value": current_followups,
                "trend": _compute_trend(current_followups, previous_followups),
            },
            "signedLeads": {
                "value": current_signed,
                "trend": _compute_trend(current_signed, previous_signed),
            },
            "invitationRate": {
                "value": current_invitation_rate,
                "trend": _compute_trend(current_invitation_rate, previous_invitation_rate),
            },
            "visitRate": {
                "value": current_visit_rate,
                "trend": _compute_trend(current_visit_rate, previous_visit_rate),
            },
        },
        "trend": _build_trend_series(trend_leads, now_utc, trend_window),
        "funnel": _build_funnel(month_leads, month_followups),
        "loss": _build_loss_distribution(month_leads),
        "staffRanking": _build_staff_ranking(month_leads, month_followups, filtered_users),
        "filtersMeta": {
            "departments": _build_department_filters(departments, department_scope),
            "staffs": [
                {"label": user.name, "value": user.id}
                for user in filtered_users
            ],
        },
        "personalGoal": personal_goal,
    }
