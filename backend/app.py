"""
HealthOracle AI — FastAPI Application
======================================
Production-grade REST API for the HealthOracle Clinical Suite frontend.

Endpoints:
  GET  /          → Health check (used by frontend status pill)
  POST /predict   → ML-powered risk prediction
  GET  /model-info → Model metadata

Run:
  uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas import PatientPayload, PredictionResponse, ContributingFactor
from backend.model import (
    load_models, are_models_loaded,
    predict_diabetes, predict_heart_disease,
    risk_level_from_probability
)
from backend.utils import engineer_features, compute_contributing_factors, generate_recommendations

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("healthoracle")

# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="HealthOracle AI Clinical API",
    description="Hospital-grade disease risk prediction for Diabetes and Cardiovascular conditions.",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── CORS — allow frontend (file:// or localhost) to call us ────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Frontend runs from file:// or localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup: Load ML models ────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    log.info("🏥 HealthOracle AI Server starting up...")
    success = load_models()
    if success:
        log.info("✅ ML models loaded and ready.")
    else:
        log.warning(
            "⚠️  ML models not found. Run 'python backend/train.py' to train them. "
            "The API will return 503 on /predict until models are available."
        )


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

@app.get("/", summary="Health Check")
async def health_check():
    """
    Status endpoint polled by the frontend every 10 seconds.
    Returns 200 with model readiness info.
    """
    return {
        "status": "ok",
        "service": "HealthOracle AI Clinical API",
        "version": "4.0.0",
        "models_ready": are_models_loaded(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/predict", summary="Patient Risk Prediction", response_model=None)
async def predict(payload: PatientPayload):
    """
    Accepts full patient data from the HealthOracle frontend and returns
    ML-powered predictions for Diabetes and Cardiovascular risk.
    """
    if not are_models_loaded():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ML models not loaded",
                "message": "Please run 'python backend/train.py' to train the models first.",
                "hint": "The frontend will automatically fall back to local inference."
            }
        )

    try:
        # 1. Feature engineering
        features = engineer_features(payload)
        resolved = features["_resolved"]

        # 2. Predictions
        db_prob, db_conf = predict_diabetes(features["diabetes"])
        hd_prob, hd_conf = predict_heart_disease(features["heart"])

        db_risk = risk_level_from_probability(db_prob)
        hd_risk = risk_level_from_probability(hd_prob)

        log.info(
            "Prediction | Patient: %s | Diabetes: %d%% (%s) | Heart: %d%% (%s)",
            payload.patientName, db_prob, db_risk, hd_prob, hd_risk
        )

        # 3. Contributing factors (top 5)
        raw_factors = compute_contributing_factors(payload, resolved, db_prob, hd_prob)

        # 4. Clinical recommendations
        recommendations = generate_recommendations(payload, resolved, db_risk, hd_risk)

        # 5. Build response
        response = {
            "predictions": {
                "diabetes": {
                    "risk_level": db_risk,
                    "probability": db_prob,
                    "confidence": db_conf
                },
                "heart_disease": {
                    "risk_level": hd_risk,
                    "probability": hd_prob,
                    "confidence": hd_conf
                }
            },
            "factors": raw_factors,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "ml_model"
        }

        return JSONResponse(content=response)

    except Exception as e:
        log.error("Prediction error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Prediction failed", "message": str(e)}
        )


@app.get("/model-info", summary="Model Metadata")
async def model_info():
    """Returns metadata about the trained models."""
    import json
    from pathlib import Path

    meta_path = Path(__file__).parent / "models" / "model_meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        return {
            "models_loaded": are_models_loaded(),
            "metadata": meta
        }
    return {
        "models_loaded": are_models_loaded(),
        "metadata": None,
        "hint": "Run python backend/train.py to generate model metadata."
    }


# ── Exception handler for clean JSON error responses ───────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
