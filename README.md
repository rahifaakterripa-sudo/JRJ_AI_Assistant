# JRJ AI Assistant — Cyberpunk Chart Analysis System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Kotlin](https://img.shields.io/badge/Kotlin-2.0+-7F52FF.svg)](https://kotlinlang.org)
[![Android SDK](https://img.shields.io/badge/Android%20SDK-API%2035-3DDC84.svg)](https://developer.android.com)
[![Gemini Vision](https://img.shields.io/badge/Gemini-2.5%20Flash%20Vision-4285F4.svg)](https://ai.google.dev)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bengali%20Reports-0088CC.svg)](https://core.telegram.org/bots)

**JRJ AI Assistant** is an elite, full-stack trading chart analysis assistant designed with a high-performance **Cyberpunk Black & Gold** aesthetic. It integrates an Android Kotlin application featuring live market WebView, a 3D-styled floating golden PRO scan button, sweeping neon-gold laser scan animations, authorized screen capture, a 12-second countdown decision HUD, and a secure Python FastAPI backend powered by Google Gemini Vision and automated Bengali Telegram reporting.

---

## ⚡ Core Features

1. **Cyberpunk Black & Gold UI**: Premium obsidian background (`#0B0B0F`), metallic gold accents (`#FFD700`, `#F5A623`), glowing neon laser beams, and high-contrast signal badges (`BUY` 🟢, `SELL` 🔴, `WAIT` 🟡).
2. **Integrated Market WebView**: High-performance WebView configured for trading platforms (Quotex / market-qx.info, TradingView) with full JavaScript, DOM storage, and responsive layout.
3. **Draggable 3D Floating PRO Button**: 3D beveled metallic golden button that can be positioned anywhere on the screen or tapped to trigger instant chart scanning.
4. **Sweeping Laser Scan Animation**: Hardware-accelerated Canvas animation with a sweeping vertical neon-gold laser beam and particle trails across the chart viewport.
5. **Authorized Chart Capture**: Authorized capture pipeline with MediaProjection Foreground Service and high-fidelity PixelCopy/View snapshot fallback — requiring zero manual screenshot uploads.
6. **Gemini Vision Technical Analysis**:
   - Market trend identification (Uptrend, Downtrend, Consolidation).
   - Horizontal and dynamic Support & Resistance zones.
   - Price action, candlestick shapes, and rejection wicks.
   - **Two-Candle Gap Setup**: Specialized detection of fair value gaps / liquidity voids between Candle 1 and Candle 3 wicks.
   - Strictly outputs `BUY`, `SELL`, or `WAIT`. Never invents signals or fabricates 100% win rates.
7. **Strict 12-Second User HUD**: Displays animated 12-second progress bar, confidence rating, timeframe, confluence factors, and Bengali summary.
8. **Automated Bengali Telegram Reports**: Sends rich HTML/Markdown analysis reports and chart photos directly to the user's Telegram channel or bot chat.
9. **Offline Scan History**: Persistent local database (Room SQLite) to inspect past scans, signals, and timestamps.
10. **Backend Security**: Secrets (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`) stored strictly on the backend, never hardcoded in the frontend.

---

## 📁 Project Structure

```text
d:\JRJ_AI_Assistant\
  ├── backend/                      # Python FastAPI Backend
  │   ├── app/
  │   │   ├── api/v1/               # REST Endpoints (/analyze, /history, /usage, /config, /telegram)
  │   │   ├── models/schemas.py     # Pydantic Schemas & DTOs
  │   │   ├── services/
  │   │   │   ├── gemini_analyzer.py # Gemini Vision Engine with 2-Candle Gap logic
  │   │   │   ├── telegram_service.py# Bengali Telegram Report Service
  │   │   │   ├── image_processor.py # Image validation & optimization
  │   │   │   └── storage.py         # SQLite persistence & usage tracking
  │   │   ├── config.py             # Settings & Environment variables
  │   │   └── main.py               # FastAPI App & CORS configuration
  │   ├── tests/                    # 10 Pytest Automated Tests
  │   ├── requirements.txt
  │   ├── run_server.py             # Fast backend runner
  │   └── .env.example
  │
  ├── android/                      # Android Kotlin Project
  │   ├── app/
  │   │   ├── src/main/java/com/jrj/aiassistant/
  │   │   │   ├── data/             # Retrofit client, Room DB & ScanRepository
  │   │   │   ├── service/          # MediaProjection ScreenCaptureService
  │   │   │   ├── ui/
  │   │   │   │   ├── components/   # FloatingProButton, LaserScannerView, DecisionHudDialog
  │   │   │   │   ├── main/         # MainActivity & MainViewModel
  │   │   │   │   ├── history/      # HistoryActivity & HistoryAdapter
  │   │   │   │   └── settings/     # SettingsActivity
  │   │   │   └── utils/            # PreferencesManager & SoundManager (AudioTrack synthesis)
  │   │   ├── src/main/res/         # Cyberpunk layouts, drawables, styles, colors
  │   │   └── build.gradle.kts      # Module Gradle config (SDK 35, Java 17)
  │   ├── build.gradle.kts          # Root Gradle script
  │   ├── settings.gradle.kts
  │   └── gradlew.bat               # Gradle Wrapper
  │
  └── README.md                     # Complete Documentation
```

---

## 🚀 Quick Start Guide

### Step 1: Set Up & Run the Backend

1. Navigate to the backend directory:
   ```powershell
   cd d:\JRJ_AI_Assistant\backend
   ```
2. Copy the example environment file:
   ```powershell
   copy .env.example .env
   ```
3. Edit `.env` and fill in your keys:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...your_bot_token
   TELEGRAM_CHAT_ID=your_telegram_chat_id
   ```
4. Run the backend tests to ensure everything is working:
   ```powershell
   python -m pytest -v
   ```
5. Launch the backend server:
   ```powershell
   python run_server.py
   ```
   The backend will be live at: `http://localhost:8000`  
   Interactive API Docs: `http://localhost:8000/docs`

---

### Step 2: Build the Android Application

1. Open PowerShell and set Java 17:
   ```powershell
   $env:JAVA_HOME = "C:\Users\USER X\.jdk17\jdk-17.0.20.1+1"
   $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
   cd d:\JRJ_AI_Assistant\android
   ```
2. Build the Debug APK:
   ```powershell
   .\gradlew.bat assembleDebug
   ```
3. The compiled APK will be generated at:
   ```text
   d:\JRJ_AI_Assistant\android\app\build\outputs\apk\debug\app-debug.apk
   ```

---

### Step 3: Connecting App to Backend

- **On Android Emulator**:
  Use default URL `http://10.0.2.2:8000` (maps to host PC `localhost:8000`).
- **On Physical Android Device (Wi-Fi)**:
  Find your PC's IP address (`ipconfig`, e.g. `192.168.1.105`), and in the app Settings screen, set Backend URL to:
  `http://192.168.1.105:8000`

---

## 📊 Bengali Telegram Report Format

Each chart scan automatically formats a report in Bengali:

```html
⚡ JRJ AI ASSISTANT — প্রফেশনাল চার্ট বিশ্লেষণ রিপোর্ট ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ট্রেড সিগন্যাল: 🟢 BUY (কল / আপ এন্ট্রি)
📊 কনফিডেন্স লেভেল: 85%
⏱️ প্রস্তাবিত টাইমফ্রেম: 1m
━━━━━━━━━━━━━━━━━━━━━━━━━
📈 মার্কেট ট্রেন্ড: Bullish Uptrend
🛡️ সাপোর্ট ও রেজিস্ট্যান্স: Support zone 1.08450 holding firmly
🕯️ প্রাইস অ্যাকশন: Hammer pin bar formed at support
🔍 টু-ক্যান্ডেল গ্যাপ (Two-Candle Gap): Bullish liquidity gap mitigated
━━━━━━━━━━━━━━━━━━━━━━━━━
📝 মূল কনফ্লুয়েন্স ও যুক্তি:
  ▫️ আপট্রেন্ড মার্কেট স্ট্রাকচার অক্ষুণ্ণ রয়েছে
  ▫️ টু-ক্যান্ডেল গ্যাপ ফিলাপের পর স্ট্রং বায়ারদের এন্ট্রি
━━━━━━━━━━━━━━━━━━━━━━━━━
💡 বাংলা সারসংক্ষেপ: মার্কেট সাপোর্ট রিজেক্ট করে বায়ারদের নিয়ন্ত্রণে আছে।
⚠️ রিস্ক ম্যানেজমেন্ট ও সতর্কতা: মূলধনের ২-৩% এর বেশি কখনো এক ট্রেডে বিনিয়োগ করবেন না।
━━━━━━━━━━━━━━━━━━━━━━━━━
🕒 সময়: 2026-10-25T16:00:00Z | JRJ Cyber Core v1.0
```
