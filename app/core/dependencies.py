from typing import Any

from fastapi import Depends, Header

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.rbac import normalize_role
from app.core.security import decode_access_token


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise AppException("缺少 Authorization", business_code=401, status_code=401)
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise AppException("Authorization 格式错误", business_code=401, status_code=401)
    return authorization[len(prefix) :].strip()


async def get_current_staff(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not settings.auth_enabled:
        if authorization:
            token = _extract_bearer_token(authorization)
            return decode_access_token(token)
        return {"staffId": "ST001", "name": "系统管理员", "role": "admin"}

    token = _extract_bearer_token(authorization)
    return decode_access_token(token)


async def require_admin(current_staff: dict[str, Any] = Depends(get_current_staff)) -> dict[str, Any]:
    if bool(current_staff.get("mustChangePassword")):
        raise AppException("首次登录请先修改密码", business_code=40301, status_code=403)
    if normalize_role(str(current_staff.get("role") or "")) != "admin":
        raise AppException("无权限执行该操作", business_code=401, status_code=403)
    return current_staff


def require_roles(*allowed_roles: str):
    async def _checker(current_staff: dict[str, Any] = Depends(get_current_staff)) -> dict[str, Any]:
        if bool(current_staff.get("mustChangePassword")):
            raise AppException("首次登录请先修改密码", business_code=40301, status_code=403)
        role = normalize_role(str(current_staff.get("role") or ""))
        normalized_allowed = {normalize_role(item) for item in allowed_roles}
        if role not in normalized_allowed:
            raise AppException("无权限执行该操作", business_code=401, status_code=403)
        current_staff["role"] = role
        return current_staff

    return _checker
