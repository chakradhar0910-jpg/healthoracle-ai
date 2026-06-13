import os

os.environ["HEALTHORACLE_GEMINI_API_KEY"] = "mock-api-key"

from unittest.mock import MagicMock, patch

from backend.gemini import (
    ai_chat_completion,
    call_gemini,
    generate_ai_recommendations,
    parse_ocr_text_with_gemini,
)

# ── Mock Responses ────────────────────────────────────────────────────────
MOCK_TEXT_RESPONSE = {"candidates": [{"content": {"parts": [{"text": "Hello, I am Gemini."}]}}]}

MOCK_RECS_RESPONSE = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": '["Monitor blood pressure daily.", "Follow a low-glycemic dietary path." ]'
                    }
                ]
            }
        }
    ]
}

MOCK_OCR_RESPONSE = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {"text": '{"glucose": 110, "hba1c": 5.9, "systolic": 132, "diastolic": 82}'}
                ]
            }
        }
    ]
}


# ── Tests ──────────────────────────────────────────────────────────────────


@patch("backend.gemini.requests.post")
def test_call_gemini_success(mock_post):
    """Verify that call_gemini successfully makes POST requests and returns text."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_TEXT_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    res = call_gemini("Say hello")
    assert res == "Hello, I am Gemini."
    mock_post.assert_called_once()


@patch("backend.gemini.requests.post")
def test_call_gemini_failure(mock_post):
    """Verify that call_gemini handles errors by returning None."""
    mock_post.side_effect = Exception("API Connection Error")

    res = call_gemini("Say hello")
    assert res is None


@patch("backend.gemini.requests.post")
def test_generate_ai_recommendations_success(mock_post):
    """Verify that generate_ai_recommendations returns a parsed list of string suggestions."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RECS_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    payload = {"age": 45, "gender": "Male", "glucose": 120}
    recs = generate_ai_recommendations(payload, 42, "Medium", 20, "Low")

    assert isinstance(recs, list)
    assert len(recs) == 2
    assert recs[0] == "Monitor blood pressure daily."
    assert recs[1] == "Follow a low-glycemic dietary path."


@patch("backend.gemini.requests.post")
def test_parse_ocr_text_with_gemini_success(mock_post):
    """Verify that parse_ocr_text_with_gemini extracts correct numeric parameters."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_OCR_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    vitals = parse_ocr_text_with_gemini("glucose is 110 and hba1c is 5.9")

    assert vitals["glucose"] == 110.0
    assert vitals["hba1c"] == 5.9
    assert vitals["systolic"] == 132.0
    assert vitals["diastolic"] == 82.0


@patch("backend.gemini.requests.post")
def test_ai_chat_completion(mock_post):
    """Verify that ai_chat_completion initiates conversation sessions."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_TEXT_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    history = [{"role": "user", "content": "hello"}]
    reply = ai_chat_completion("How are you?", history)

    assert reply == "Hello, I am Gemini."
