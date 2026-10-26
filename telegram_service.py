import logging
from typing import Optional
import httpx
from app.config import settings
from app.models.schemas import AnalysisResult
from app.services.storage import storage_service

logger = logging.getLogger("jrj.telegram")

class TelegramService:
    BASE_URL = "https://api.telegram.org/bot"

    @classmethod
    def get_credentials(cls) -> tuple[str, str]:
        """Fetches credentials from storage or settings."""
        token = settings.TELEGRAM_BOT_TOKEN or storage_service.get_config("TELEGRAM_BOT_TOKEN", "")
        chat_id = settings.TELEGRAM_CHAT_ID or storage_service.get_config("TELEGRAM_CHAT_ID", "")
        return token.strip(), chat_id.strip()

    @classmethod
    def format_bengali_report(cls, result: AnalysisResult) -> str:
        """
        Formats a comprehensive, professional Bengali trading analysis report
        for Telegram with cyberpunk emojis and structural clarity.
        """
        # Signal badge
        if result.signal.value == "BUY":
            signal_badge = "🟢 BUY (কল / আপ এন্ট্রি)"
        elif result.signal.value == "SELL":
            signal_badge = "🔴 SELL (পুট / ডাউন এন্ট্রি)"
        else:
            signal_badge = "🟡 WAIT (অপেক্ষা করুন / নো ট্রেড)"

        reasons_bullet = "\n".join([f"  ▫️ {r}" for r in result.reasons]) if result.reasons else "  ▫️ বাজার সামগ্রিক পর্যালোচনা সাপেক্ষে।"

        report = (
            "⚡ <b>JRJ AI ASSISTANT — প্রফেশনাল চার্ট বিশ্লেষণ রিপোর্ট</b> ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>ট্রেড সিগন্যাল:</b> {signal_badge}\n"
            f"📊 <b>প্রমাণের শক্তি (জয়ের সম্ভাবনা নয়):</b> <code>{result.confidence}%</code>\n"
            f"⏱️ <b>প্রস্তাবিত টাইমফ্রেম:</b> <code>{result.timeframe}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>মার্কেট ট্রেন্ড:</b> {result.trend}\n"
            f"🧭 <b>মার্কেট স্ট্রাকচার:</b> {result.market_structure or result.trend}\n"
            f"🛡️ <b>সাপোর্ট ও রেজিস্ট্যান্স:</b> {result.support_resistance}\n"
            f"🕯️ <b>প্রাইস অ্যাকশন:</b> {result.price_action}\n"
            f"🔍 <b>টু-ক্যান্ডেল গ্যাপ (Two-Candle Gap):</b> {result.two_candle_gap}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 <b>মূল কনফ্লুয়েন্স ও যুক্তি:</b>\n"
            f"{reasons_bullet}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Bullish evidence:</b> {'; '.join(result.bullish_evidence or ['Not identified'])}\n"
            f"🔴 <b>Bearish evidence:</b> {'; '.join(result.bearish_evidence or ['Not identified'])}\n"
            f"❔ <b>অনিশ্চয়তা:</b> {'; '.join(result.uncertainty or ['কোনো অতিরিক্ত অনিশ্চয়তা জানানো হয়নি'])}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>বাংলা সারসংক্ষেপ:</b> {result.bengali_summary}\n\n"
            f"⚠️ <b>রিস্ক ম্যানেজমেন্ট ও সতর্কতা:</b>\n{result.risk_warning}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 সময়: <code>{result.timestamp}</code> | <i>JRJ Cyber Core v1.0</i>"
        )
        return report

    @classmethod
    async def send_analysis_report(cls, result: AnalysisResult, image_bytes: Optional[bytes] = None) -> bool:
        """
        Sends the analysis report and chart image to the configured Telegram chat.
        """
        token, chat_id = cls.get_credentials()
        if not token or not chat_id:
            logger.warning("Telegram Bot Token or Chat ID not configured. Skipping Telegram notification.")
            return False

        report_text = cls.format_bengali_report(result)
        send_photo_url = f"{cls.BASE_URL}{token}/sendPhoto"
        send_message_url = f"{cls.BASE_URL}{token}/sendMessage"

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                # 1. If image is available, try sending with sendPhoto
                if image_bytes:
                    # Telegram sendPhoto caption has a 1024 character limit.
                    # If the report is within limit, send photo with caption.
                    if len(report_text) <= 1024:
                        files = {"photo": ("chart.jpg", image_bytes, "image/jpeg")}
                        data = {
                            "chat_id": chat_id,
                            "caption": report_text,
                            "parse_mode": "HTML"
                        }
                        resp = await client.post(send_photo_url, data=data, files=files)
                        if resp.status_code == 200:
                            return True
                    else:
                        # Send photo first with a brief header, then send full detailed HTML report
                        brief_caption = (
                            f"⚡ <b>JRJ AI Assistant</b> | সিগন্যাল: <b>{result.signal.value}</b> ({result.confidence}%)\n"
                            f"⏱️ টাইমফ্রেম: {result.timeframe} | ট্রেন্ড: {result.trend}"
                        )
                        files = {"photo": ("chart.jpg", image_bytes, "image/jpeg")}
                        data = {"chat_id": chat_id, "caption": brief_caption, "parse_mode": "HTML"}
                        await client.post(send_photo_url, data=data, files=files)

                # 2. Send the detailed Bengali message
                msg_data = {
                    "chat_id": chat_id,
                    "text": report_text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                resp = await client.post(send_message_url, json=msg_data)
                return resp.status_code == 200

            except Exception as e:
                logger.error(f"Failed to deliver Telegram report: {str(e)}")
                return False

    @classmethod
    async def send_test_message(cls, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> tuple[bool, str]:
        """Validates bot token and chat ID by sending a test ping."""
        active_token = bot_token or storage_service.get_config("TELEGRAM_BOT_TOKEN", settings.TELEGRAM_BOT_TOKEN)
        active_chat = chat_id or storage_service.get_config("TELEGRAM_CHAT_ID", settings.TELEGRAM_CHAT_ID)

        if not active_token:
            return False, "Telegram Bot Token is missing."
        if not active_chat:
            return False, "Telegram Chat ID is missing."

        url = f"{cls.BASE_URL}{active_token}/sendMessage"
        test_text = (
            "🚀 <b>JRJ AI Assistant — কানেকশন সফল!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনার টেলিগ্রাম বট এবং চ্যাট আইডি সফলভাবে সংযুক্ত হয়েছে।\n"
            "এখন থেকে প্রতিটি চার্ট স্ক্যানের পর সম্পূর্ণ বাংলা বিশ্লেষণ এখানে পাঠানো হবে।"
        )
        async with httpx.AsyncClient(timeout=6.0) as client:
            try:
                resp = await client.post(url, json={
                    "chat_id": active_chat,
                    "text": test_text,
                    "parse_mode": "HTML"
                })
                data = resp.json()
                if resp.status_code == 200 and data.get("ok"):
                    return True, "Telegram test message sent successfully!"
                else:
                    return False, f"Telegram API error: {data.get('description', 'Unknown error')}"
            except Exception as e:
                return False, f"Connection failed: {str(e)}"
