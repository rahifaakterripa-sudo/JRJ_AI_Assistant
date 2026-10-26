import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jrj.main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional Cyberpunk Trading Chart Analysis Engine with Gemini Vision & Telegram reporting."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def attach_analysis_deadline(request: Request, call_next):
    if request.url.path == "/api/v1/analyze":
        # Start before multipart parsing so upload time counts against the same budget.
        request.state.analysis_deadline = time.monotonic() + settings.ANALYSIS_BUDGET_SECONDS
    return await call_next(request)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global unhandled exception path=%s category=%s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "signal": "WAIT",
            "confidence": 0,
            "error": "Internal server processing failure. WAIT signal preserved.",
        }
    )

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root_info():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "analyze": "/api/v1/analyze",
            "history": "/api/v1/history",
            "usage": "/api/v1/usage",
            "config": "/api/v1/config",
            "telegram_test": "/api/v1/telegram/test"
        }
    }
