from typing import Any
import importlib

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.settings import (
    CustomFieldCreate,
    CustomFieldOut,
    CustomFieldsData,
    CustomFieldUpdate,
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    DictItemManageCreate,
    DictItemManageOut,
    DictItemsManageData,
    DictItemManageUpdate,
    DictItemMove,
    DictTypeOut,
    OrgData,
    OrgUserCreate,
    OrgUserOut,
    OrgUserUpdate,
    PlatformAiTestData,
    PlatformAiTestRequest,
    PlatformSettingsData,
    PlatformSettingsUpdate,
    RecycleRulesData,
    RecycleRulesUpdate,
    RoleCreate,
    RolesData,
    RoleOut,
    RoleUpdate,
)

settings_service = importlib.import_module("app.services.settings_service")

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/platform", response_model=ApiEnvelope[PlatformSettingsData])
async def get_platform_settings(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.get_platform_settings(db)
    return success_response(data=data, message="操作成功")


@router.put("/platform", response_model=ApiEnvelope[PlatformSettingsData])
async def update_platform_settings(
    payload: PlatformSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_platform_settings(db, payload)
    return success_response(data=data, message="操作成功")


@router.post("/platform/test-ai", response_model=ApiEnvelope[PlatformAiTestData])
async def test_platform_ai_connection(
    payload: PlatformAiTestRequest,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.test_platform_ai_connection(db, payload)
    return success_response(data=data, message="操作成功")


@router.get("/org", response_model=ApiEnvelope[OrgData])
async def get_org_data(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.bootstrap_org(db)
    data = await settings_service.list_org_data(db)
    return success_response(data=data, message="操作成功")


@router.post("/org/departments", response_model=ApiEnvelope[DepartmentOut])
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.create_department(db, payload)
    return success_response(data=data, message="操作成功")


@router.put("/org/departments/{department_id}", response_model=ApiEnvelope[DepartmentOut])
async def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_department(db, department_id, payload)
    return success_response(data=data, message="操作成功")


@router.delete("/org/departments/{department_id}", response_model=ApiEnvelope[dict[str, int]])
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.delete_department(db, department_id)
    return success_response(data={"id": department_id}, message="操作成功")


@router.post("/org/users", response_model=ApiEnvelope[OrgUserOut])
async def create_org_user(
    payload: OrgUserCreate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.create_org_user(db, payload)
    return success_response(data=data, message="操作成功")


@router.put("/org/users/{user_id}", response_model=ApiEnvelope[OrgUserOut])
async def update_org_user(
    user_id: str,
    payload: OrgUserUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_org_user(db, user_id, payload)
    return success_response(data=data, message="操作成功")


@router.delete("/org/users/{user_id}", response_model=ApiEnvelope[dict[str, str]])
async def delete_org_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.delete_org_user(db, user_id)
    return success_response(data={"id": user_id}, message="操作成功")


@router.get("/roles", response_model=ApiEnvelope[RolesData])
async def get_roles(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.list_roles(db)
    return success_response(data=data, message="操作成功")


@router.post("/roles", response_model=ApiEnvelope[RoleOut])
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.create_role(db, payload)
    return success_response(data=data, message="操作成功")


@router.put("/roles/{role_id}", response_model=ApiEnvelope[RoleOut])
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_role(db, role_id, payload)
    return success_response(data=data, message="操作成功")


@router.delete("/roles/{role_id}", response_model=ApiEnvelope[dict[str, int]])
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.delete_role(db, role_id)
    return success_response(data={"id": role_id}, message="操作成功")


@router.get("/fields/{entity}", response_model=ApiEnvelope[CustomFieldsData])
async def get_custom_fields(
    entity: str,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await settings_service.list_custom_fields(db, entity)
    return success_response(data=data, message="操作成功")


@router.post("/fields/{entity}", response_model=ApiEnvelope[CustomFieldOut])
async def create_custom_field(
    entity: str,
    payload: CustomFieldCreate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.create_custom_field(db, entity, payload)
    return success_response(data=data, message="操作成功")


@router.put("/fields/item/{field_id}", response_model=ApiEnvelope[CustomFieldOut])
async def update_custom_field(
    field_id: int,
    payload: CustomFieldUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_custom_field(db, field_id, payload)
    return success_response(data=data, message="操作成功")


@router.delete("/fields/item/{field_id}", response_model=ApiEnvelope[dict[str, int]])
async def delete_custom_field(
    field_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.delete_custom_field(db, field_id)
    return success_response(data={"id": field_id}, message="操作成功")


@router.get("/dict/types", response_model=ApiEnvelope[list[DictTypeOut]])
async def get_dict_types(
    _: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = settings_service.list_dict_types()
    return success_response(data=data, message="操作成功")


@router.get("/dict/{dict_type}", response_model=ApiEnvelope[DictItemsManageData])
async def get_dict_items_manage(
    dict_type: str,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    data = await settings_service.list_dict_items_manage(db, dict_type)
    return success_response(data=data, message="操作成功")


@router.post("/dict/{dict_type}", response_model=ApiEnvelope[DictItemManageOut])
async def create_dict_item_manage(
    dict_type: str,
    payload: DictItemManageCreate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.create_dict_item_manage(db, dict_type, payload)
    return success_response(data=data, message="操作成功")


@router.put("/dict/item/{item_id}", response_model=ApiEnvelope[DictItemManageOut])
async def update_dict_item_manage(
    item_id: int,
    payload: DictItemManageUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_dict_item_manage(db, item_id, payload)
    return success_response(data=data, message="操作成功")


@router.delete("/dict/item/{item_id}", response_model=ApiEnvelope[dict[str, int]])
async def delete_dict_item_manage(
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.delete_dict_item_manage(db, item_id)
    return success_response(data={"id": item_id}, message="操作成功")


@router.post("/dict/item/{item_id}/move", response_model=ApiEnvelope[dict[str, int]])
async def move_dict_item(
    item_id: int,
    payload: DictItemMove,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    await settings_service.move_dict_item(db, item_id, payload.direction)
    return success_response(data={"id": item_id}, message="操作成功")


@router.get("/rules", response_model=ApiEnvelope[RecycleRulesData])
async def get_recycle_rules(
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.get_recycle_rules(db)
    return success_response(data=data, message="操作成功")


@router.put("/rules", response_model=ApiEnvelope[RecycleRulesData])
async def update_recycle_rules(
    payload: RecycleRulesUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin")),
) -> dict[str, Any]:
    data = await settings_service.update_recycle_rules(db, payload)
    return success_response(data=data, message="操作成功")
