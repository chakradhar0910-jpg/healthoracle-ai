"""
HealthOracle AI — Settings Configuration
========================================
Parses environment variables to define service configurations for
the FastAPI app, database path, logging configurations, and OCR systems.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR = BASE_DIR.parent.resolve()

# ── API Server Settings ───────────────────────────────────────────────────
API_HOST = os.getenv("HEALTHORACLE_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("HEALTHORACLE_API_PORT", "8000"))
DEBUG = os.getenv("HEALTHORACLE_DEBUG", "false").lower() in ("true", "1")

# ── CORS Settings ─────────────────────────────────────────────────────────
# Split by commas to support multiple origins (e.g. http://localhost:3000,http://localhost:5173)
CORS_ORIGINS = [
    origin.strip() for origin in os.getenv("HEALTHORACLE_CORS_ORIGINS", "*").split(",") if origin.strip()
]
CORS_ALLOW_CREDENTIALS = os.getenv("HEALTHORACLE_CORS_ALLOW_CREDENTIALS", "false").lower() in ("true", "1")

# ── Logging Settings ──────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("HEALTHORACLE_LOG_LEVEL", "INFO")
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

# ── Gemini LLM Settings ───────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv(
    "HEALTHORACLE_GEMINI_API_KEY", 
    ""
)

