# Backend hosting preparation

The FastAPI entry point is `run_server.py`; it reads `HOST` and `PORT` from the environment and binds Uvicorn accordingly. A container/service command can use `python run_server.py`, with the platform-provided `PORT` and `HOST=0.0.0.0`.

Set `GEMINI_API_KEY` and, if needed, `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the provider's secret manager. Environment-provided credentials take precedence over values saved by the local configuration endpoint. Never commit a real `.env` file. Configure `ANALYSIS_BUDGET_SECONDS=80` and `MAX_CONCURRENT_ANALYSES` for the service limits.

The backend stores configuration, usage, and scan history in SQLite under `DATA_DIR` (default: `backend/data`). A cloud instance needs a persistent volume mounted at that path or a database migration before redeploys/scale-out; local SQLite is not shared across multiple instances.

**Public deployment is not ready.** `/api/v1/config`, `/api/v1/telegram/test`, history, usage, and analysis currently do not have a complete user identity/rate-limiting policy. `REQUIRE_AUTH` is an optional single shared-key check for analysis only and must not be enabled by embedding that key in the Android APK. Before public exposure, put the API behind supported user authentication and rate limiting, protect administrative/configuration endpoints, review CORS, and choose durable shared storage. No cloud service has been selected or deployed.

After deploying and securing an HTTPS endpoint, configure its base URL in the Android app's backend URL setting (include the scheme and host, without `/api/v1`). The existing emulator default `http://10.0.2.2:8000` is only for local Android emulator development.
