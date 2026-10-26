import asyncio
import hashlib
import logging
import time
from typing import Optional

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import AnalysisResult, AnalyzeResponse
from app.services.gemini_analyzer import AnalysisProviderError, GeminiAnalyzer
from app.services.image_processor import ImageProcessingError, ImageProcessor
from app.services.storage import storage_service
from app.services.telegram_service import TelegramService

router = APIRouter()
logger = logging.getLogger("jrj.analyze")
_recent_requests: dict[str, float] = {}
_in_flight: set[str] = set()
_request_lock = asyncio.Lock()
_image_processing_slots = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSES)
_MAX_DUPLICATE_ENTRIES = 512
_MAX_TELEGRAM_TASKS = 4
_telegram_pending = 0
_telegram_tasks: set[asyncio.Task] = set()


def _schedule_telegram(result: AnalysisResult, image_bytes: bytes) -> bool:
    """Queue a bounded best-effort notification without delaying the API response."""
    global _telegram_pending
    if _telegram_pending >= _MAX_TELEGRAM_TASKS:
        logger.info("Telegram report skipped because notification capacity is full")
        return False
    _telegram_pending += 1

    async def deliver():
        global _telegram_pending
        try:
            if await TelegramService.send_analysis_report(result, image_bytes):
                result.telegram_sent = True
        except Exception as exc:
            logger.warning("Telegram report failed category=%s", type(exc).__name__)
        finally:
            _telegram_pending -= 1

    task = asyncio.create_task(deliver())
    _telegram_tasks.add(task)
    task.add_done_callback(_telegram_tasks.discard)
    return True


def _failure(status_code: int, status: str, message: str, started: float) -> JSONResponse:
    payload = AnalyzeResponse(
        success=False,
        signal="WAIT",
        confidence=0,
        error=message,
        status=status,
        execution_time_seconds=round(time.monotonic() - started, 2),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


async def _preprocess_bounded(image_bytes: bytes, deadline: float):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError
    await asyncio.wait_for(_image_processing_slots.acquire(), timeout=remaining)
    worker = asyncio.create_task(asyncio.to_thread(ImageProcessor.validate_and_preprocess, image_bytes))
    try:
        return await asyncio.shield(worker)
    finally:
        if worker.done():
            _image_processing_slots.release()
        else:
            # Keep the slot occupied until a cancelled Pillow worker really exits.
            worker.add_done_callback(lambda _: _image_processing_slots.release())


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_chart(
    request: Request,
    file: UploadFile = File(..., description="Chart screenshot captured by Android app"),
    client_timestamp: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    started = time.monotonic()
    deadline = getattr(request.state, "analysis_deadline", started + settings.ANALYSIS_BUDGET_SECONDS)
    img_hash = None
    acquired = False
    try:
        async with asyncio.timeout_at(deadline):
            if settings.REQUIRE_AUTH and (not settings.API_SECRET_KEY or x_api_key != settings.API_SECRET_KEY):
                return _failure(401, "UNAUTHORIZED", "Unauthorized client request.", started)

            raw_bytes = await file.read()
            if not raw_bytes:
                return _failure(400, "INVALID_IMAGE", "Empty chart image uploaded.", started)

            img_hash = hashlib.sha256(raw_bytes).hexdigest()
            now = time.monotonic()
            async with _request_lock:
                for old_hash, seen_at in list(_recent_requests.items()):
                    if now - seen_at > 30:
                        _recent_requests.pop(old_hash, None)
                if img_hash in _in_flight or (img_hash in _recent_requests and now - _recent_requests[img_hash] < 4):
                    return _failure(409, "DUPLICATE_SCAN", "This chart was just submitted. Wait before scanning it again.", started)
                if len(_recent_requests) >= _MAX_DUPLICATE_ENTRIES:
                    oldest = min(_recent_requests, key=_recent_requests.get)
                    _recent_requests.pop(oldest, None)
                _in_flight.add(img_hash)
                _recent_requests[img_hash] = now
                acquired = True

            try:
                processed_bytes, _ = await _preprocess_bounded(raw_bytes, deadline)
            except ImageProcessingError as exc:
                return _failure(422, "INVALID_IMAGE", str(exc), started)

            result = await GeminiAnalyzer.analyze_chart(processed_bytes, deadline=deadline)
            result.latency_ms = round((time.monotonic() - started) * 1000, 2)

            _schedule_telegram(result, processed_bytes)
            try:
                await asyncio.to_thread(storage_service.save_scan, result)
            except Exception as exc:
                logger.warning("Analysis history persistence failed category=%s", type(exc).__name__)

            elapsed = time.monotonic() - started
            logger.info("Analysis completed elapsed_seconds=%.2f remaining_seconds=%.2f signal=%s", elapsed, max(0, deadline-time.monotonic()), result.signal.value)
            return AnalyzeResponse(
                success=True,
                signal=result.signal.value,
                confidence=result.confidence,
                data=result,
                status="SUCCESS",
                execution_time_seconds=round(elapsed, 2),
            )
    except TimeoutError:
        logger.warning("Analysis deadline exceeded elapsed_seconds=%.2f", time.monotonic() - started)
        return _failure(504, "DEADLINE_EXCEEDED", "The analysis exceeded its 80-second deadline. Please try again.", started)
    except AnalysisProviderError as exc:
        logger.warning("Analysis failed status=%s elapsed_seconds=%.2f", exc.status, time.monotonic() - started)
        status_code = 504 if exc.status == "DEADLINE_EXCEEDED" else 502
        return _failure(status_code, exc.status, exc.public_message, started)
    except Exception as exc:
        logger.error("Analysis failed category=%s elapsed_seconds=%.2f", type(exc).__name__, time.monotonic() - started)
        return _failure(500, "INTERNAL_ERROR", "Analysis could not be completed.", started)
    finally:
        if acquired and img_hash:
            async with _request_lock:
                _in_flight.discard(img_hash)
