"""
HealthOracle AI — OpenAI Compatible Cloud Client
================================================
Strict interface for custom OpenAI-compatible endpoints.
"""

import logging
import requests

log = logging.getLogger("healthoracle.ai.openai")

def call_openai(
    prompt: str,
    api_key: str = None,
    endpoint: str = None,
    model: str = None
) -> str:
    """
    Strict OpenAI API caller.
    TIMEOUT: 120s
    """
    url = endpoint or "https://api.openai.com/v1/chat/completions"
    model_name = model or "gpt-4o"
    
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "stream": False
    }
    
    try:
        log.info(f"📡 Routing to: OpenAI Compatible ({model_name})")
        log.info(f"📡 Endpoint: {url}")
        
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        
        choices = data.get("choices", [])
        if choices:
            res_text = str(choices[0].get("message", {}).get("content", "")).strip()
            return f"[OPENAI] {res_text}"
            
        return "[ERROR] OpenAI compatible endpoint returned empty response"
    except Exception as e:
        log.error(f"❌ OpenAI request failed: {e}")
        return f"[ERROR] OpenAI request failed: {e}"
