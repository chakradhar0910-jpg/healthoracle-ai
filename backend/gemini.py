"""
HealthOracle AI — Gemini LLM Service Module
===========================================
Interfaces with the Gemini 2.5 Flash API to parse medical report texts,
generate personalized clinical recommendations, and hold pre-screening dialogues.
"""

import json
import logging
from typing import Any

import requests

from backend.config import DEFAULT_AI_PROVIDER, GEMINI_API_KEY, OLLAMA_ENDPOINT, OLLAMA_MODEL

log = logging.getLogger("healthoracle.gemini")


def call_llm(
    prompt: str,
    provider: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
) -> str | None:
    """
    Unified LLM calling entrypoint.
    Supports Google Gemini, Local Ollama, and Custom OpenAI-compatible endpoints.
    """
    provider_name = (provider or DEFAULT_AI_PROVIDER or "gemini").lower()
    res_text: str | None = None

    if provider_name == "gemini":
        key = api_key or GEMINI_API_KEY
        if not key:
            log.warning("⚠️ Gemini API Key is missing. Skipping LLM call.")
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        payload: dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            log.info("📡 Dispatching request to Gemini API...")
            resp = requests.post(url, json=payload, headers=headers, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    res_text = str(parts[0].get("text", "")).strip()
                else:
                    log.warning("⚠️ Gemini API returned candidate with empty content parts.")
            else:
                log.warning("⚠️ Gemini API returned no completion candidates.")
        except Exception as e:
            log.error("❌ Gemini API request encountered an error: %s", e)

    elif provider_name == "ollama":
        url = endpoint or OLLAMA_ENDPOINT
        model_name = model or OLLAMA_MODEL
        headers = {"Content-Type": "application/json"}
        
        # Determine if we are using the native Ollama generate API or OpenAI-compatible
        if "/api/generate" in url:
            payload_ollama = {"model": model_name, "prompt": prompt, "stream": False}
            try:
                log.info("📡 Dispatching request to native Ollama API at %s...", url)
                resp = requests.post(url, json=payload_ollama, headers=headers, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                res_text = str(data.get("response", "")).strip()
            except Exception as e:
                log.error("❌ Native Ollama request failed: %s", e)
        else:
            # Assume OpenAI-compatible chat completions
            payload_openai = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            try:
                log.info("📡 Dispatching request to OpenAI-compatible Local AI at %s...", url)
                resp = requests.post(url, json=payload_openai, headers=headers, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    res_text = str(choices[0].get("message", {}).get("content", "")).strip()
            except Exception as e:
                log.error("❌ OpenAI-compatible Local AI request failed: %s", e)

    return res_text


def call_gemini(prompt: str) -> str | None:
    """Wrapper for backward compatibility."""
    return call_llm(prompt, provider="gemini")


def _clean_json_text(text: str) -> str:
    """Helper to clean markdown fences (e.g. ```json ... ```) from responses."""
    text = text.strip()
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
    """
    Asks Gemini/LLM to analyze patient biometrics and ML scores
    and returns a list of highly personalized recommendations.
    """
    # Exclude identity details from prompt to protect privacy
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
    Return ONLY a raw JSON array of strings. Do not include markdown code block syntax.
    IMPORTANT: Do not output any preamble or conversational text. Output ONLY the JSON.
    Example:
    ["Urgent: Consult an endocrinologist immediately...", "Introduce 30 minutes of daily aerobic activity..."]
    """

    raw_response = call_llm(prompt, provider, api_key, endpoint, model)
    if not raw_response:
        return None

    try:
        clean_text = _clean_json_text(raw_response)
        recs = json.loads(clean_text)
        if isinstance(recs, list) and all(isinstance(r, str) for r in recs):
            log.info("✅ Parsed %d personalized AI recommendations from LLM.", len(recs))
            return recs
        log.warning("⚠️ LLM returned JSON, but format was not a list of strings: %s", raw_response)
        return None
    except Exception as e:
        log.error("❌ Failed to parse LLM recommendations JSON: %s", e)
        return None


def parse_ocr_text_with_gemini(
    ocr_text: str,
    provider: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
) -> dict[str, float] | None:
    """
    Uses Gemini/LLM to extract structured numeric vitals from messy, unstructured OCR texts.
    """
    prompt = f"""
    You are a clinical database utility.
    Parse the following unstructured OCR output from a blood report.
    Identify and extract numerical values for these specific parameters:
    - glucose (fasting, in mg/dL)
    - hba1c (%)
    - cholesterol (total cholesterol, in mg/dL)
    - ldl (mg/dL)
    - hdl (mg/dL)
    - triglycerides (mg/dL)
    - systolic (blood pressure, in mmHg)
    - diastolic (blood pressure, in mmHg)
    
    Task:
    Return a flat JSON object where keys are the parameter names and values are floats or integers.
    If a parameter is not mentioned, omit it from the JSON object. Do not output anything except the JSON.
    Do not use markdown code blocks.
    IMPORTANT: Do not output any preamble or conversational text. Output ONLY the JSON.
    
    OCR Text:
    {ocr_text}
    """

    raw_response = call_llm(prompt, provider, api_key, endpoint, model)
    if not raw_response:
        return None

    try:
        clean_text = _clean_json_text(raw_response)
        vitals = json.loads(clean_text)
        if isinstance(vitals, dict):
            # Clean and normalize keys to float/int
            cleaned = {}
            for k in [
                "glucose",
                "hba1c",
                "cholesterol",
                "ldl",
                "hdl",
                "triglycerides",
                "systolic",
                "diastolic",
            ]:
                if k in vitals and vitals[k] is not None:
                    try:
                        cleaned[k] = float(vitals[k])
                    except (ValueError, TypeError):
                        pass
            log.info("✅ Parsed vitals using LLM OCR: %s", list(cleaned.keys()))
            return cleaned
        log.warning("⚠️ LLM OCR output did not parse as dictionary: %s", raw_response)
        return None
    except Exception as e:
        log.error("❌ Failed to parse LLM OCR JSON response: %s", e)
        return None


def ai_chat_completion(
    message: str,
    history: list[dict[str, str]],
    provider: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    model: str | None = None,
) -> str:
    """
    Handles a pre-screening conversation with a user about their health risks.
    """
    system_instruction = """
    You are the HealthOracle AI Clinical Assistant. You provide friendly, professional health pre-screening guidance.
    - Provide general, educational advice about diabetes, cardiovascular health, biometrics, and healthy habits.
    - Always maintain a helpful, warm, yet clinical tone.
    - Do NOT prescribe medications or claim to give a final medical diagnosis.
    - Advise consulting with qualified primary care physicians or cardiologists/endocrinologists for clinical diagnostics.
    - Limit replies to 3-4 clear, concise sentences. Use bullet points for recommendations.
    """

    # Format message history for context
    history_str = ""
    for turn in history[-8:]:  # Limit to last 8 turns to conserve context
        role = "User" if turn.get("role") == "user" else "Assistant"
        history_str += f"{role}: {turn.get('content')}\n"

    prompt = f"""
    {system_instruction}
    
    Recent Chat History:
    {history_str}
    User: {message}
    Assistant:"""

    response = call_llm(prompt, provider, api_key, endpoint, model)
    if response:
        return response

    return (
        "I'm sorry, I am currently having trouble communicating with my clinical logic center. "
        "Please try again in a moment, or schedule a physical consultation with your primary physician."
    )
