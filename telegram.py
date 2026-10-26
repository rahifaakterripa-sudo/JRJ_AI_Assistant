from fastapi import APIRouter
from app.models.schemas import TelegramTestRequest, TelegramTestResponse
from app.services.telegram_service import TelegramService
from app.services.storage import storage_service

router = APIRouter()

@router.post("/telegram/test", response_model=TelegramTestResponse)
async def test_telegram_connection(request: TelegramTestRequest):
    bot_token = request.bot_token
    chat_id = request.chat_id
    success, msg = await TelegramService.send_test_message(bot_token=bot_token, chat_id=chat_id)
    return TelegramTestResponse(
        success=success,
        message=msg,
        chat_id=chat_id or storage_service.get_config("TELEGRAM_CHAT_ID")
    )
