"""
HealthOracle AI — Pydantic Request/Response Schemas
Matches the exact JSON payload emitted by frontend/script.js
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────────
# REQUEST MODEL — exactly matches script.js payload
# ─────────────────────────────────────────────────
class PatientPayload(BaseModel):
    # Patient identity (not used by ML, echoed back)
    patientName: Optional[str] = "Unknown"
    mrn: Optional[str] = "N/A"

    # Core biometrics
    age: int = Field(..., ge=1, le=115)
    gender: str = Field(..., pattern="^(Male|Female)$")
    height: float = Field(..., ge=80, le=250)      # cm
    weight: float = Field(..., ge=10, le=300)      # kg

    # Legacy categorical blood pressure (frontend fallback)
    bp: Optional[str] = None  # "Normal", "Elevated", "High1", "High2"

    # Lab panel — all optional
    systolic: Optional[float] = Field(None, ge=70, le=250)
    diastolic: Optional[float] = Field(None, ge=40, le=150)
    glucose: Optional[float] = Field(None, ge=50, le=500)      # mg/dL fasting
    hba1c: Optional[float] = Field(None, ge=3.0, le=18.0)      # %
    cholesterol: Optional[float] = Field(None, ge=80, le=500)  # mg/dL
    ldl: Optional[float] = Field(None, ge=30, le=350)          # mg/dL
    hdl: Optional[float] = Field(None, ge=15, le=150)          # mg/dL
    triglycerides: Optional[float] = Field(None, ge=30, le=600) # mg/dL

    # Lifestyle
    sleepHours: float = Field(7.0, ge=4.0, le=10.0)
    dietQuality: int = Field(7, ge=1, le=10)
    stressLevel: int = Field(5, ge=1, le=10)
    smoking: str = Field("Never", pattern="^(Never|Former|Current)$")
    physicalActivity: str = Field("Medium", pattern="^(Low|Medium|High)$")
    alcohol: str = Field("None", pattern="^(None|Moderate|Heavy)$")

    # Genetics
    familyDiabetes: str = Field("None", pattern="^(None|One|Both)$")
    familyHeart: str = Field("None", pattern="^(None|One|Both)$")

    # Checklists (arrays of strings)
    symptoms: List[str] = Field(default_factory=list)
    comorbidities: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────────
class RiskResult(BaseModel):
    risk_level: str          # "Low" | "Medium" | "High"
    probability: int         # 0-100 (display as %)
    confidence: int          # 0-100 (model confidence %)


class ContributingFactor(BaseModel):
    name: str
    weight: int              # numeric weight for bar chart
    positive: bool           # True = increases risk, False = decreases


class PredictionResponse(BaseModel):
    predictions: dict        # { diabetes: RiskResult, heart_disease: RiskResult }
    factors: List[ContributingFactor]
    recommendations: List[str]
    timestamp: str
    source: str = "ml_model" # "ml_model" | "fallback"

    model_config = {
        "json_schema_extra": {
            "example": {
                "predictions": {
                    "diabetes": {"risk_level": "Medium", "probability": 42, "confidence": 88},
                    "heart_disease": {"risk_level": "Low", "probability": 21, "confidence": 86}
                },
                "factors": [
                    {"name": "Elevated HbA1c (5.9%)", "weight": 22, "positive": True},
                    {"name": "Family History of Diabetes (1 Parent)", "weight": 15, "positive": True}
                ],
                "recommendations": [
                    "Schedule a laboratory HbA1c review with a primary care physician.",
                    "Monitor cardiovascular markers..."
                ],
                "timestamp": "2026-06-10T12:00:00",
                "source": "ml_model"
            }
        }
    }


# ─────────────────────────────────────────────────
# HISTORY MODELS
# ─────────────────────────────────────────────────
class AssessmentHistoryRecord(BaseModel):
    id: int
    timestamp: datetime
    patient_name: str
    mrn: str
    age: int
    gender: str
    diabetes_risk_level: str
    diabetes_probability: int
    heart_risk_level: str
    heart_probability: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "timestamp": "2026-06-10T13:30:00",
                "patient_name": "John Doe",
                "mrn": "MRN-12345",
                "age": 45,
                "gender": "Male",
                "diabetes_risk_level": "Medium",
                "diabetes_probability": 42,
                "heart_risk_level": "Low",
                "heart_probability": 18
            }
        }
    }


# ─────────────────────────────────────────────────
# CHATBOT MODELS
# ─────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[ChatMessage] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What does a high HbA1c of 7.2 mean?",
                "history": [
                    {"role": "user", "content": "Hello HealthOracle AI!"},
                    {"role": "assistant", "content": "Hello! I am your pre-screening assistant. How can I help you understand your metrics today?"}
                ]
            }
        }
    }


