from typing import Any
import importlib

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.common import ApiEnvelope
from app.schemas.dicts import DictItemsData

dict_service = importlib.import_module("app.services.dict_service")

router = APIRouter(prefix="/dict", tags=["dict"])


@router.get("/{dict_type}", response_model=ApiEnvelope[DictItemsData])
async def get_dict_items(
    dict_type: str,
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_roles("admin", "manager", "sales")),
) -> dict[str, Any]:
    items = await dict_service.get_dict_items(db, dict_type)
    data = {
        "dictType": dict_type,
        "items": items,
    }
    return success_response(data=data, message="操作成功")
