from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "MengKeCloud CRM API"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mengkecloud"
    alembic_database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mengkecloud"
    message_bus_backend: str = "memory"
    redis_url: str = "redis://127.0.0.1:6379/0"
    ws_voice_assist_channel_prefix: str = "voice_assist"
    auth_enabled: bool = False
    jwt_secret_key: str = "change-me-in-production-with-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    jwt_refresh_expire_minutes: int = 10080
    ai_enabled: bool = False
    ai_timeout_seconds: int = 12
    ai_max_input_chars: int = 4000
    ai_require_redis_when_enabled: bool = False
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    recycle_worker_enabled: bool = True

    model_config = SettingsConfigDict(env_prefix="MENGKE_", extra="ignore")


settings = Settings()


def ensure_runtime_security() -> None:
    if settings.app_env.lower() == "production" and not settings.auth_enabled:
        raise RuntimeError("MENGKE_AUTH_ENABLED must be true in production")
    if (
        settings.app_env.lower() == "production"
        and settings.ai_enabled
        and settings.ai_require_redis_when_enabled
        and settings.message_bus_backend.lower() != "redis"
    ):
        raise RuntimeError("MENGKE_MESSAGE_BUS_BACKEND must be redis when AI is enabled in production")
