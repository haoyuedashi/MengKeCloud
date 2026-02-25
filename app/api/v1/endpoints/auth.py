from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_staff
from app.core.response import success_response
from app.db.session import get_db_session
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginData,
    LoginRequest,
    LogoutRequest,
    MeData,
    RefreshData,
    RefreshRequest,
)
from app.schemas.common import ApiEnvelope
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiEnvelope[LoginData])
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    client_ip = request.client.host if request.client else "127.0.0.1"
    data = await auth_service.login(db, payload.phone, payload.password, client_ip)
    return success_response(data=data, message="登录成功")


@router.post("/refresh", response_model=ApiEnvelope[RefreshData])
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    data = await auth_service.refresh(db, payload.refresh_token)
    return success_response(
        data=data,
        message="刷新成功",
    )


@router.post("/logout", response_model=ApiEnvelope[dict[str, bool]])
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    await auth_service.logout(db, payload.refresh_token)
    return success_response(data={"ok": True}, message="已退出登录")


@router.get("/me", response_model=ApiEnvelope[MeData])
async def me(
    current_staff: dict[str, Any] = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    data = await auth_service.get_me(db, str(current_staff.get("staffId") or ""))
    return success_response(data=data, message="操作成功")


@router.post("/change-password", response_model=ApiEnvelope[LoginData])
async def change_password(
    payload: ChangePasswordRequest,
    current_staff: dict[str, Any] = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    staff_id = str(current_staff.get("staffId") or "")
    data = await auth_service.change_password(
        db,
        staff_id=staff_id,
        current_password=payload.currentPassword,
        new_password=payload.newPassword,
    )
    return success_response(data=data, message="密码修改成功")
