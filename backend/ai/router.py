"""
HealthOracle AI — AI Health Router
==================================
Exposes system-wide AI health status.
"""

import logging
from fastapi import APIRouter
from backend.ai.ollama_client import is_ollama_running, get_ollama_models
from backend.config import GEMINI_API_KEY, OLLAMA_ENDPOINT

log = logging.getLogger("healthoracle.ai.router")

router = APIRouter(prefix="/ai", tags=["AI Status"])

@router.get("/health")
async def ai_health():
    """
    Returns diagnostics for local and cloud AI providers.
    """
    ollama_status = is_ollama_running()
    log.info(f"🏥 Health check: Ollama={ollama_status} (Endpoint: {OLLAMA_ENDPOINT})")
    
    return {
        "ollama_running": ollama_status,
        "available_models": get_ollama_models(),
        "gemini_available": bool(GEMINI_API_KEY)
    }
