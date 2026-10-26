import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "JRJ AI Assistant Backend"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Gemini Vision
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Security
    API_SECRET_KEY: str = ""
    REQUIRE_AUTH: bool = False  # Set to True in production; allows development access

    # Market Platform
    DEFAULT_MARKET_URL: str = "https://market-qx.info/en/trade"

    # Operational Constraints
    ANALYSIS_BUDGET_SECONDS: int = Field(default=80, gt=0)
    ANALYSIS_RESPONSE_RESERVE_SECONDS: int = Field(default=5, ge=0)
    MAX_CONCURRENT_ANALYSES: int = Field(default=4, ge=1)
    DATA_DIR: Path = BASE_DIR / "data"

    def get_data_dir(self) -> Path:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return self.DATA_DIR

settings = Settings()
