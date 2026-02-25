from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiEnvelope(BaseModel, Generic[T]):
    code: int = Field(default=200)
    message: str = Field(default="操作成功")
    data: T | None = None
