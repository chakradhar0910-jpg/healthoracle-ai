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

from backend.config import GEMINI_API_KEY

log = logging.getLogger("healthoracle.gemini")
def call_gemini(prompt: str) -> str | None:
    """
    Sends a prompt request to the Gemini 2.5 Flash API.
    Returns the generated content text or None if an error occurs.
    """
    if not GEMINI_API_KEY:
        log.warning("⚠️ Gemini API Key is missing. Skipping LLM call.")
        return None

    # Official endpoint for Gemini 2.5 Flash API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    payload: dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        log.info("📡 Dispatching prompt request to Gemini API...")
        resp = requests.post(url, json=payload, headers=headers, timeout=12)
        resp.raise_for_status()
        
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            log.warning("⚠️ Gemini API returned no completion candidates.")
            return None
            
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            log.warning("⚠️ Gemini API returned candidate with empty content parts.")
            return None
            
        text = parts[0].get("text", "")
        return text.strip()
        
    except Exception as e:
        log.error("❌ Gemini API request encountered an error: %s", e, exc_info=True)
        return None


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
    hd_risk: str
) -> list[str] | None:
    """
    Asks Gemini to analyze patient biometrics and ML scores
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
    Example:
    ["Urgent: Consult an endocrinologist immediately...", "Introduce 30 minutes of daily aerobic activity..."]
    """
    
    raw_response = call_gemini(prompt)
    if not raw_response:
        return None
        
    try:
        clean_text = _clean_json_text(raw_response)
        recs = json.loads(clean_text)
        if isinstance(recs, list) and all(isinstance(r, str) for r in recs):
            log.info("✅ Parsed %d personalized AI recommendations from Gemini.", len(recs))
            return recs
        log.warning("⚠️ Gemini returned JSON, but format was not a list of strings: %s", raw_response)
        return None
    except Exception as e:
        log.error("❌ Failed to parse Gemini recommendations JSON: %s", e)
        return None


def parse_ocr_text_with_gemini(ocr_text: str) -> dict[str, float] | None:
    """
    Uses Gemini to extract structured numeric vitals from messy, unstructured OCR texts.
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
    
    OCR Text:
    {ocr_text}
    """
    
    raw_response = call_gemini(prompt)
    if not raw_response:
        return None
        
    try:
        clean_text = _clean_json_text(raw_response)
        vitals = json.loads(clean_text)
        if isinstance(vitals, dict):
            # Clean and normalize keys to float/int
            cleaned = {}
            for k in ["glucose", "hba1c", "cholesterol", "ldl", "hdl", "triglycerides", "systolic", "diastolic"]:
                if k in vitals and vitals[k] is not None:
                    try:
                        cleaned[k] = float(vitals[k])
                    except (ValueError, TypeError):
                        pass
            log.info("✅ Parsed vitals using Gemini OCR: %s", list(cleaned.keys()))
            return cleaned
        log.warning("⚠️ Gemini OCR output did not parse as dictionary: %s", raw_response)
        return None
    except Exception as e:
        log.error("❌ Failed to parse Gemini OCR JSON response: %s", e)
        return None


def ai_chat_completion(message: str, history: list[dict[str, str]]) -> str:
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
    
    response = call_gemini(prompt)
    if response:
        return response
        
    return (
        "I'm sorry, I am currently having trouble communicating with my clinical logic center. "
        "Please try again in a moment, or schedule a physical consultation with your primary physician."
    )
