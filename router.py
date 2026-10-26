from fastapi import APIRouter
from app.api.v1.analyze import router as analyze_router
from app.api.v1.history import router as history_router
from app.api.v1.usage import router as usage_router
from app.api.v1.telegram import router as telegram_router
from app.api.v1.health import router as health_router
from app.api.v1.config_route import router as config_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(analyze_router, tags=["Chart Analysis"])
api_router.include_router(history_router, tags=["Scan History"])
api_router.include_router(usage_router, tags=["API Usage"])
api_router.include_router(telegram_router, tags=["Telegram Notifications"])
api_router.include_router(config_router, tags=["Configuration"])
