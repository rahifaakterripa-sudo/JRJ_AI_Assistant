import time
from fastapi import APIRouter
from app.config import settings
from app.services.storage import storage_service

router = APIRouter()
_app_start_time = time.time()

@router.get("/health")
async def health_check():
    gemini_key = settings.GEMINI_API_KEY or storage_service.get_config("GEMINI_API_KEY", "")
    telegram_token = settings.TELEGRAM_BOT_TOKEN or storage_service.get_config("TELEGRAM_BOT_TOKEN", "")
    telegram_chat = settings.TELEGRAM_CHAT_ID or storage_service.get_config("TELEGRAM_CHAT_ID", "")

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": round(time.time() - _app_start_time, 1),
        "gemini_configured": bool(gemini_key.strip()),
        "telegram_configured": bool(telegram_token.strip() and telegram_chat.strip()),
        "market_url": storage_service.get_config("DEFAULT_MARKET_URL", settings.DEFAULT_MARKET_URL)
    }
