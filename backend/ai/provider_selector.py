"""
HealthOracle AI — Provider Selector Logic
=========================================
Implements strict routing, auto-discovery, and debug logging.
"""

import logging
from backend.ai.ollama_client import is_ollama_running, get_ollama_models, call_ollama, try_start_ollama, pull_ollama_model
from backend.ai.gemini_client import call_gemini
from backend.ai.openai_client import call_openai

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
        if not is_ollama_running(endpoint):
            if not try_start_ollama():
                log.warning("⚠️ Ollama selected but could not be started.")
                return "[ERROR] Ollama is unavailable on this system. Please start it manually."

        # Check if model is downloaded
        from backend.config import OLLAMA_MODEL
        target_model = model or OLLAMA_MODEL
        models = get_ollama_models(endpoint)

        if models:
            # Flexible matching: check for exact match or base name match
            # e.g. "llama3.2:1b" matches "llama3.2:1b" or "llama3.2"
            normalized_target = target_model.split(":")[0].lower()
            model_exists = False

            log.info(f"🔎 Checking for model '{target_model}' in: {models}")

            for m in models:
                m_lower = m.lower()
                m_base = m_lower.split(":")[0]

                if m_lower == target_model.lower() or m_base == normalized_target:
                    model_exists = True
                    # If we found a base match but it's different, use the one the user has
                    target_model = m 
                    break

            if not model_exists:
                log.info(f"📥 Model '{target_model}' missing. Triggering auto-pull...")
                pull_ollama_model(target_model)
                return f"[ERROR] Model '{target_model}' is being downloaded. Please wait 1-2 minutes and try again."
        else:
            # If we are here, Ollama is running but has NO models
            log.info(f"📥 No models found. Triggering pull for '{target_model}'...")
            pull_ollama_model(target_model)
            return f"[ERROR] Downloading model '{target_model}'... Please wait 1-2 minutes and try again."

        return call_ollama(prompt, endpoint, target_model)
    elif selected_provider == "gemini":
        return call_gemini(prompt, api_key=api_key)
        
    elif selected_provider == "openai":
        return call_openai(prompt, api_key=api_key, endpoint=endpoint, model=model)
    
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
