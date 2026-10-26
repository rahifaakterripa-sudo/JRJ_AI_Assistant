import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.config import settings
from app.models.schemas import ScanHistoryItem, UsageStats, AnalysisResult

class StorageService:
    def __init__(self, db_path: Optional[Path] = None):
        data_dir = settings.get_data_dir()
        self.db_path = db_path or (data_dir / "jrj_assistant.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scan_history (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    timeframe TEXT NOT NULL,
                    trend TEXT NOT NULL,
                    support_resistance TEXT NOT NULL,
                    two_candle_gap TEXT NOT NULL,
                    price_action TEXT NOT NULL,
                    reasons TEXT NOT NULL,
                    risk_warning TEXT NOT NULL,
                    bengali_summary TEXT NOT NULL,
                    telegram_sent INTEGER NOT NULL DEFAULT 0,
                    latency_ms REAL NOT NULL DEFAULT 0.0,
                    image_filename TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dynamic_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_scan(self, result: AnalysisResult, image_filename: Optional[str] = None) -> str:
        scan_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO scan_history (
                    id, timestamp, signal, confidence, timeframe, trend,
                    support_resistance, two_candle_gap, price_action,
                    reasons, risk_warning, bengali_summary, telegram_sent,
                    latency_ms, image_filename
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                result.timestamp,
                result.signal.value,
                result.confidence,
                result.timeframe,
                result.trend,
                result.support_resistance,
                result.two_candle_gap,
                result.price_action,
                json.dumps(result.reasons, ensure_ascii=False),
                result.risk_warning,
                result.bengali_summary,
                1 if result.telegram_sent else 0,
                result.latency_ms,
                image_filename
            ))
            conn.commit()
        return scan_id

    def get_history(self, limit: int = 50, offset: int = 0) -> List[ScanHistoryItem]:
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, timestamp, signal, confidence, timeframe, trend,
                       bengali_summary, telegram_sent, latency_ms
                FROM scan_history
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()

            items = []
            for r in rows:
                items.append(ScanHistoryItem(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    signal=r["signal"],
                    confidence=r["confidence"],
                    timeframe=r["timeframe"],
                    trend=r["trend"],
                    summary=r["bengali_summary"],
                    telegram_sent=bool(r["telegram_sent"]),
                    latency_ms=r["latency_ms"]
                ))
            return items

    def get_history_count(self) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM scan_history").fetchone()
            return row["total"] if row else 0

    def get_usage_stats(self) -> UsageStats:
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS count FROM scan_history").fetchone()["count"]
            buys = conn.execute("SELECT COUNT(*) AS count FROM scan_history WHERE signal = 'BUY'").fetchone()["count"]
            sells = conn.execute("SELECT COUNT(*) AS count FROM scan_history WHERE signal = 'SELL'").fetchone()["count"]
            waits = conn.execute("SELECT COUNT(*) AS count FROM scan_history WHERE signal = 'WAIT'").fetchone()["count"]
            avg_lat = conn.execute("SELECT AVG(latency_ms) AS avg_lat FROM scan_history").fetchone()["avg_lat"] or 0.0
            last_ts_row = conn.execute("SELECT timestamp FROM scan_history ORDER BY timestamp DESC LIMIT 1").fetchone()
            last_ts = last_ts_row["timestamp"] if last_ts_row else None

            # Estimated ~800 tokens per chart vision request (input image + system prompt + output JSON)
            est_tokens = total * 800

            return UsageStats(
                total_scans=total,
                successful_scans=total,
                failed_scans=0,
                buy_count=buys,
                sell_count=sells,
                wait_count=waits,
                avg_latency_ms=round(avg_lat, 2),
                estimated_tokens_used=est_tokens,
                last_scan_timestamp=last_ts
            )

    def set_config(self, key: str, value: str):
        with self._get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO dynamic_config (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_config(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM dynamic_config WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

storage_service = StorageService()
