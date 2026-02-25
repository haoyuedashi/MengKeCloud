from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=200)
    message: str = Field(default="操作成功")
    data: T | None = Field(default=None)


def success_response(data: Any = None, message: str = "操作成功") -> dict[str, Any]:
    return ApiResponse(code=200, message=message, data=data).model_dump()


def error_response(code: int = 400, message: str = "请求失败", data: Any = None) -> dict[str, Any]:
    return ApiResponse(code=code, message=message, data=data).model_dump()
