from typing import Any
import asyncio
import os

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import ensure_runtime_security
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.response import success_response
from app.services.recycle_runner_service import recycle_worker_loop


def create_app() -> FastAPI:
    ensure_runtime_security()
    app = FastAPI(
        title="MengKeCloud CRM API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)
    app.include_router(api_v1_router, prefix="/api/v1")

    @app.on_event("startup")
    async def _startup_recycle_worker() -> None:
        if not settings.recycle_worker_enabled:
            return
        if os.getenv("PYTEST_CURRENT_TEST"):
            return
        stop_event = asyncio.Event()
        task = asyncio.create_task(recycle_worker_loop(stop_event))
        app.state.recycle_worker_stop_event = stop_event
        app.state.recycle_worker_task = task

    @app.on_event("shutdown")
    async def _shutdown_recycle_worker() -> None:
        stop_event = getattr(app.state, "recycle_worker_stop_event", None)
        task = getattr(app.state, "recycle_worker_task", None)
        if stop_event is not None:
            stop_event.set()
        if task is not None:
            await task

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return success_response(data={"status": "ok"}, message="操作成功")

    @app.get("/")
    async def root() -> dict[str, Any]:
        return success_response(
            data={
                "service": "MengKeCloud CRM API",
                "docs": "/docs",
                "health": "/health",
            },
            message="服务已启动",
        )

    return app


app = create_app()
