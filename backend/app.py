"""
HealthOracle AI — FastAPI Application
======================================
Production-grade REST API for the HealthOracle Clinical Suite frontend.

Now features persistent structured logging, SQLite database tracking,
configurable CORS, and OCR file uploads for automatic data extraction.
"""

from datetime import datetime

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# Initialize structured logging first before other imports configure loggers
from backend.logging_config import setup_logging

setup_logging()

import logging

log = logging.getLogger("healthoracle.api")

from backend.config import CORS_ALLOW_CREDENTIALS, CORS_ORIGINS
from backend.database import get_assessments, get_db, init_db, save_assessment
from backend.gemini import ai_chat_completion, generate_ai_recommendations
from backend.model import (
    are_models_loaded,
    load_models,
    predict_diabetes,
    predict_heart_disease,
    risk_level_from_probability,
)
from backend.ocr import extract_vitals_from_report
from backend.schemas import AssessmentHistoryRecord, ChatRequest, PatientPayload
from backend.utils import compute_contributing_factors, engineer_features, generate_recommendations

# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="HealthOracle AI Clinical API",
    description="Hospital-grade disease risk prediction and patient pre-screening manager.",
    version="4.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ── CORS Middleware Configuration ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup Hooks ─────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    log.info("🏥 HealthOracle AI Server starting up...")
    
    # Initialize Database Tables
    init_db()
    
    # Load ML models
    success = load_models()
    if success:
        log.info("✅ ML models loaded and ready.")
    else:
        log.warning("⚠️ ML models not found or incompatible. Training new models automatically...")
        import subprocess
        try:
            subprocess.run(["python", "-m", "backend.train"], check=True)
            if load_models():
                log.info("✅ ML models newly trained and successfully loaded.")
            else:
                log.error("❌ On-the-fly training finished but models still failed to load.")
        except Exception as e:
            log.error("❌ Failed to train models automatically: %s", e)


# ── REST API Endpoints ─────────────────────────────────────────────────────

@app.get("/", summary="Health Check")
async def health_check():
    """
    Status endpoint polled by the frontend.
    Returns 200 with service information and model readiness.
    """
    return {
        "status": "ok",
        "service": "HealthOracle AI Clinical API",
        "version": "4.1.0",
        "models_ready": are_models_loaded(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/predict", summary="Patient Risk Prediction", response_model=None)
async def predict(payload: PatientPayload, db: Session = Depends(get_db)):
    """
    Accepts patient biometric data and returns risk probabilities,
    contributing factors, clinical recommendations, and stores findings in the DB.
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

        # 2. ML Inference
        db_prob, db_conf = predict_diabetes(features["diabetes"])
        hd_prob, hd_conf = predict_heart_disease(features["heart"])

        db_risk = risk_level_from_probability(db_prob)
        hd_risk = risk_level_from_probability(hd_prob)

        log.info(
            "Prediction Request | Patient: %s (MRN: %s) | Diabetes: %d%% (%s) | Heart: %d%% (%s)",
            payload.patientName, payload.mrn, db_prob, db_risk, hd_prob, hd_risk
        )

        # 3. Save assessment results to history database
        payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
        save_assessment(db, payload_dict, db_prob, db_risk, hd_prob, hd_risk)

        # 4. Generate explainable factors (top 5) and clinical suggestions
        raw_factors = compute_contributing_factors(payload, resolved, db_prob, hd_prob)
        
        # Use Gemini dynamic recommendations if available, else fallback to local rule-based system
        payload_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
        ai_recs = generate_ai_recommendations(payload_dict, db_prob, db_risk, hd_prob, hd_risk)
        if ai_recs:
            recommendations = ai_recs
            log.info("✅ Gemini AI Recommendations generated successfully.")
        else:
            log.info("⚠️ Gemini recommendations unavailable, using local rules.")
            recommendations = generate_recommendations(payload, resolved, db_risk, hd_risk)

        # 5. Formulate API Response
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
        log.error("❌ Prediction execution failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Prediction failed", "message": str(e)}
        )


@app.get("/history", summary="Query Assessment History", response_model=list[AssessmentHistoryRecord])
async def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves list of past patient pre-screenings persisted in local database."""
    assessments = get_assessments(db, limit=limit)
    return assessments


@app.post("/ocr-upload", summary="Parse Medical Report OCR")
async def ocr_upload(file: UploadFile = File(...)):
    """
    Uploader for PDF/Image blood report files.
    Applies OCR parsing and regex capture to identify and auto-fill clinical lab panels.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload an image file (PNG/JPG)."
        )
        
    try:
        file_bytes = await file.read()
        vitals = extract_vitals_from_report(file_bytes, file.filename)
        return {
            "success": True,
            "filename": file.filename,
            "vitals": vitals
        }
    except Exception as e:
        log.error("❌ Failed to process report file OCR: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "OCR extraction failed", "message": str(e)}
        )
@app.post("/chat", summary="AI Health Chatbot Assistant")
async def chat(request: ChatRequest):
    """
    Interactive pre-screening chatbot assistant.
    Responds dynamically using historical conversation turns for context.
    """
    try:
        history_list = [
            turn.model_dump() if hasattr(turn, "model_dump") else turn.dict()
            for turn in request.history
        ]
        response_text = ai_chat_completion(request.message, history_list)
        return {"response": response_text}
    except Exception as e:
        log.error("❌ Chat completion failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Chatbot query failed", "message": str(e)}
        )


@app.get("/model-info", summary="Model Metadata")
async def model_info():
    """Returns metadata details about the currently active trained models."""
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


# ── Global Exception Handler ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("💥 Unhandled exception on request path %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
