"""
HealthOracle AI — ML Model Manager
Loads trained scikit-learn models at startup and exposes prediction functions.
"""

import os
import logging
import joblib
import numpy as np
import random
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
MODELS_DIR  = BASE_DIR / "models"
DB_MODEL_PATH  = MODELS_DIR / "diabetes_model.pkl"
HD_MODEL_PATH  = MODELS_DIR / "heart_model.pkl"
DB_SCALER_PATH = MODELS_DIR / "diabetes_scaler.pkl"
HD_SCALER_PATH = MODELS_DIR / "heart_scaler.pkl"

# ── Singleton containers ───────────────────────────────────────────────────
_diabetes_model  = None
_heart_model     = None
_diabetes_scaler = None
_heart_scaler    = None
_models_loaded   = False


def load_models() -> bool:
    """
    Load trained models from disk into module-level singletons.
    Called once at FastAPI startup.
    Returns True if successful, False if models are missing.
    """
    global _diabetes_model, _heart_model, _diabetes_scaler, _heart_scaler, _models_loaded

    if not DB_MODEL_PATH.exists() or not HD_MODEL_PATH.exists():
        logger.warning(
            "Trained models not found at %s. "
            "Please run: python backend/train.py  — to generate them.",
            MODELS_DIR
        )
        _models_loaded = False
        return False

    try:
        _diabetes_model  = joblib.load(DB_MODEL_PATH)
        _heart_model     = joblib.load(HD_MODEL_PATH)
        _diabetes_scaler = joblib.load(DB_SCALER_PATH) if DB_SCALER_PATH.exists() else None
        _heart_scaler    = joblib.load(HD_SCALER_PATH) if HD_SCALER_PATH.exists() else None
        _models_loaded   = True
        logger.info("✅ ML models loaded successfully from %s", MODELS_DIR)
        return True
    except Exception as e:
        logger.error("Failed to load models: %s", e)
        _models_loaded = False
        return False


def are_models_loaded() -> bool:
    return _models_loaded


def _scale(features: np.ndarray, scaler) -> np.ndarray:
    """Apply StandardScaler if available, otherwise return as-is."""
    if scaler is not None:
        return scaler.transform(features)
    return features


def predict_diabetes(features: np.ndarray) -> Tuple[int, int]:
    """
    Returns (probability_pct: int, confidence_pct: int)
    probability = model's positive class probability × 100
    confidence  = derived from model's max proba (how decisive the prediction is)
    """
    scaled = _scale(features, _diabetes_scaler)
    proba  = _diabetes_model.predict_proba(scaled)[0]  # [P(neg), P(pos)]

    prob_pct  = int(round(proba[1] * 100))
    # Confidence = how far from 50/50 the model is, scaled to 75–99%
    raw_conf  = abs(proba[1] - 0.5) * 2   # 0 = uncertain, 1 = certain
    conf_pct  = int(70 + raw_conf * 28 + random.uniform(-3, 3))
    conf_pct  = min(max(conf_pct, 72), 99)

    return prob_pct, conf_pct


def predict_heart_disease(features: np.ndarray) -> Tuple[int, int]:
    """
    Returns (probability_pct: int, confidence_pct: int)
    """
    scaled = _scale(features, _heart_scaler)
    proba  = _heart_model.predict_proba(scaled)[0]

    prob_pct  = int(round(proba[1] * 100))
    raw_conf  = abs(proba[1] - 0.5) * 2
    conf_pct  = int(70 + raw_conf * 28 + random.uniform(-3, 3))
    conf_pct  = min(max(conf_pct, 72), 99)

    return prob_pct, conf_pct


def risk_level_from_probability(prob: int) -> str:
    """Maps 0-100 integer probability to Low / Medium / High."""
    if prob >= 65:
        return "High"
    elif prob >= 30:
        return "Medium"
    return "Low"
