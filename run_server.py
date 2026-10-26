#!/usr/bin/env python3
"""
JRJ AI Assistant - Server Launcher
Usage:
    python run_server.py
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Listening on http://{settings.HOST}:{settings.PORT}")
    print(f"Swagger Documentation: http://localhost:{settings.PORT}/docs")
    print("=" * 60)
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False
    )
