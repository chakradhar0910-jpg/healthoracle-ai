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
