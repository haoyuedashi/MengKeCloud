from typing import Any
from datetime import datetime, timezone
import json
import time
import urllib.error
import urllib.request

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.custom_field import CustomField
from app.models.department import Department
from app.models.dict_item import DictItem
from app.models.platform_setting import PlatformSetting
from app.models.recycle_rule import RecycleRule
from app.models.system_role import SystemRole
from app.models.user import User
from app.repositories import settings_repository
from app.services.auth_security_service import hash_password, is_weak_password
from app.core.rbac import normalize_role, CANONICAL_ROLES
from app.schemas.settings import (
    CustomFieldCreate,
    CustomFieldUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    DictItemManageCreate,
    DictItemManageUpdate,
    OrgUserCreate,
    OrgUserUpdate,
    PlatformSettingsUpdate,
    PlatformAiTestRequest,
    RecycleRulesUpdate,
    RoleCreate,
    RoleUpdate,
)

DICT_TYPES: list[dict[str, str]] = [
    {"code": "lead_status", "name": "客户跟进状态"},
    {"code": "lead_level", "name": "客户意向评级"},
    {"code": "lead_source", "name": "客户来源渠道"},
    {"code": "lead_tag", "name": "客户标签"},
    {"code": "loss_reason", "name": "战败流失原因"},
]

ROLE_MENU_TREE: list[dict[str, Any]] = [
    {"id": 1, "children": [{"id": 11}]},
    {"id": 2, "children": [{"id": 21}, {"id": 22}]},
    {"id": 3, "children": [{"id": 31}, {"id": 32}, {"id": 33}]},
    {"id": 4, "children": [{"id": 41}]},
    {"id": 5, "children": [{"id": 51}, {"id": 52}, {"id": 53}, {"id": 54}, {"id": 55}]},
]


def _collect_menu_ids(nodes: list[dict[str, Any]]) -> set[int]:
    ids: set[int] = set()
    for node in nodes:
        ids.add(int(node["id"]))
        children = node.get("children") or []
        if children:
            ids.update(_collect_menu_ids(children))
    return ids


ALLOWED_MENU_IDS = _collect_menu_ids(ROLE_MENU_TREE)


def normalize_menu_keys(keys: list[int] | None) -> list[int]:
    raw = keys or []
    normalized = sorted({int(item) for item in raw if int(item) in ALLOWED_MENU_IDS})
    return normalized

REQUIRED_LEAD_STATUS_ITEMS: list[dict[str, Any]] = [
    {"value": "pending", "label": "待跟进", "color": "#9ca3af", "sort": 1},
    {"value": "communicating", "label": "初步沟通", "color": "#3b82f6", "sort": 2},
    {"value": "deep_following", "label": "深度跟进", "color": "#2563eb", "sort": 3},
    {"value": "invited", "label": "已邀约", "color": "#6366f1", "sort": 4},
    {"value": "visited", "label": "已到访", "color": "#4f46e5", "sort": 5},
    {"value": "deposit_paid", "label": "已交定金", "color": "#06b6d4", "sort": 6},
    {"value": "signed", "label": "已签约", "color": "#10b981", "sort": 7},
    {"value": "invalid", "label": "无效客户", "color": "#64748b", "sort": 8},
    {"value": "lost", "label": "战败流失", "color": "#ef4444", "sort": 9},
]


async def _cleanup_duplicate_dict_items(session: AsyncSession, dict_type: str) -> None:
    rows = await settings_repository.list_dict_items(session, dict_type)
    if not rows:
        return

    grouped: dict[str, list[DictItem]] = {}
    for row in rows:
        grouped.setdefault(row.item_key, []).append(row)

    changed = False
    for same_key_rows in grouped.values():
        if len(same_key_rows) <= 1:
            continue

        same_key_rows.sort(
            key=lambda item: (
                not item.is_system,
                not item.enabled,
                item.sort_order,
                item.id,
            )
        )
        keeper = same_key_rows[0]
        for duplicate in same_key_rows[1:]:
            if duplicate.id == keeper.id:
                continue
            await settings_repository.delete_dict_item(session, duplicate)
            changed = True

    remaining_rows = await settings_repository.list_dict_items(session, dict_type)
    for index, item in enumerate(remaining_rows, start=1):
        if item.sort_order != index:
            item.sort_order = index
            changed = True

    if changed:
        await settings_repository.commit(session)


async def _ensure_required_lead_status_items(session: AsyncSession) -> None:
    rows = await settings_repository.list_dict_items(session, "lead_status")
    existing_by_key = {row.item_key: row for row in rows}
    changed = False

    for required in REQUIRED_LEAD_STATUS_ITEMS:
        key = required["value"]
        row = existing_by_key.get(key)
        if row is None:
            settings_repository.add_dict_item(
                session,
                DictItem(
                    dict_type="lead_status",
                    item_key=key,
                    item_label=required["label"],
                    color=required["color"],
                    sort_order=required["sort"],
                    enabled=True,
                    is_system=True,
                ),
            )
            changed = True
            continue

        if row.is_system is False:
            row.is_system = True
            changed = True

    if changed:
        await settings_repository.commit(session)


def _platform_to_dict(entity: PlatformSetting) -> dict[str, Any]:
    monthly_targets = entity.monthly_targets or []
    if len(monthly_targets) != 12:
        monthly_targets = [0] * 12
    masked_key = ""
    if entity.ai_api_key:
        masked_key = f"***{entity.ai_api_key[-4:]}" if len(entity.ai_api_key) >= 4 else "***"
    return {
        "companyName": entity.company_name,
        "officialPhone": entity.official_phone,
        "announcement": entity.announcement,
        "annualTarget": entity.annual_target,
        "monthlyTargets": monthly_targets,
        "maxLeadsPerRep": entity.max_leads_per_rep,
        "globalDropWarningDays": entity.global_drop_warning_days,
        "aiEnabled": entity.ai_enabled,
        "aiApiKeyMasked": masked_key,
        "aiBaseUrl": entity.ai_base_url,
        "aiModel": entity.ai_model,
        "aiTimeoutSeconds": entity.ai_timeout_seconds,
    }


async def _ensure_platform_setting(session: AsyncSession) -> PlatformSetting:
    entity = await settings_repository.get_platform_setting(session)
    if entity is not None:
        return entity

    entity = PlatformSetting(
        company_name="梦客云技术有限公司",
        official_phone="400-888-8888",
        announcement="",
        annual_target=120,
        monthly_targets=[10] * 12,
        max_leads_per_rep=300,
        global_drop_warning_days=3,
        ai_enabled=False,
        ai_api_key="",
        ai_base_url="https://api.openai.com/v1",
        ai_model="gpt-4o-mini",
        ai_timeout_seconds=12,
    )
    settings_repository.add_platform_setting(session, entity)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return entity


async def get_platform_settings(session: AsyncSession) -> dict[str, Any]:
    entity = await _ensure_platform_setting(session)
    return _platform_to_dict(entity)


async def update_platform_settings(session: AsyncSession, payload: PlatformSettingsUpdate) -> dict[str, Any]:
    entity = await _ensure_platform_setting(session)
    entity.company_name = payload.companyName
    entity.official_phone = payload.officialPhone
    entity.announcement = payload.announcement
    entity.annual_target = payload.annualTarget
    entity.monthly_targets = payload.monthlyTargets
    entity.max_leads_per_rep = payload.maxLeadsPerRep
    entity.global_drop_warning_days = payload.globalDropWarningDays
    entity.ai_enabled = payload.aiEnabled
    if payload.aiApiKey is not None:
        key = payload.aiApiKey.strip()
        if key:
            entity.ai_api_key = key
    entity.ai_base_url = payload.aiBaseUrl.strip() or "https://api.openai.com/v1"
    entity.ai_model = payload.aiModel.strip() or "gpt-4o-mini"
    entity.ai_timeout_seconds = payload.aiTimeoutSeconds

    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return _platform_to_dict(entity)


async def test_platform_ai_connection(session: AsyncSession, payload: PlatformAiTestRequest) -> dict[str, Any]:
    if not payload.aiEnabled:
        return {"ok": False, "message": "AI未开启，请先开启后测试", "latencyMs": 0, "model": payload.aiModel}
    api_key = (payload.aiApiKey or "").strip()
    if not api_key:
        entity = await _ensure_platform_setting(session)
        api_key = (entity.ai_api_key or "").strip()
    if not api_key:
        return {"ok": False, "message": "未配置模型 Key", "latencyMs": 0, "model": payload.aiModel}

    url = f"{payload.aiBaseUrl.rstrip('/')}/chat/completions"
    body = json.dumps(
        {
            "model": payload.aiModel,
            "messages": [{"role": "user", "content": "Return exactly: pong"}],
            "temperature": 0,
            "max_tokens": 8,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=payload.aiTimeoutSeconds) as resp:
            _ = resp.read().decode("utf-8")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"ok": True, "message": "模型连通成功", "latencyMs": latency_ms, "model": payload.aiModel}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "ok": False,
            "message": f"模型连通失败: {detail or exc.reason}",
            "latencyMs": latency_ms,
            "model": payload.aiModel,
        }
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "ok": False,
            "message": f"模型连通失败: {str(exc)}",
            "latencyMs": latency_ms,
            "model": payload.aiModel,
        }


def _department_to_dict(entity: Department, user_name_map: dict[str, str]) -> dict[str, Any]:
    return {
        "id": entity.id,
        "label": entity.name,
        "leaderStaffId": entity.leader_staff_id,
        "leaderName": user_name_map.get(entity.leader_staff_id),
        "parentId": entity.parent_id,
        "sortOrder": entity.sort_order,
        "active": entity.active,
        "monthlyTarget": entity.monthly_target,
    }


def _user_to_org_dict(entity: User, dept_map: dict[str, int]) -> dict[str, Any]:
    created_at = entity.created_at.isoformat(sep=" ") if entity.created_at else None
    return {
        "id": entity.id,
        "deptId": dept_map.get(entity.dept_name or ""),
        "name": entity.name,
        "phone": entity.phone,
        "role": entity.role,
        "active": entity.active,
        "joinDate": created_at,
        "monthlyTarget": entity.monthly_target,
    }


async def list_org_data(session: AsyncSession) -> dict[str, Any]:
    departments = await settings_repository.list_departments(session)
    users = await settings_repository.list_users(session)
    user_name_map = {user.id: user.name for user in users}
    dept_map = {department.name: department.id for department in departments}
    return {
        "departments": [_department_to_dict(item, user_name_map) for item in departments],
        "users": [_user_to_org_dict(item, dept_map) for item in users],
    }


async def create_department(session: AsyncSession, payload: DepartmentCreate) -> dict[str, Any]:
    leader = await settings_repository.get_user(session, payload.leaderStaffId)
    if leader is None:
        raise AppException("负责人不存在", business_code=400, status_code=404)
    if not leader.active:
        raise AppException("负责人账号已停用", business_code=400, status_code=400)

    if payload.parentId is not None:
        parent = await settings_repository.get_department(session, payload.parentId)
        if parent is None:
            raise AppException("父级部门不存在", business_code=400, status_code=404)

    entity = Department(
        name=payload.label,
        leader_staff_id=payload.leaderStaffId,
        parent_id=payload.parentId,
        sort_order=payload.sortOrder,
        active=payload.active,
        monthly_target=payload.monthlyTarget,
    )
    settings_repository.add_department(session, entity)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return _department_to_dict(entity, {leader.id: leader.name})


async def update_department(session: AsyncSession, department_id: int, payload: DepartmentUpdate) -> dict[str, Any]:
    entity = await settings_repository.get_department(session, department_id)
    if entity is None:
        raise AppException("部门不存在", business_code=400, status_code=404)

    if payload.parentId is not None and payload.parentId == department_id:
        raise AppException("部门不能挂载到自身", business_code=400, status_code=400)

    if payload.parentId is not None:
        parent = await settings_repository.get_department(session, payload.parentId)
        if parent is None:
            raise AppException("父级部门不存在", business_code=400, status_code=404)
        entity.parent_id = payload.parentId

    if payload.leaderStaffId is not None:
        leader = await settings_repository.get_user(session, payload.leaderStaffId)
        if leader is None:
            raise AppException("负责人不存在", business_code=400, status_code=404)
        if not leader.active:
            raise AppException("负责人账号已停用", business_code=400, status_code=400)
        entity.leader_staff_id = payload.leaderStaffId

    if payload.label is not None:
        old_name = entity.name
        entity.name = payload.label
        users = await settings_repository.list_users(session)
        for user in users:
            if user.dept_name == old_name:
                user.dept_name = payload.label
    if payload.sortOrder is not None:
        entity.sort_order = payload.sortOrder
    if payload.active is not None:
        entity.active = payload.active
    if payload.monthlyTarget is not None:
        entity.monthly_target = payload.monthlyTarget

    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    users = await settings_repository.list_users(session)
    user_name_map = {user.id: user.name for user in users}
    return _department_to_dict(entity, user_name_map)


async def delete_department(session: AsyncSession, department_id: int) -> None:
    entity = await settings_repository.get_department(session, department_id)
    if entity is None:
        raise AppException("部门不存在", business_code=400, status_code=404)

    children = await settings_repository.list_departments(session)
    if any(item.parent_id == department_id for item in children):
        raise AppException("请先删除或迁移子部门", business_code=400, status_code=400)

    users = await settings_repository.list_users(session)
    if any((user.dept_name or "") == entity.name for user in users):
        raise AppException("该部门下仍有员工，无法删除", business_code=400, status_code=400)

    await settings_repository.delete_department(session, entity)
    await settings_repository.commit(session)


async def _ensure_seed_roles(session: AsyncSession) -> None:
    roles = await settings_repository.list_roles(session)
    if roles:
        return

    defaults = [
        SystemRole(name="超级管理员 (老板)", is_system=True, menu_keys=[1, 11, 2, 21, 22, 3, 31, 4, 41, 5, 51, 52, 53, 54, 55], data_scope="all", active=True),
        SystemRole(name="销售主管", is_system=True, menu_keys=[1, 11, 2, 21, 22, 3, 31, 4, 41], data_scope="dept", active=True),
        SystemRole(name="普通销售", is_system=True, menu_keys=[1, 11, 2, 21, 22, 3, 31], data_scope="self", active=True),
    ]
    for role in defaults:
        settings_repository.add_role(session, role)
    await settings_repository.commit(session)


def _role_to_dict(entity: SystemRole) -> dict[str, Any]:
    return {
        "id": entity.id,
        "name": entity.name,
        "isSystem": entity.is_system,
        "menuKeys": normalize_menu_keys(entity.menu_keys),
        "dataScope": entity.data_scope,
        "active": entity.active,
    }


async def list_roles(session: AsyncSession) -> dict[str, Any]:
    await _ensure_seed_roles(session)
    roles = await settings_repository.list_roles(session)
    return {"list": [_role_to_dict(item) for item in roles]}


async def create_role(session: AsyncSession, payload: RoleCreate) -> dict[str, Any]:
    duplicated = await settings_repository.get_role_by_name(session, payload.name)
    if duplicated is not None:
        raise AppException("角色名称已存在", business_code=400, status_code=400)

    entity = SystemRole(
        name=payload.name,
        is_system=False,
        menu_keys=normalize_menu_keys(payload.menuKeys),
        data_scope=payload.dataScope,
        active=payload.active,
    )
    settings_repository.add_role(session, entity)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return _role_to_dict(entity)


async def update_role(session: AsyncSession, role_id: int, payload: RoleUpdate) -> dict[str, Any]:
    entity = await settings_repository.get_role(session, role_id)
    if entity is None:
        raise AppException("角色不存在", business_code=400, status_code=404)

    if payload.name is not None and payload.name != entity.name:
        duplicated = await settings_repository.get_role_by_name(session, payload.name)
        if duplicated is not None and duplicated.id != role_id:
            raise AppException("角色名称已存在", business_code=400, status_code=400)
        entity.name = payload.name
    if payload.menuKeys is not None:
        entity.menu_keys = normalize_menu_keys(payload.menuKeys)
    if payload.dataScope is not None:
        entity.data_scope = payload.dataScope
    if payload.active is not None:
        entity.active = payload.active

    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return _role_to_dict(entity)


async def delete_role(session: AsyncSession, role_id: int) -> None:
    entity = await settings_repository.get_role(session, role_id)
    if entity is None:
        raise AppException("角色不存在", business_code=400, status_code=404)
    if entity.is_system:
        raise AppException("系统内置角色无法删除", business_code=400, status_code=400)

    await settings_repository.delete_role(session, entity)
    await settings_repository.commit(session)


def _field_to_dict(entity: CustomField) -> dict[str, Any]:
    options = _normalize_field_options(entity.field_options)
    return {
        "id": entity.id,
        "name": entity.name,
        "code": entity.code,
        "type": entity.field_type,
        "placeholder": entity.placeholder,
        "isRequired": entity.is_required,
        "active": entity.active,
        "isSystem": entity.is_system,
        "sort": entity.sort_order,
        "fieldOptions": options,
    }


def _normalize_field_options(options: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    source = options or []
    normalized: list[dict[str, str]] = []
    seen_values: set[str] = set()
    for item in source:
        label = str(item.get("label", "")).strip()
        value = str(item.get("value", "")).strip()
        if not label or not value:
            continue
        if value in seen_values:
            continue
        seen_values.add(value)
        normalized.append({"label": label, "value": value})
    return normalized


async def _ensure_seed_custom_fields(session: AsyncSession, entity: str) -> None:
    if entity != "lead":
        return

    rows = await settings_repository.list_custom_fields(session, entity)
    existing_by_code = {row.code: row for row in rows}
    defaults = [
        {
            "name": "客户姓名",
            "code": "customer_name",
            "field_type": "text",
            "is_required": True,
            "active": True,
            "sort_order": 1,
        },
        {
            "name": "手机号码",
            "code": "phone",
            "field_type": "text",
            "is_required": True,
            "active": True,
            "sort_order": 2,
        },
        {
            "name": "意向评级",
            "code": "level",
            "field_type": "select",
            "is_required": False,
            "active": True,
            "sort_order": 3,
        },
        {
            "name": "来源渠道",
            "code": "source",
            "field_type": "select",
            "is_required": True,
            "active": True,
            "sort_order": 4,
        },
        {
            "name": "城市",
            "code": "city",
            "field_type": "text",
            "is_required": False,
            "active": True,
            "sort_order": 5,
        },
    ]

    changed = False
    for item in defaults:
        code = str(item["code"])
        name = str(item["name"])
        field_type = str(item["field_type"])
        is_required = bool(item["is_required"])
        active = bool(item["active"])
        sort_order = int(item["sort_order"])

        row = existing_by_code.get(code)
        if row is None:
            settings_repository.add_custom_field(
                session,
                CustomField(
                    entity="lead",
                    name=name,
                    code=code,
                    field_type=field_type,
                    is_required=is_required,
                    active=active,
                    is_system=True,
                    sort_order=sort_order,
                    field_options=[],
                ),
            )
            changed = True
            continue

        if row.is_system is False:
            row.is_system = True
            changed = True

    if changed:
        await settings_repository.commit(session)


async def list_custom_fields(session: AsyncSession, entity: str) -> dict[str, Any]:
    await _ensure_seed_custom_fields(session, entity)
    rows = await settings_repository.list_custom_fields(session, entity)
    return {"entity": entity, "list": [_field_to_dict(item) for item in rows]}


async def create_custom_field(session: AsyncSession, entity: str, payload: CustomFieldCreate) -> dict[str, Any]:
    duplicated = await settings_repository.get_custom_field_by_code(session, entity, payload.code)
    if duplicated is not None:
        raise AppException("字段编码已存在", business_code=400, status_code=400)

    sort_order = payload.sort
    if sort_order is None:
        sort_order = await settings_repository.get_custom_field_max_sort(session, entity) + 1

    row = CustomField(
        entity=entity,
        name=payload.name,
        code=payload.code,
        field_type=payload.type,
        placeholder=payload.placeholder,
        field_options=_normalize_field_options(payload.fieldOptions if payload.type == "select" else []),
        is_required=payload.isRequired,
        active=payload.active,
        is_system=False,
        sort_order=sort_order,
    )
    settings_repository.add_custom_field(session, row)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, row)
    return _field_to_dict(row)


async def update_custom_field(session: AsyncSession, field_id: int, payload: CustomFieldUpdate) -> dict[str, Any]:
    row = await settings_repository.get_custom_field(session, field_id)
    if row is None:
        raise AppException("字段不存在", business_code=400, status_code=404)

    if payload.name is not None:
        row.name = payload.name
    if payload.placeholder is not None:
        row.placeholder = payload.placeholder
    if payload.fieldOptions is not None:
        row.field_options = _normalize_field_options(payload.fieldOptions if row.field_type == "select" else [])
    if payload.isRequired is not None:
        row.is_required = payload.isRequired
    if payload.active is not None:
        row.active = payload.active
    if payload.sort is not None:
        row.sort_order = payload.sort

    await settings_repository.commit(session)
    await settings_repository.refresh(session, row)
    return _field_to_dict(row)


async def delete_custom_field(session: AsyncSession, field_id: int) -> None:
    row = await settings_repository.get_custom_field(session, field_id)
    if row is None:
        raise AppException("字段不存在", business_code=400, status_code=404)
    if row.is_system:
        raise AppException("系统字段不可删除", business_code=400, status_code=400)

    await settings_repository.delete_custom_field(session, row)
    await settings_repository.commit(session)


async def _ensure_seed_dicts(session: AsyncSession) -> None:
    existing_status = await settings_repository.list_dict_items(session, "lead_status")
    existing_level = await settings_repository.list_dict_items(session, "lead_level")
    existing_source = await settings_repository.list_dict_items(session, "lead_source")
    existing_tag = await settings_repository.list_dict_items(session, "lead_tag")
    existing_loss_reason = await settings_repository.list_dict_items(session, "loss_reason")

    if not existing_status:
        for item in REQUIRED_LEAD_STATUS_ITEMS:
            settings_repository.add_dict_item(
                session,
                DictItem(
                    dict_type="lead_status",
                    item_key=item["value"],
                    item_label=item["label"],
                    color=item["color"],
                    sort_order=item["sort"],
                    enabled=True,
                    is_system=True,
                ),
            )

    if not existing_level:
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_level", item_key="A", item_label="A级 (近期可成交)", color="#ef4444", sort_order=1, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_level", item_key="B", item_label="B级 (持续跟进)", color="#f59e0b", sort_order=2, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_level", item_key="C", item_label="C级 (意向一般)", color="#3b82f6", sort_order=3, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_level", item_key="D", item_label="D级 (低意向)", color="#94a3b8", sort_order=4, enabled=True, is_system=False))

    if not existing_source:
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_source", item_key="douyin", item_label="抖音广告", color=None, sort_order=1, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_source", item_key="baidu", item_label="百度搜索", color=None, sort_order=2, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_source", item_key="expo", item_label="线下展会", color=None, sort_order=3, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_source", item_key="referral", item_label="转介绍", color=None, sort_order=4, enabled=True, is_system=False))

    if not existing_tag:
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_tag", item_key="high_value", item_label="高净值", color=None, sort_order=1, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_tag", item_key="franchise_exp", item_label="曾加盟过", color=None, sort_order=2, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_tag", item_key="mall_shop", item_label="商场铺", color=None, sort_order=3, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_tag", item_key="competitor_convert", item_label="竞品转出", color=None, sort_order=4, enabled=True, is_system=False))
        settings_repository.add_dict_item(session, DictItem(dict_type="lead_tag", item_key="signed", item_label="已签约", color=None, sort_order=5, enabled=True, is_system=False))

    if not existing_loss_reason:
        settings_repository.add_dict_item(session, DictItem(dict_type="loss_reason", item_key="no_money", item_label="资金不足", color=None, sort_order=1, enabled=True, is_system=False))

    if not existing_status or not existing_level or not existing_source or not existing_tag or not existing_loss_reason:
        await settings_repository.commit(session)

    await _ensure_required_lead_status_items(session)


def list_dict_types() -> list[dict[str, str]]:
    return DICT_TYPES


def _dict_item_to_manage_dict(item: DictItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "label": item.item_label,
        "value": item.item_key,
        "color": item.color,
        "active": item.enabled,
        "isSystem": item.is_system,
        "sort": item.sort_order,
    }


async def list_dict_items_manage(session: AsyncSession, dict_type: str) -> dict[str, Any]:
    await _ensure_seed_dicts(session)
    await _cleanup_duplicate_dict_items(session, dict_type)
    rows = await settings_repository.list_dict_items(session, dict_type)
    return {"dictType": dict_type, "items": [_dict_item_to_manage_dict(item) for item in rows]}


async def create_dict_item_manage(session: AsyncSession, dict_type: str, payload: DictItemManageCreate) -> dict[str, Any]:
    await _cleanup_duplicate_dict_items(session, dict_type)
    duplicated = await settings_repository.get_dict_item_by_key(session, dict_type, payload.value)
    if duplicated is not None:
        raise AppException("字典值已存在", business_code=400, status_code=400)

    sort_order = await settings_repository.get_dict_max_sort(session, dict_type) + 1
    row = DictItem(
        dict_type=dict_type,
        item_key=payload.value,
        item_label=payload.label,
        color=payload.color,
        enabled=payload.active,
        is_system=False,
        sort_order=sort_order,
    )
    settings_repository.add_dict_item(session, row)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, row)
    return _dict_item_to_manage_dict(row)


async def update_dict_item_manage(session: AsyncSession, item_id: int, payload: DictItemManageUpdate) -> dict[str, Any]:
    row = await settings_repository.get_dict_item(session, item_id)
    if row is None:
        raise AppException("字典项不存在", business_code=400, status_code=404)

    if payload.value is not None and payload.value != row.item_key:
        duplicated = await settings_repository.get_dict_item_by_key(session, row.dict_type, payload.value)
        if duplicated is not None and duplicated.id != item_id:
            raise AppException("字典值已存在", business_code=400, status_code=400)
        row.item_key = payload.value
    if payload.label is not None:
        row.item_label = payload.label
    if payload.color is not None:
        row.color = payload.color
    if payload.active is not None:
        row.enabled = payload.active

    await settings_repository.commit(session)
    await _cleanup_duplicate_dict_items(session, row.dict_type)
    await settings_repository.refresh(session, row)
    return _dict_item_to_manage_dict(row)


async def delete_dict_item_manage(session: AsyncSession, item_id: int) -> None:
    row = await settings_repository.get_dict_item(session, item_id)
    if row is None:
        raise AppException("字典项不存在", business_code=400, status_code=404)
    if row.is_system:
        raise AppException("系统字典不可删除", business_code=400, status_code=400)

    await settings_repository.delete_dict_item(session, row)
    await settings_repository.commit(session)
    await _cleanup_duplicate_dict_items(session, row.dict_type)


async def move_dict_item(session: AsyncSession, item_id: int, direction: str) -> None:
    row = await settings_repository.get_dict_item(session, item_id)
    if row is None:
        raise AppException("字典项不存在", business_code=400, status_code=404)

    rows = await settings_repository.list_dict_items(session, row.dict_type)
    index = next((i for i, item in enumerate(rows) if item.id == item_id), -1)
    if index < 0:
        return

    target_index = index - 1 if direction == "up" else index + 1
    if target_index < 0 or target_index >= len(rows):
        return

    target = rows[target_index]
    row.sort_order, target.sort_order = target.sort_order, row.sort_order
    await settings_repository.commit(session)
    await _cleanup_duplicate_dict_items(session, row.dict_type)


def _recycle_to_dict(entity: RecycleRule) -> dict[str, Any]:
    return {
        "enabled": entity.enabled,
        "rule1": {
            "active": entity.rule1_active,
            "days": entity.rule1_days,
        },
        "rule2": {
            "active": entity.rule2_active,
            "days": entity.rule2_days,
            "protectHighIntent": entity.rule2_protect_high_intent,
        },
        "rule3": {
            "active": entity.rule3_active,
            "count": entity.rule3_count,
        },
        "notify": {
            "beforeDrop": entity.notify_before_drop,
            "afterDrop": entity.notify_after_drop,
        },
    }


async def _ensure_recycle_rule(session: AsyncSession) -> RecycleRule:
    entity = await settings_repository.get_recycle_rule(session)
    if entity is not None:
        return entity

    entity = RecycleRule(
        enabled=True,
        rule1_active=True,
        rule1_days=3,
        rule2_active=True,
        rule2_days=15,
        rule2_protect_high_intent=True,
        rule3_active=False,
        rule3_count=20,
        notify_before_drop=True,
        notify_after_drop=False,
    )
    settings_repository.add_recycle_rule(session, entity)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return entity


async def get_recycle_rules(session: AsyncSession) -> dict[str, Any]:
    entity = await _ensure_recycle_rule(session)
    return _recycle_to_dict(entity)


async def update_recycle_rules(session: AsyncSession, payload: RecycleRulesUpdate) -> dict[str, Any]:
    entity = await _ensure_recycle_rule(session)
    entity.enabled = payload.enabled
    entity.rule1_active = payload.rule1.active
    entity.rule1_days = payload.rule1.days or 1
    entity.rule2_active = payload.rule2.active
    entity.rule2_days = payload.rule2.days or 1
    entity.rule2_protect_high_intent = bool(payload.rule2.protectHighIntent)
    entity.rule3_active = payload.rule3.active
    entity.rule3_count = payload.rule3.count or 1
    entity.notify_before_drop = payload.notify.beforeDrop
    entity.notify_after_drop = payload.notify.afterDrop
    await settings_repository.commit(session)
    await settings_repository.refresh(session, entity)
    return _recycle_to_dict(entity)


async def _ensure_root_department(session: AsyncSession) -> Department:
    departments = await settings_repository.list_departments(session)
    root = next((item for item in departments if item.parent_id is None), None)
    if root is not None:
        return root
    root = Department(name="梦客餐饮集团 (总部)", leader_staff_id="ST001", parent_id=None, sort_order=1, active=True, monthly_target=0)
    settings_repository.add_department(session, root)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, root)
    return root


async def create_org_user(session: AsyncSession, payload: OrgUserCreate) -> dict[str, Any]:
    duplicated = await settings_repository.get_user_by_phone(session, payload.phone)
    if duplicated is not None:
        raise AppException("手机号已存在", business_code=400, status_code=400)

    if payload.password is not None and is_weak_password(payload.password):
        raise AppException("密码强度不足，请至少 8 位且不要使用弱口令", business_code=400, status_code=400)

    normalized_role = normalize_role(payload.role)
    if normalized_role not in CANONICAL_ROLES:
        raise AppException("角色不合法，仅支持 admin/manager/sales", business_code=400, status_code=400)

    dept_name: str | None = None
    if payload.deptId is not None:
        department = await settings_repository.get_department(session, payload.deptId)
        if department is None:
            raise AppException("部门不存在", business_code=400, status_code=404)
        dept_name = department.name

    staff_ids = await settings_repository.list_staff_ids(session)
    max_serial = 0
    for staff_id in staff_ids:
        serial_part = staff_id[2:]
        if serial_part.isdigit():
            max_serial = max(max_serial, int(serial_part))

    serial = max_serial + 1
    user_id = f"ST{serial:04d}"
    while await settings_repository.get_user(session, user_id) is not None:
        serial += 1
        user_id = f"ST{serial:04d}"

    user = User(
        id=user_id,
        name=payload.name,
        phone=payload.phone,
        role=normalized_role,
        password_hash=hash_password(payload.password or "12345678"),
        password_updated_at=datetime.now(timezone.utc),
        must_change_password=True,
        active=payload.active,
        dept_name=dept_name,
        monthly_target=payload.monthlyTarget if normalized_role == "sales" else 0,
        monthly_deposit_target=0,
    )
    settings_repository.add_user(session, user)
    await settings_repository.commit(session)
    await settings_repository.refresh(session, user)

    departments = await settings_repository.list_departments(session)
    dept_map = {department.name: department.id for department in departments}
    return _user_to_org_dict(user, dept_map)


async def update_org_user(session: AsyncSession, user_id: str, payload: OrgUserUpdate) -> dict[str, Any]:
    user = await settings_repository.get_user(session, user_id)
    if user is None:
        raise AppException("员工不存在", business_code=400, status_code=404)

    if payload.phone is not None and payload.phone != user.phone:
        duplicated = await settings_repository.get_user_by_phone(session, payload.phone)
        if duplicated is not None and duplicated.id != user_id:
            raise AppException("手机号已存在", business_code=400, status_code=400)
        user.phone = payload.phone

    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        normalized_role = normalize_role(payload.role)
        if normalized_role not in CANONICAL_ROLES:
            raise AppException("角色不合法，仅支持 admin/manager/sales", business_code=400, status_code=400)
        user.role = normalized_role
        if normalized_role != "sales":
            user.monthly_target = 0
            user.monthly_deposit_target = 0
    if payload.active is not None:
        user.active = payload.active
    if payload.monthlyTarget is not None:
        user.monthly_target = payload.monthlyTarget if user.role == "sales" else 0
    user.monthly_deposit_target = 0
    if payload.password is not None:
        if is_weak_password(payload.password):
            raise AppException("密码强度不足，请至少 8 位且不要使用弱口令", business_code=400, status_code=400)
        user.password_hash = hash_password(payload.password)
        user.password_updated_at = datetime.now(timezone.utc)
        user.must_change_password = True
    if payload.deptId is not None:
        department = await settings_repository.get_department(session, payload.deptId)
        if department is None:
            raise AppException("部门不存在", business_code=400, status_code=404)
        user.dept_name = department.name

    await settings_repository.commit(session)
    await settings_repository.refresh(session, user)

    departments = await settings_repository.list_departments(session)
    dept_map = {department.name: department.id for department in departments}
    return _user_to_org_dict(user, dept_map)


async def delete_org_user(session: AsyncSession, user_id: str) -> None:
    user = await settings_repository.get_user(session, user_id)
    if user is None:
        raise AppException("员工不存在", business_code=400, status_code=404)

    if user.id == "ST001":
        raise AppException("系统默认管理员不可删除", business_code=400, status_code=400)

    departments = await settings_repository.list_departments(session)
    leader_departments = [department.name for department in departments if department.leader_staff_id == user.id]
    if leader_departments:
        raise AppException("该员工仍是部门负责人，请先调整部门负责人", business_code=400, status_code=400)

    users = await settings_repository.list_users(session)
    admin_count = sum(1 for row in users if normalize_role(row.role) == "admin")
    if normalize_role(user.role) == "admin" and admin_count <= 1:
        raise AppException("至少保留一名管理员", business_code=400, status_code=400)

    await settings_repository.delete_user(session, user)
    await settings_repository.commit(session)


async def bootstrap_org(session: AsyncSession) -> None:
    root = await _ensure_root_department(session)

    default_user = await settings_repository.get_user(session, "ST001")
    if default_user is None:
        return

    if default_user.dept_name != root.name:
        default_user.dept_name = root.name
        await settings_repository.commit(session)
