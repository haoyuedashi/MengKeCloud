from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.rbac import normalize_role
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.models.refresh_session import RefreshSession
from app.repositories import auth_repository
from app.services import auth_security_service


def _build_token_payload(
    user_id: str,
    name: str,
    role: str,
    phone: str,
    *,
    must_change_password: bool,
) -> dict[str, str | bool]:
    return {
        "staffId": user_id,
        "name": name,
        "role": normalize_role(role),
        "phone": phone,
        "mustChangePassword": bool(must_change_password),
    }


async def _issue_token_pair(
    session: AsyncSession,
    user_id: str,
    name: str,
    role: str,
    phone: str,
    *,
    must_change_password: bool,
) -> dict[str, str | bool]:
    base_payload = _build_token_payload(
        user_id,
        name,
        role,
        phone,
        must_change_password=must_change_password,
    )
    access_token = create_access_token(base_payload)

    refresh_id = uuid4().hex
    refresh_payload = {**base_payload, "jti": refresh_id}
    refresh_token = create_refresh_token(refresh_payload)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_refresh_expire_minutes)
    refresh_entity = RefreshSession(
        id=refresh_id,
        user_id=user_id,
        token_hash=auth_security_service.hash_password(refresh_token),
        revoked=False,
        expires_at=expires_at,
    )
    auth_repository.add_refresh_session(session, refresh_entity)
    await auth_repository.commit(session)

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "tokenType": "Bearer",
        "staffId": user_id,
        "name": name,
        "role": normalize_role(role),
        "phone": phone,
        "mustChangePassword": bool(must_change_password),
    }


async def login(session: AsyncSession, phone: str, password: str, client_ip: str) -> dict[str, str | bool]:
    rate_key = auth_security_service.build_rate_limit_key(phone, client_ip)
    if auth_security_service.is_login_rate_limited(rate_key):
        raise AppException("登录过于频繁，请稍后再试", business_code=429, status_code=429)
    auth_security_service.record_login_attempt(rate_key)

    user = await auth_repository.get_user_by_phone(session, phone)
    if user is None or not user.active:
        raise AppException("账号或密码错误", business_code=401, status_code=401)
    if auth_security_service.is_user_locked(user):
        raise AppException("账号已锁定，请稍后再试", business_code=401, status_code=423)
    if not auth_security_service.verify_password(password, user.password_hash):
        auth_security_service.record_failed_login(user)
        await auth_repository.commit(session)
        raise AppException("账号或密码错误", business_code=401, status_code=401)

    must_change_password = bool(user.must_change_password)
    if not must_change_password and auth_security_service.verify_password("12345678", user.password_hash):
        user.must_change_password = True
        must_change_password = True

    auth_security_service.record_successful_login(user)
    await auth_repository.commit(session)
    return await _issue_token_pair(
        session,
        user.id,
        user.name,
        user.role,
        user.phone,
        must_change_password=must_change_password,
    )


async def refresh(session: AsyncSession, refresh_token: str) -> dict[str, str | bool]:
    token_data = decode_refresh_token(refresh_token)
    refresh_id = str(token_data.get("jti") or "")
    staff_id = str(token_data.get("staffId") or "")
    if not refresh_id or not staff_id:
        raise AppException("无效令牌", business_code=401, status_code=401)

    refresh_session = await auth_repository.get_refresh_session(session, refresh_id)
    now = datetime.now(timezone.utc)
    if (
        refresh_session is None
        or refresh_session.revoked
        or refresh_session.expires_at <= now
        or not auth_security_service.verify_password(refresh_token, refresh_session.token_hash)
    ):
        raise AppException("登录已过期", business_code=401, status_code=401)

    await auth_repository.revoke_refresh_session(session, refresh_session)
    user = await auth_repository.get_user(session, staff_id)
    if user is None or not user.active:
        await auth_repository.commit(session)
        raise AppException("登录已过期", business_code=401, status_code=401)

    data = await _issue_token_pair(
        session,
        user.id,
        user.name,
        user.role,
        user.phone,
        must_change_password=bool(user.must_change_password),
    )
    return data


async def logout(session: AsyncSession, refresh_token: str) -> None:
    token_data = decode_refresh_token(refresh_token)
    refresh_id = str(token_data.get("jti") or "")
    if not refresh_id:
        return
    refresh_session = await auth_repository.get_refresh_session(session, refresh_id)
    if refresh_session is not None and not refresh_session.revoked:
        await auth_repository.revoke_refresh_session(session, refresh_session)
        await auth_repository.commit(session)


async def get_me(session: AsyncSession, staff_id: str) -> dict[str, str | bool]:
    user = await auth_repository.get_user(session, staff_id)
    if user is None:
        raise AppException("用户不存在", business_code=404, status_code=404)
    return {
        "staffId": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": normalize_role(user.role),
        "mustChangePassword": bool(user.must_change_password),
    }


async def change_password(
    session: AsyncSession,
    *,
    staff_id: str,
    current_password: str,
    new_password: str,
) -> dict[str, str | bool]:
    user = await auth_repository.get_user(session, staff_id)
    if user is None or not user.active:
        raise AppException("用户不存在", business_code=404, status_code=404)
    if not auth_security_service.verify_password(current_password, user.password_hash):
        raise AppException("当前密码错误", business_code=400, status_code=400)
    if auth_security_service.is_weak_password(new_password):
        raise AppException("密码强度不足，请至少 8 位且不要使用弱口令", business_code=400, status_code=400)
    if auth_security_service.verify_password(new_password, user.password_hash):
        raise AppException("新密码不能与当前密码相同", business_code=400, status_code=400)

    user.password_hash = auth_security_service.hash_password(new_password)
    user.password_updated_at = datetime.now(timezone.utc)
    user.must_change_password = False
    await auth_repository.revoke_refresh_sessions_by_user(session, user.id)
    return await _issue_token_pair(
        session,
        user.id,
        user.name,
        user.role,
        user.phone,
        must_change_password=False,
    )
