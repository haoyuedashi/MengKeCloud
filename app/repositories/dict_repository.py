from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dict_item import DictItem


def build_dict_query(dict_type: str) -> Select[tuple[DictItem]]:
    return (
        select(DictItem)
        .where(DictItem.dict_type == dict_type, DictItem.enabled.is_(True))
        .order_by(DictItem.sort_order.asc(), DictItem.id.asc())
    )


async def list_dict_items(session: AsyncSession, stmt: Select[tuple[DictItem]]) -> list[DictItem]:
    result = await session.execute(stmt)
    return list(result.scalars().all())
