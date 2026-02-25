from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field import CustomField
from app.models.department import Department
from app.models.dict_item import DictItem
from app.models.platform_setting import PlatformSetting
from app.models.recycle_rule import RecycleRule
from app.models.system_role import SystemRole
from app.models.user import User


async def get_platform_setting(session: AsyncSession) -> PlatformSetting | None:
    result = await session.execute(select(PlatformSetting).order_by(PlatformSetting.id.asc()).limit(1))
    return result.scalar_one_or_none()


def add_platform_setting(session: AsyncSession, entity: PlatformSetting) -> None:
    session.add(entity)


async def list_departments(session: AsyncSession) -> list[Department]:
    result = await session.execute(select(Department).order_by(Department.sort_order.asc(), Department.id.asc()))
    return list(result.scalars().all())


async def get_department(session: AsyncSession, department_id: int) -> Department | None:
    return await session.get(Department, department_id)


async def get_department_by_name(session: AsyncSession, name: str) -> Department | None:
    result = await session.execute(select(Department).where(Department.name == name))
    return result.scalar_one_or_none()


def add_department(session: AsyncSession, entity: Department) -> None:
    session.add(entity)


async def delete_department(session: AsyncSession, entity: Department) -> None:
    await session.delete(entity)


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.created_at.desc(), User.id.desc()))
    return list(result.scalars().all())


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    result = await session.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_latest_staff_id(session: AsyncSession) -> str | None:
    result = await session.execute(
        select(User.id).where(User.id.like("ST%")).order_by(User.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def list_staff_ids(session: AsyncSession) -> list[str]:
    result = await session.execute(select(User.id).where(User.id.like("ST%")))
    return list(result.scalars().all())


def add_user(session: AsyncSession, user: User) -> None:
    session.add(user)


async def delete_user(session: AsyncSession, entity: User) -> None:
    await session.delete(entity)


async def list_roles(session: AsyncSession) -> list[SystemRole]:
    result = await session.execute(select(SystemRole).order_by(SystemRole.id.asc()))
    return list(result.scalars().all())


async def get_role(session: AsyncSession, role_id: int) -> SystemRole | None:
    return await session.get(SystemRole, role_id)


async def get_role_by_name(session: AsyncSession, name: str) -> SystemRole | None:
    result = await session.execute(select(SystemRole).where(SystemRole.name == name))
    return result.scalar_one_or_none()


def add_role(session: AsyncSession, role: SystemRole) -> None:
    session.add(role)


async def delete_role(session: AsyncSession, role: SystemRole) -> None:
    await session.delete(role)


async def list_custom_fields(session: AsyncSession, entity: str) -> list[CustomField]:
    result = await session.execute(
        select(CustomField)
        .where(CustomField.entity == entity)
        .order_by(CustomField.sort_order.asc(), CustomField.id.asc())
    )
    return list(result.scalars().all())


async def get_custom_field(session: AsyncSession, field_id: int) -> CustomField | None:
    return await session.get(CustomField, field_id)


async def get_custom_field_by_code(session: AsyncSession, entity: str, code: str) -> CustomField | None:
    result = await session.execute(
        select(CustomField).where(CustomField.entity == entity, CustomField.code == code)
    )
    return result.scalar_one_or_none()


async def get_custom_field_max_sort(session: AsyncSession, entity: str) -> int:
    value = await session.scalar(select(func.max(CustomField.sort_order)).where(CustomField.entity == entity))
    return int(value or 0)


def add_custom_field(session: AsyncSession, entity: CustomField) -> None:
    session.add(entity)


async def delete_custom_field(session: AsyncSession, entity: CustomField) -> None:
    await session.delete(entity)


async def list_dict_items(session: AsyncSession, dict_type: str) -> list[DictItem]:
    result = await session.execute(
        select(DictItem)
        .where(DictItem.dict_type == dict_type)
        .order_by(DictItem.sort_order.asc(), DictItem.id.asc())
    )
    return list(result.scalars().all())


async def get_dict_item(session: AsyncSession, item_id: int) -> DictItem | None:
    return await session.get(DictItem, item_id)


async def get_dict_item_by_key(session: AsyncSession, dict_type: str, item_key: str) -> DictItem | None:
    result = await session.execute(
        select(DictItem).where(DictItem.dict_type == dict_type, DictItem.item_key == item_key)
    )
    return result.scalar_one_or_none()


async def get_dict_max_sort(session: AsyncSession, dict_type: str) -> int:
    value = await session.scalar(select(func.max(DictItem.sort_order)).where(DictItem.dict_type == dict_type))
    return int(value or 0)


def add_dict_item(session: AsyncSession, entity: DictItem) -> None:
    session.add(entity)


async def delete_dict_item(session: AsyncSession, entity: DictItem) -> None:
    await session.delete(entity)


async def get_recycle_rule(session: AsyncSession) -> RecycleRule | None:
    result = await session.execute(select(RecycleRule).order_by(RecycleRule.id.asc()).limit(1))
    return result.scalar_one_or_none()


def add_recycle_rule(session: AsyncSession, entity: RecycleRule) -> None:
    session.add(entity)


async def commit(session: AsyncSession) -> None:
    await session.commit()


async def refresh(session: AsyncSession, entity: object) -> None:
    await session.refresh(entity)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
