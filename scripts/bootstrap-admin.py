import asyncio
import os
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.auth_security_service import hash_password


def _env(name: str, default: str) -> str:
    value = (os.getenv(name) or "").strip()
    return value if value else default


async def main() -> None:
    admin_phone = _env("MENGKE_BOOTSTRAP_ADMIN_PHONE", "13800000001")
    admin_password = _env("MENGKE_BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!")
    admin_name = _env("MENGKE_BOOTSTRAP_ADMIN_NAME", "老板")

    if len(admin_phone) < 11:
        raise RuntimeError("MENGKE_BOOTSTRAP_ADMIN_PHONE must be at least 11 characters")

    async with AsyncSessionLocal() as session:
        user = await session.get(User, "ST001")
        password_hash = hash_password(admin_password)
        now = datetime.now(timezone.utc)

        if user is None:
            user = User(
                id="ST001",
                name=admin_name,
                phone=admin_phone,
                role="admin",
                active=True,
                dept_name="总部",
                monthly_target=0,
                monthly_deposit_target=0,
                password_hash=password_hash,
                password_updated_at=now,
                must_change_password=True,
                failed_attempts=0,
                locked_until=None,
            )
            session.add(user)
        else:
            user.name = admin_name
            user.phone = admin_phone
            user.role = "admin"
            user.active = True
            user.password_hash = password_hash
            user.password_updated_at = now
            user.must_change_password = True
            user.failed_attempts = 0
            user.locked_until = None

        await session.commit()

    print("Bootstrap admin ready")
    print(f"Phone: {admin_phone}")
    print(f"Password: {admin_password}")
    print("Notice: password change is required on first login")


if __name__ == "__main__":
    asyncio.run(main())
