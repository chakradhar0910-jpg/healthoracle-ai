"""
HealthOracle AI — Provider Selector Logic
=========================================
Implements strict routing, auto-discovery, and debug logging.
"""

import logging
from backend.ai.ollama_client import is_ollama_running, get_ollama_models, call_ollama
from backend.ai.gemini_client import call_gemini

log = logging.getLogger("healthoracle.ai.selector")

def route_ai_request(
    prompt: str,
    provider: str = "auto",
    api_key: str = None,
    endpoint: str = None,
    model: str = None
) -> str:
    """
    Main entrypoint for AI routing.
    Enforces strict rules: no silent fallbacks unless 'auto' is selected.
    """
    selected_provider = (provider or "auto").lower()
    log.info(f"[INFO] Provider selected: {selected_provider}")

    if selected_provider == "ollama":
        return call_ollama(prompt, endpoint=endpoint, model=model)
    
    elif selected_provider == "gemini":
        return call_gemini(prompt, api_key=api_key)
    
    elif selected_provider == "auto":
        # 1. Check if Ollama is running
        if is_ollama_running(endpoint):
            models = get_ollama_models(endpoint)
            if models:
                # 2. Select best model (priority: llama3.2 > llama3 > mistral)
                target_model = None
                for priority in ["llama3.2", "llama3", "mistral"]:
                    for m in models:
                        if priority in m:
                            target_model = m
                            break
                    if target_model: break
                
                # Default to first available if no priority match
                target_model = target_model or models[0]
                return call_ollama(prompt, endpoint=endpoint, model=target_model, is_auto=True)
        
        # 3. Fallback to Gemini if Ollama is unavailable or has no models
        return call_gemini(prompt, api_key=api_key, is_auto=True)
    
    else:
        log.warning(f"⚠️ Unknown provider '{selected_provider}'. Defaulting to Gemini.")
        return call_gemini(prompt, api_key=api_key)
