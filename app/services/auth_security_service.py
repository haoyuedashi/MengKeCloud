from datetime import datetime, timedelta, timezone
from collections import defaultdict

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    deprecated="auto",
)

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60

_rate_limit_bucket: dict[str, list[datetime]] = defaultdict(list)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return bool(pwd_context.verify(plain_password, hashed_password))


def is_weak_password(password: str) -> bool:
    value = password.strip()
    if len(value) < 8 or len(value) > 64:
        return True
    weak = {
        "password",
        "12345678",
        "qwerty123",
        "admin123",
        "11111111",
    }
    return value.lower() in weak


def is_user_locked(user: object, now: datetime | None = None) -> bool:
    locked_until = getattr(user, "locked_until", None)
    if locked_until is None:
        return False
    current = now or datetime.now(timezone.utc)
    return locked_until > current


def record_failed_login(user: object, now: datetime | None = None) -> None:
    current = now or datetime.now(timezone.utc)
    attempts = int(getattr(user, "failed_attempts", 0) or 0) + 1
    setattr(user, "failed_attempts", attempts)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        setattr(user, "locked_until", current + timedelta(minutes=LOCKOUT_MINUTES))


def record_successful_login(user: object) -> None:
    setattr(user, "failed_attempts", 0)
    setattr(user, "locked_until", None)


def build_rate_limit_key(phone: str, client_ip: str) -> str:
    return f"{phone.strip()}@{client_ip.strip()}"


def is_login_rate_limited(key: str, now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    bucket = _rate_limit_bucket.get(key, [])
    if not bucket:
        return False

    threshold = current - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    valid = [item for item in bucket if item > threshold]
    _rate_limit_bucket[key] = valid
    return len(valid) >= RATE_LIMIT_MAX_ATTEMPTS


def record_login_attempt(key: str, now: datetime | None = None) -> None:
    current = now or datetime.now(timezone.utc)
    _rate_limit_bucket[key].append(current)


def reset_rate_limit_bucket() -> None:
    _rate_limit_bucket.clear()
