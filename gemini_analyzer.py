import asyncio
import json
import logging
import os
import time
from typing import Any

import google.generativeai as genai
from google.api_core.retry import Retry, if_transient_error
from pydantic import ValidationError

from app.config import settings
from app.models.schemas import AnalysisResult
from app.services.storage import storage_service

logger = logging.getLogger("jrj.gemini")
_analysis_slots = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSES)

GEMINI_SYSTEM_PROMPT = """Analyze only the supplied chart screenshot. Do not claim live market-data access,
hidden candles, prices, indicators, or timeframes that are not legible in the image. Describe
visible market structure, candle behavior, swings, support/resistance or zones when identifiable,
breakouts/rejections/retests, momentum/volatility clues, conflicting evidence and uncertainty.
Do not invent details. Use WAIT when evidence is insufficient or conflicting. Confidence is an
evidence-strength score, not a probability of profit; use 0 for insufficient evidence. Return only
one JSON object with exactly these keys and correct types:
signal (BUY|SELL|WAIT), confidence (integer 0..100), timeframe, trend,
support_resistance, two_candle_gap, price_action, reasons (non-empty string array),
risk_warning, bengali_summary, market_structure, bullish_evidence (string array),
bearish_evidence (string array), uncertainty (non-empty string array).
For insufficient evidence use WAIT, confidence 0, and explain what cannot be read."""


class AnalysisProviderError(Exception):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status
        self.public_message = message


class GeminiAnalyzer:
    @classmethod
    def get_api_key(cls) -> str:
        # Environment secrets take precedence for cloud deployments.
        return settings.GEMINI_API_KEY.strip() or storage_service.get_config("GEMINI_API_KEY", "").strip()

    @classmethod
    def get_model_name(cls) -> str:
        configured_model = os.getenv("GEMINI_MODEL", "").strip()
        return configured_model or storage_service.get_config("GEMINI_MODEL", settings.GEMINI_MODEL).strip() or "gemini-2.5-flash"

    @classmethod
    async def analyze_chart(cls, image_bytes: bytes, deadline: float | None = None) -> AnalysisResult:
        started = time.monotonic()
        deadline = deadline if deadline is not None else started + settings.ANALYSIS_BUDGET_SECONDS
        api_key = cls.get_api_key()
        if not api_key:
            raise AnalysisProviderError("PROVIDER_NOT_CONFIGURED", "Gemini analysis is not configured.")

        remaining = deadline - time.monotonic() - settings.ANALYSIS_RESPONSE_RESERVE_SECONDS
        if remaining <= 0:
            raise AnalysisProviderError("DEADLINE_EXCEEDED", "Analysis deadline exceeded.")

        acquired = False
        try:
            await asyncio.wait_for(_analysis_slots.acquire(), timeout=remaining)
            acquired = True
            genai.configure(api_key=api_key)
            model_name = cls.get_model_name()
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=GEMINI_SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            )
            contents = [
                "Analyze the submitted chart image using the required JSON schema.",
                {"mime_type": "image/jpeg", "data": image_bytes},
            ]
            response = None
            for attempt in range(2):
                remaining = deadline - time.monotonic() - settings.ANALYSIS_RESPONSE_RESERVE_SECONDS
                if remaining <= 0:
                    raise AnalysisProviderError("DEADLINE_EXCEEDED", "Analysis deadline exceeded.")
                logger.info("Gemini request model=%s attempt=%s remaining_seconds=%.2f", model_name, attempt + 1, remaining)
                try:
                    response = await asyncio.wait_for(
                        model.generate_content_async(
                            contents,
                            request_options={
                                "timeout": remaining,
                                # Disable hidden SDK retries; the explicit single retry below shares our deadline.
                                "retry": Retry(predicate=lambda _: False, initial=0.1, maximum=0.1, timeout=remaining),
                            },
                        ),
                        timeout=remaining,
                    )
                    break
                except Exception as exc:
                    if attempt != 0 or not if_transient_error(exc):
                        raise
                    retry_delay = min(0.25, max(0.0, deadline - time.monotonic() - settings.ANALYSIS_RESPONSE_RESERVE_SECONDS - 0.05))
                    if retry_delay <= 0:
                        raise asyncio.TimeoutError from exc
                    logger.warning("Gemini transient failure; one bounded retry will use remaining deadline")
                    await asyncio.sleep(retry_delay)
            raw_text = getattr(response, "text", None)
            if not isinstance(raw_text, str) or not raw_text.strip():
                raise AnalysisProviderError("INVALID_PROVIDER_RESPONSE", "Gemini returned an empty analysis.")
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].removesuffix("```").strip()
            parsed: Any = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError("JSON root must be an object")
            required_keys = {
                "signal", "confidence", "timeframe", "trend", "support_resistance",
                "two_candle_gap", "price_action", "reasons", "risk_warning",
                "bengali_summary", "market_structure", "bullish_evidence",
                "bearish_evidence", "uncertainty",
            }
            if set(parsed) != required_keys:
                raise ValueError("response keys do not match the required report schema")
            for key in ("reasons", "bullish_evidence", "bearish_evidence", "uncertainty"):
                if not isinstance(parsed[key], list) or any(
                    not isinstance(item, str) or not item.strip() for item in parsed[key]
                ):
                    raise ValueError(f"{key} must contain non-empty strings")
            parsed["signal"] = str(parsed.get("signal", "")).upper()
            result = AnalysisResult.model_validate(parsed)
            if result.signal.value not in {"BUY", "SELL", "WAIT"}:
                raise ValueError("invalid signal")
            if not all(value.strip() for value in (
                result.timeframe, result.trend, result.support_resistance, result.two_candle_gap,
                result.price_action, result.risk_warning, result.bengali_summary,
                result.market_structure,
            )) or not result.reasons or not result.uncertainty:
                raise ValueError("required report fields must be non-empty")
            if result.confidence == 0 and result.signal.value != "WAIT":
                raise ValueError("insufficient-evidence confidence requires WAIT")
            result.latency_ms = round((time.monotonic() - started) * 1000, 2)
            logger.info("Gemini analysis validated model=%s elapsed_ms=%.0f signal=%s", model_name, result.latency_ms, result.signal.value)
            return result
        except asyncio.TimeoutError as exc:
            logger.warning("Gemini analysis deadline reached elapsed_ms=%.0f", (time.monotonic() - started) * 1000)
            raise AnalysisProviderError("DEADLINE_EXCEEDED", "Analysis deadline exceeded while waiting for Gemini.") from exc
        except AnalysisProviderError:
            raise
        except json.JSONDecodeError as exc:
            logger.warning("Gemini response invalid_json elapsed_ms=%.0f", (time.monotonic() - started) * 1000)
            raise AnalysisProviderError("INVALID_PROVIDER_RESPONSE", "Gemini returned an invalid analysis response.") from exc
        except ValueError as exc:
            logger.warning("Gemini response schema_invalid elapsed_ms=%.0f", (time.monotonic() - started) * 1000)
            raise AnalysisProviderError("INVALID_PROVIDER_RESPONSE", "Gemini returned an incomplete analysis.") from exc
        except ValidationError as exc:
            logger.warning("Gemini response schema_invalid elapsed_ms=%.0f", (time.monotonic() - started) * 1000)
            raise AnalysisProviderError("INVALID_PROVIDER_RESPONSE", "Gemini returned an incomplete analysis.") from exc
        except Exception as exc:
            category = type(exc).__name__
            logger.error("Gemini provider failure category=%s elapsed_ms=%.0f", category, (time.monotonic() - started) * 1000)
            # No automatic fallback: the old fallback used a second unbounded synchronous call.
            raise AnalysisProviderError("PROVIDER_ERROR", "Gemini could not complete the analysis.") from exc
        finally:
            if acquired:
                _analysis_slots.release()
