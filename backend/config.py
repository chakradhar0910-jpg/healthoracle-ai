"""
HealthOracle AI — Settings Configuration
========================================
Parses environment variables to define service configurations for
the FastAPI app, database path, logging configurations, and OCR systems.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR = BASE_DIR.parent.resolve()

# Load environment variables from .env file
load_dotenv(WORKSPACE_DIR / ".env")

# ── API Server Settings ───────────────────────────────────────────────────
API_HOST = os.getenv("HEALTHORACLE_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("HEALTHORACLE_API_PORT", "8000"))
DEBUG = True # Forced debug mode for troubleshooting

# ── CORS Settings ─────────────────────────────────────────────────────────
# Split by commas to support multiple origins (e.g. http://localhost:3000,http://localhost:5173)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("HEALTHORACLE_CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = os.getenv("HEALTHORACLE_CORS_ALLOW_CREDENTIALS", "false").lower() in (
    "true",
    "1",
)

# ── Logging Settings ──────────────────────────────────────────────────────
LOG_LEVEL = "DEBUG"
LOG_DIR = WORKSPACE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE_PATH = LOG_DIR / "app.log"

# ── Database Settings ─────────────────────────────────────────────────────
# Default database path inside the backend folder
DB_PATH = WORKSPACE_DIR / "backend" / "health_oracle.db"
DATABASE_URL = os.getenv("HEALTHORACLE_DATABASE_URL", f"sqlite:///{DB_PATH}")

# ── Model Settings ────────────────────────────────────────────────────────
MODELS_DIR = BASE_DIR / "models"
DB_MODEL_PATH = MODELS_DIR / "diabetes_model.pkl"
HD_MODEL_PATH = MODELS_DIR / "heart_model.pkl"
DB_SCALER_PATH = MODELS_DIR / "diabetes_scaler.pkl"
HD_SCALER_PATH = MODELS_DIR / "heart_scaler.pkl"

# ── OCR / Tesseract Settings ──────────────────────────────────────────────
# Force fallback mock OCR if true, or auto-detect if false
FORCE_OCR_MOCK = os.getenv("HEALTHORACLE_FORCE_OCR_MOCK", "false").lower() in ("true", "1")
TESSERACT_CMD = os.getenv("HEALTHORACLE_TESSERACT_CMD", "")

# ── Gemini / Local AI (Ollama) Settings ───────────────────────────────────
# Set via environment variable or .env file — NEVER hardcode keys here
GEMINI_API_KEY = os.getenv("HEALTHORACLE_GEMINI_API_KEY", "")

# Local AI / Ollama Settings
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1")
DEFAULT_AI_PROVIDER = "ollama" if USE_OLLAMA else os.getenv("HEALTHORACLE_DEFAULT_AI_PROVIDER", "gemini")
OLLAMA_ENDPOINT = os.getenv("HEALTHORACLE_OLLAMA_ENDPOINT", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or os.getenv("HEALTHORACLE_OLLAMA_MODEL", "llama3.1:8b")
