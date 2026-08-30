"""
Configuration and Environment Management for SupportFlow AI.

Loads environment variables from .env and provides secure configuration helpers
without printing or logging sensitive credentials.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load the root .env file
ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


def get_gemini_api_key() -> str:
    """
    Securely retrieves the Google Gemini API key from environment variables.
    Returns empty string if not configured.
    """
    return os.getenv("GEMINI_API_KEY", "").strip()


def is_gemini_configured() -> bool:
    """
    Checks if a Gemini API key is present and non-empty.
    """
    key = get_gemini_api_key()
    return bool(key and key != "your_api_key_here")


# AI Model Configuration
# Uses gemini-3-flash-preview as the active supported flash model
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
