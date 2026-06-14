"""
HealthOracle AI — Ollama Local Client
=====================================
Strict interface for local Ollama API with model discovery and response tagging.
"""

import logging
import requests
import subprocess
import time
import os
from backend.config import OLLAMA_ENDPOINT, OLLAMA_MODEL

log = logging.getLogger("healthoracle.ai.ollama")

def _get_base_url(endpoint: str = None) -> str:
    url_to_clean = endpoint or OLLAMA_ENDPOINT
    base_url = url_to_clean
    for suffix in ["/api/generate", "/api/chat", "/api/tags"]:
        if base_url.endswith(suffix):
            base_url = base_url[:-len(suffix)]
            break
    if not base_url.endswith("/"):
        base_url += "/"
    return base_url

def is_ollama_running(endpoint: str = None) -> bool:
    """Pings the Ollama server to check availability."""
    base_url = _get_base_url(endpoint)
    
    # Try the provided/configured URL first
    urls_to_try = [base_url]
    
    # If using 127.0.0.1, also try localhost as backup (some Windows setups vary)
    if "127.0.0.1" in base_url:
        urls_to_try.append(base_url.replace("127.0.0.1", "localhost"))
    elif "localhost" in base_url:
        urls_to_try.append(base_url.replace("localhost", "127.0.0.1"))

    for url in urls_to_try:
        try:
            log.debug(f"🔍 Heartbeat ping to Ollama: {url}")
            resp = requests.get(url, timeout=3.0) # Increased timeout to 3s
            if resp.status_code == 200:
                return True
        except requests.exceptions.RequestException as e:
            log.debug(f"⚠️ Ollama heartbeat failed for {url}: {e}")
            continue
    
    return False

def try_start_ollama():
    """Attempts to launch the Ollama service if it's not running."""
    if is_ollama_running():
        return True
        
    log.info("🚀 Ollama not detected. Attempting to launch service...")
    try:
        # Try to launch the service in the background
        if os.name == 'nt': # Windows
            subprocess.Popen(["ollama", "serve"], 
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        else: # Linux/Mac
            subprocess.Popen(["ollama", "serve"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        
        # Wait a few seconds for it to warm up
        for _ in range(5):
            time.sleep(1.5)
            if is_ollama_running():
                log.info("✅ Ollama service started successfully.")
                return True
    except Exception as e:
        log.error(f"❌ Failed to auto-start Ollama: {e}")
    
    return False

def pull_ollama_model(model_name: str):
    """Triggers a background download of the specified Ollama model."""
    log.info(f"📥 Model '{model_name}' missing. Starting background download...")
    try:
        # We use a detached process so it doesn't block the API
        if os.name == 'nt':
            subprocess.Popen(["ollama", "pull", model_name], 
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["ollama", "pull", model_name], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        log.error(f"❌ Failed to trigger model pull: {e}")
        return False

def get_ollama_models(endpoint: str = None) -> list[str]:
    """Fetches list of installed models from Ollama."""
    base_url = _get_base_url(endpoint)
    url = base_url + "api/tags"
    
    urls_to_try = [url]
    if "127.0.0.1" in url:
        urls_to_try.append(url.replace("127.0.0.1", "localhost"))
    elif "localhost" in url:
        urls_to_try.append(url.replace("localhost", "127.0.0.1"))

    for u in urls_to_try:
        try:
            resp = requests.get(u, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            log.debug(f"⚠️ Failed to fetch models from {u}: {e}")
            continue
    return []


def call_ollama(prompt: str, endpoint: str = None, model: str = None, is_auto: bool = False) -> str:
    """
    Strict Ollama API caller.
    TIMEOUT: 120s
    """
    url = endpoint or OLLAMA_ENDPOINT
    model_name = model or OLLAMA_MODEL
    
    tag = "[AUTO-LOCAL] " if is_auto else "[OLLAMA] "
    
    # Route request based on endpoint type
    if url.endswith("/chat"):
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9},
        }
    else:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9},
        }

    try:
        log.info(f"📡 Routing to: Ollama ({model_name})")
        log.info(f"📡 Endpoint: {url}")

        resp = requests.post(url, json=payload, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()

        if url.endswith("/chat"):
            res_text = str(data.get("message", {}).get("content", "")).strip()
        else:
            res_text = str(data.get("response", "")).strip()

        return f"{tag}{res_text}"
    except Exception as e:
        log.error(f"❌ Ollama request failed: {e}")
        return "[ERROR] Ollama not responding"
