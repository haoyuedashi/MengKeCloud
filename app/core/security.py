from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt

from app.core.config import settings
from app.core.exceptions import AppException


TokenType = Literal["access", "refresh"]


def create_token(payload: dict[str, Any], token_type: TokenType, expires_minutes: int) -> str:
    expire_delta = timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    expire_at = datetime.now(timezone.utc) + expire_delta
    data = payload.copy()
    data.update({"exp": int(expire_at.timestamp()), "tokenType": token_type})
    return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(payload: dict[str, Any], expires_minutes: int | None = None) -> str:
    return create_token(
        payload,
        "access",
        expires_minutes or settings.jwt_expire_minutes,
    )


def create_refresh_token(payload: dict[str, Any], expires_minutes: int | None = None) -> str:
    return create_token(
        payload,
        "refresh",
        expires_minutes or settings.jwt_refresh_expire_minutes,
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AppException("登录已过期", business_code=401, status_code=401) from exc
    except jwt.InvalidTokenError as exc:
        raise AppException("无效令牌", business_code=401, status_code=401) from exc

    if "staffId" not in payload:
        raise AppException("令牌缺少 staffId", business_code=401, status_code=401)

    token_type = payload.get("tokenType")
    if expected_type and token_type != expected_type:
        raise AppException("令牌类型错误", business_code=401, status_code=401)
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="access")


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="refresh")
