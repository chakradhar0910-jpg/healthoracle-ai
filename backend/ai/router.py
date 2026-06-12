"""
HealthOracle AI — AI Health Router
==================================
Exposes system-wide AI health status.
"""

from fastapi import APIRouter
from backend.ai.ollama_client import is_ollama_running, get_ollama_models
from backend.config import GEMINI_API_KEY

router = APIRouter(prefix="/ai", tags=["AI Status"])

@router.get("/health")
async def ai_health():
    """
    Returns diagnostics for local and cloud AI providers.
    """
    return {
        "ollama_running": is_ollama_running(),
        "available_models": get_ollama_models(),
        "gemini_available": bool(GEMINI_API_KEY)
    }
