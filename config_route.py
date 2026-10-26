from fastapi import APIRouter
import os
from app.config import settings
from app.models.schemas import ConfigResponse, ConfigUpdateRequest
from app.services.storage import storage_service

router = APIRouter()

@router.get("/config", response_model=ConfigResponse)
async def get_configuration():
    gemini_key = settings.GEMINI_API_KEY or storage_service.get_config("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "").strip() or storage_service.get_config("GEMINI_MODEL", settings.GEMINI_MODEL)
    tg_token = storage_service.get_config("TELEGRAM_BOT_TOKEN", settings.TELEGRAM_BOT_TOKEN)
    tg_chat = storage_service.get_config("TELEGRAM_CHAT_ID", settings.TELEGRAM_CHAT_ID)
    market_url = storage_service.get_config("DEFAULT_MARKET_URL", settings.DEFAULT_MARKET_URL)

    return ConfigResponse(
        has_gemini_key=bool(gemini_key.strip()),
        gemini_model=gemini_model,
        has_telegram_token=bool(tg_token.strip()),
        telegram_chat_id=tg_chat,
        default_market_url=market_url,
        scan_timeout_seconds=settings.ANALYSIS_BUDGET_SECONDS
    )

@router.post("/config", response_model=ConfigResponse)
async def update_configuration(req: ConfigUpdateRequest):
    if req.gemini_api_key is not None:
        storage_service.set_config("GEMINI_API_KEY", req.gemini_api_key.strip())
    if req.gemini_model is not None:
        storage_service.set_config("GEMINI_MODEL", req.gemini_model.strip())
    if req.telegram_bot_token is not None:
        storage_service.set_config("TELEGRAM_BOT_TOKEN", req.telegram_bot_token.strip())
    if req.telegram_chat_id is not None:
        storage_service.set_config("TELEGRAM_CHAT_ID", req.telegram_chat_id.strip())
    if req.default_market_url is not None:
        storage_service.set_config("DEFAULT_MARKET_URL", req.default_market_url.strip())

    return await get_configuration()
