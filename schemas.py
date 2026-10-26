from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

class TrendType(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    UNKNOWN = "UNKNOWN"

class AnalysisResult(BaseModel):
    signal: SignalType = Field(..., description="Actionable trading signal: BUY, SELL, or WAIT")
    confidence: int = Field(..., strict=True, ge=0, le=100, description="Evidence-strength score, not a win probability (0-100)")
    timeframe: str = Field(..., description="Visible timeframe or explicit statement that it is unreadable")
    trend: str = Field(..., description="Identified market trend (e.g., Bullish, Bearish, Sideways Consolidation)")
    support_resistance: str = Field(..., description="Identified key support and resistance levels")
    two_candle_gap: str = Field(..., description="Detailed observation of the requested two-candle gap / imbalance setup")
    price_action: str = Field(..., description="Price action notes including candle wicks, body rejection, and momentum")
    reasons: List[str] = Field(default_factory=list, description="Top confluence factors backing the signal")
    risk_warning: str = Field(..., description="Risk warning and money management reminder")
    bengali_summary: str = Field(..., description="Concise analysis summary in Bengali for quick trader context")
    market_structure: str = Field(default="", description="Market structure visible in the submitted screenshot")
    bullish_evidence: List[str] = Field(default_factory=list)
    bearish_evidence: List[str] = Field(default_factory=list)
    uncertainty: List[str] = Field(default_factory=list)
    telegram_sent: bool = Field(default=False, description="Whether the detailed report was sent to Telegram")
    latency_ms: float = Field(default=0.0, description="Processing latency in milliseconds")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AnalyzeResponse(BaseModel):
    success: bool
    signal: str = "WAIT"
    confidence: int = 0
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    status: Optional[str] = None

class ScanHistoryItem(BaseModel):
    id: str
    timestamp: str
    signal: str
    confidence: int
    timeframe: str
    trend: str
    summary: str
    telegram_sent: bool
    latency_ms: float

class HistoryResponse(BaseModel):
    total: int
    items: List[ScanHistoryItem]

class UsageStats(BaseModel):
    total_scans: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    buy_count: int = 0
    sell_count: int = 0
    wait_count: int = 0
    avg_latency_ms: float = 0.0
    estimated_tokens_used: int = 0
    last_scan_timestamp: Optional[str] = None

class TelegramTestRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    message: Optional[str] = None

class TelegramTestResponse(BaseModel):
    success: bool
    message: str
    chat_id: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    default_market_url: Optional[str] = None

class ConfigResponse(BaseModel):
    has_gemini_key: bool
    gemini_model: str
    has_telegram_token: bool
    telegram_chat_id: str
    default_market_url: str
    scan_timeout_seconds: int
