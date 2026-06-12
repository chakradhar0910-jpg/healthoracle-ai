"""
HealthOracle AI — Ollama Local Client
=====================================
Strict interface for local Ollama API with model discovery and response tagging.
"""

import logging
import requests
from backend.config import OLLAMA_ENDPOINT, OLLAMA_MODEL

log = logging.getLogger("healthoracle.ai.ollama")

def is_ollama_running(endpoint: str = None) -> bool:
    """Pings the Ollama server to check availability."""
    url = (endpoint or OLLAMA_ENDPOINT).replace("/api/generate", "/")
    try:
        resp = requests.get(url, timeout=2)
        return resp.status_code == 200
    except:
        return False

def get_ollama_models(endpoint: str = None) -> list[str]:
    """Fetches list of installed models from Ollama."""
    url = (endpoint or OLLAMA_ENDPOINT).replace("/api/generate", "/api/tags")
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
    except:
        pass
    return []

def call_ollama(prompt: str, endpoint: str = None, model: str = None, is_auto: bool = False) -> str:
    """
    Strict Ollama API caller.
    TIMEOUT: 120s
    """
    url = endpoint or OLLAMA_ENDPOINT
    model_name = model or OLLAMA_MODEL
    
    tag = "[AUTO-LOCAL] " if is_auto else "[OLLAMA] "
    
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        log.info(f"📡 Routing to: Ollama ({model_name})")
        log.info(f"📡 Endpoint: {url}")
        
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        res_text = str(data.get("response", "")).strip()
        return f"{tag}{res_text}"
    except Exception as e:
        log.error(f"❌ Ollama request failed: {e}")
        return "[ERROR] Ollama not responding"
