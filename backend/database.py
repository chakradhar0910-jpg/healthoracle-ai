"""
HealthOracle AI — Database Persistence Layer
============================================
Establishes the SQLAlchemy engine, configures local sessions,
and declares the database schema for persisting patient prediction history.
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.config import DATABASE_URL

log = logging.getLogger("healthoracle.db")

# ── SQLAlchemy Database Engine Setup ──────────────────────────────────────
# check_same_thread=False is needed only for SQLite to support multi-threading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: Any = declarative_base()


# ── Table Schema Declaration ──────────────────────────────────────────────
class PatientRiskAssessment(Base):
    """Stores a history of risk predictions for analysis and progress tracking."""

    __tablename__ = "patient_risk_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    patient_name = Column(String(255), default="Unknown", nullable=False)
    mrn = Column(String(100), default="N/A", nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(50), nullable=False)
    diabetes_risk_level = Column(String(50), nullable=False)
    diabetes_probability = Column(Integer, nullable=False)
    heart_risk_level = Column(String(50), nullable=False)
    heart_probability = Column(Integer, nullable=False)

    # Expanded Diseases Columns
    kidney_risk_level = Column(String(50), default="Low", nullable=True)
    kidney_probability = Column(Integer, default=0, nullable=True)
    liver_risk_level = Column(String(50), default="Low", nullable=True)
    liver_probability = Column(Integer, default=0, nullable=True)
    stroke_risk_level = Column(String(50), default="Low", nullable=True)
    stroke_probability = Column(Integer, default=0, nullable=True)
    cancer_risk_level = Column(String(50), default="Low", nullable=True)
    cancer_probability = Column(Integer, default=0, nullable=True)

    payload_json = Column(Text, nullable=False)  # Raw submitted JSON for auditing


# ── Database Initialization ───────────────────────────────────────────────
def init_db():
    """Initializes and creates all database tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        log.info("💾 Database tables initialized successfully.")
    except Exception as e:
        log.critical("❌ Failed to initialize database tables: %s", e, exc_info=True)
        raise


def get_db():
    """FastAPI dependency yielding a thread-safe database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── CRUD Operations ────────────────────────────────────────────────────────
def save_assessment(
    db: Session,
    payload_dict: dict[str, Any],
    db_prob: int,
    db_risk: str,
    hd_prob: int,
    hd_risk: str,
    kd_prob: int = 0,
    kd_risk: str = "Low",
    ld_prob: int = 0,
    ld_risk: str = "Low",
    st_prob: int = 0,
    st_risk: str = "Low",
    ca_prob: int = 0,
    ca_risk: str = "Low",
) -> PatientRiskAssessment | None:
    """Persists a prediction result to the history database."""
    try:
        assessment = PatientRiskAssessment(
            patient_name=payload_dict.get("patientName", "Unknown"),
            mrn=payload_dict.get("mrn", "N/A"),
            age=payload_dict.get("age"),
            gender=payload_dict.get("gender"),
            diabetes_risk_level=db_risk,
            diabetes_probability=db_prob,
            heart_risk_level=hd_risk,
            heart_probability=hd_prob,
            kidney_risk_level=kd_risk,
            kidney_probability=kd_prob,
            liver_risk_level=ld_risk,
            liver_probability=ld_prob,
            stroke_risk_level=st_risk,
            stroke_probability=st_prob,
            cancer_risk_level=ca_risk,
            cancer_probability=ca_prob,
            payload_json=json.dumps(payload_dict),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        log.debug("💾 Saved assessment to DB with ID: %s", assessment.id)
        return assessment
    except Exception as e:
        db.rollback()
        log.error("❌ Failed to save assessment to database: %s", e, exc_info=True)
        return None


def get_assessments(db: Session, limit: int = 100) -> list[PatientRiskAssessment]:
    """Retrieves list of past patient risk assessment runs sorted by time descending."""
    try:
        return (
            db.query(PatientRiskAssessment)
            .order_by(PatientRiskAssessment.timestamp.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        log.error("❌ Failed to query assessments: %s", e, exc_info=True)
        return []
