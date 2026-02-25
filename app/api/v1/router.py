from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.dicts import router as dict_router
from app.api.v1.endpoints.leads import router as leads_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.pool import router as pool_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.settings import router as settings_router
from app.api.v1.endpoints.ws import router as ws_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(leads_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(pool_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(dict_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(ws_router)
