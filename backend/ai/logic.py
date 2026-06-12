"""
HealthOracle AI — AI Logic Module
=================================
High-level functions for recommendations, OCR parsing, and chat.
Connects the clinical logic to the modular AI routing system.
"""

import json
import logging
import re
from typing import Any

from backend.ai.provider_selector import route_ai_request

log = logging.getLogger("healthoracle.ai.logic")

def _strip_ai_tags(text: str) -> str:
    """Removes mandatory tags like [OLLAMA] or [GEMINI] before parsing JSON."""
    tags = ["[OLLAMA] ", "[GEMINI] ", "[AUTO-LOCAL] ", "[AUTO-CLOUD] ", "[ERROR] "]
    for tag in tags:
        if text.startswith(tag):
            return text[len(tag):]
    return text

def _clean_json_text(text: str) -> str:
    """Helper to clean markdown fences (e.g. ```json ... ```) from responses."""
    text = _strip_ai_tags(text.strip())
    if text.startswith("```"):
        # Find the first newline after the opening backticks
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline:]
        else:
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]
    return text.strip()

def generate_ai_recommendations(
    payload_dict: dict[str, Any],
    db_prob: int,
    db_risk: str,
    hd_prob: int,
    hd_risk: str,
    provider: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
) -> list[str] | None:
    """Asks AI to analyze patient metrics and return recommendations."""
    sanitized_payload = {k: v for k, v in payload_dict.items() if k not in ("patientName", "mrn")}

    prompt = f"""
    You are a hospital-grade clinical AI assistant.
    Analyze the following patient lab vitals, biometrics, symptoms, and risk predictions.
    
    Patient Data:
    {json.dumps(sanitized_payload, indent=2)}
    
    Ensemble ML Predictions:
    - Diabetes Risk Probability: {db_prob}% (Risk Level: {db_risk})
    - Cardiovascular Disease Risk Probability: {hd_prob}% (Risk Level: {hd_risk})
    
    Task:
    Generate a JSON list of exactly 5 to 8 highly custom, actionable clinical recommendations.
    - Each recommendation must be a single, direct, action-oriented sentence.
    - Focus heavily on their high-risk areas, specific symptoms, and outlying lab markers.
    - Prepend critical flags (using the red alert emoji 🚨) to urgent warnings if any markers are in emergency thresholds.
    
    Format:
    Return ONLY a raw JSON array of strings. Output ONLY the JSON.
    """

    raw_response = route_ai_request(prompt, provider, api_key, endpoint, model)
    if not raw_response or "[ERROR]" in raw_response:
        return None

    try:
        clean_text = _clean_json_text(raw_response)
        recs = json.loads(clean_text)
        if isinstance(recs, list) and all(isinstance(r, str) for r in recs):
            return recs
        return None
    except Exception as e:
        log.error(f"❌ Failed to parse AI recommendations: {e}")
        return None

def parse_ocr_text_with_ai(
    ocr_text: str,
    provider: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
) -> dict[str, float] | None:
    """Uses AI to extract structured numeric vitals from messy OCR texts."""
    prompt = f"""
    You are a clinical database utility.
    Parse the following unstructured OCR output from a blood report.
    Identify numerical values for: glucose, hba1c, cholesterol, ldl, hdl, triglycerides, systolic, diastolic.
    
    Task:
    Return a flat JSON object where keys are the parameter names and values are floats.
    Output ONLY the JSON.
    
    OCR Text:
    {ocr_text}
    """

    raw_response = route_ai_request(prompt, provider, api_key, endpoint, model)
    if not raw_response or "[ERROR]" in raw_response:
        return None

    try:
        clean_text = _clean_json_text(raw_response)
        vitals = json.loads(clean_text)
        if isinstance(vitals, dict):
            cleaned = {}
            for k in ["glucose", "hba1c", "cholesterol", "ldl", "hdl", "triglycerides", "systolic", "diastolic"]:
                if k in vitals and vitals[k] is not None:
                    try:
                        cleaned[k] = float(vitals[k])
                    except: pass
            return cleaned
        return None
    except Exception as e:
        log.error(f"❌ Failed to parse AI OCR response: {e}")
        return None

def ai_chat_completion(
    message: str,
    history: list[dict[str, str]],
    provider: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
) -> str:
    """Handles conversational pre-screening AI."""
    system_instruction = """
    You are the HealthOracle AI Clinical Assistant.
    - Provide general, educational advice about diabetes and cardiovascular health.
    - Do NOT prescribe medications or claim to give a final medical diagnosis.
    - Limit replies to 3-4 clear, concise sentences.
    """

    history_str = ""
    for turn in history[-8:]:
        role = "User" if turn.get("role") == "user" else "Assistant"
        history_str += f"{role}: {turn.get('content')}\n"

    prompt = f"{system_instruction}\n\nRecent History:\n{history_str}\nUser: {message}\nAssistant:"

    return route_ai_request(prompt, provider, api_key, endpoint, model)
