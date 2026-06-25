"""
config.py
---------
Centralised, secure configuration loader.

All secrets (API keys, model names, Google Sheet ID) are read from a local
`.env` file using python-dotenv. Nothing sensitive is ever hard-coded.
"""

import os
from dotenv import load_dotenv

# Load variables from the local .env file into the environment.
load_dotenv()

# --- Groq API (PRIMARY provider) -----------------------------------------
# The chatbot talks to Groq first (fast, free, strong Arabic + tool calling)
# and only falls back to Gemini if every Groq model fails.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Primary Groq model (tried first) and a secondary Groq model (tried next).
# openai/gpt-oss-120b was chosen for the best Arabic + reliable function calling.
GROQ_MODEL_1 = os.getenv("GROQ_MODEL_1", "openai/gpt-oss-120b").strip()
GROQ_MODEL_2 = os.getenv("GROQ_MODEL_2", "qwen/qwen3-32b").strip()

# --- Gemini API (FALLBACK provider) --------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Gemini fallback models, tried in order only after all Groq models fail.
MODEL_GEMINI_1 = os.getenv("MODEL_GEMINI_1", "gemini-2.5-flash").strip()
MODEL_GEMINI_2 = os.getenv("MODEL_GEMINI_2", "gemini-2.0-flash").strip()

# --- Google Sheets -------------------------------------------------------
# Service-account credentials file (downloaded from Google Cloud Console).
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json").strip()

# The ID of the Google Sheet (the long string in the sheet URL between /d/ and /edit).
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()

# Name of the worksheet/tab inside the spreadsheet.
GOOGLE_WORKSHEET_NAME = os.getenv("GOOGLE_WORKSHEET_NAME", "Reservations").strip()


def groq_is_configured() -> bool:
    """True when we have a Groq API key (the primary provider)."""
    return bool(GROQ_API_KEY)


def gemini_is_configured() -> bool:
    """True when we have everything needed to talk to Gemini (the fallback)."""
    return bool(GEMINI_API_KEY)


def chatbot_is_configured() -> bool:
    """True when at least one provider (Groq or Gemini) is ready to use."""
    return groq_is_configured() or gemini_is_configured()


def sheets_is_configured() -> bool:
    """True when Google Sheets storage is fully configured."""
    return bool(GOOGLE_SHEET_ID) and os.path.exists(GOOGLE_CREDENTIALS_FILE)
