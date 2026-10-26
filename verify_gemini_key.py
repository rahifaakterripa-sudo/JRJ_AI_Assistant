#!/usr/bin/env python3
"""
JRJ AI Assistant - Gemini API Key Verification Utility
Checks whether GEMINI_API_KEY is configured in backend/.env
and tests connectivity to the Gemini API without leaking secrets.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

env_path = backend_dir / ".env"
load_dotenv(env_path, override=True)

from app.config import settings
from app.services.gemini_analyzer import GeminiAnalyzer

def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "Not Set"
    return f"{key[:6]}...{key[-4:]}"

def verify_key():
    print("=" * 60)
    print("  JRJ AI Assistant — Gemini Configuration Verification")
    print("=" * 60)

    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"

    print(f"Target .env file : {env_path}")
    print(f"Configured Model : {model_name}")
    print(f"Detected Key     : {mask_key(api_key)}")

    if not api_key.strip():
        print("\n[STATUS: MISSING KEY]")
        print("Please open backend/.env and paste your key in:")
        print("GEMINI_API_KEY=your_actual_gemini_api_key_here\n")
        return False

    print("\nTesting connection with Google Gemini API...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key.strip())
        
        # Test listing available models or lightweight call
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Ping")
        
        print("[STATUS: SUCCESS] ✓ Real Gemini API Key is active, authorized, and functional!")
        print(f"Test Response snippet: {response.text.strip()[:40]}...")
        return True
    except Exception as e:
        print(f"\n[STATUS: AUTH ERROR] Connection failed: {str(e)}")
        print("Please verify that your Google AI Studio API key is active and correctly typed.")
        return False

if __name__ == "__main__":
    verify_key()
