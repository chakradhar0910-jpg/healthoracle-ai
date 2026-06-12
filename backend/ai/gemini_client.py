"""
HealthOracle AI — Gemini Cloud Client
=====================================
Strict interface for Google Gemini API with mandatory response tagging.
"""

import logging
import requests
from backend.config import GEMINI_API_KEY

log = logging.getLogger("healthoracle.ai.gemini")

def call_gemini(prompt: str, api_key: str = None, is_auto: bool = False) -> str:
    """
    Strict Gemini API caller.
    TIMEOUT: 30s
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        log.error("❌ Gemini API Key is missing.")
        return "[ERROR] Gemini API Key is missing"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    tag = "[AUTO-CLOUD] " if is_auto else "[GEMINI] "
    
    try:
        log.info(f"📡 Routing to: Gemini (Cloud)")
        log.info(f"📡 Endpoint: {url.split('?')[0]}")
        
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                res_text = str(parts[0].get("text", "")).strip()
                return f"{tag}{res_text}"
        
        return "[ERROR] Gemini API returned empty response"
    except Exception as e:
        log.error(f"❌ Gemini API failed: {e}")
        return "[ERROR] Gemini API failed"
