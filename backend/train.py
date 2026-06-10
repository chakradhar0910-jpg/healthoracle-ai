"""
HealthOracle AI — Model Training Pipeline
==========================================
Strategy:
  1. Download real public datasets (PIMA Indians Diabetes + UCI Heart Disease)
  2. Map them to our 16/18-feature schema
  3. Generate synthetic augmentation rows with realistic medical distributions
  4. Merge, balance with SMOTE, train Random Forest + Gradient Boosting ensemble
  5. Save models + scalers to backend/models/

Run:  python backend/train.py
"""

import os
import sys
import io
import warnings
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import joblib

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, roc_auc_score, accuracy_score, confusion_matrix
)
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
MODELS_DIR  = BASE_DIR / "models"
DATASET_DIR = BASE_DIR.parent / "dataset"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# ── Real Dataset URLs ──────────────────────────────────────────────────────
# PIMA Indians Diabetes (768 rows) — from OpenML / kaggle mirror
PIMA_URL = (
    "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
)
# UCI Cleveland Heart Disease (303 rows) — from UCI ML Repo CSV mirror
HEART_URL = (
    "https://raw.githubusercontent.com/YBIFoundation/Dataset/main/Heart%20Disease.csv"
)

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


# ══════════════════════════════════════════════════════════════════════
# 1.  SYNTHETIC DATA GENERATOR
#     Generates realistic synthetic rows matching our feature schema.
#     Uses published prevalence rates and clinical reference ranges.
# ══════════════════════════════════════════════════════════════════════

def generate_synthetic_diabetes(n: int = 1500) -> pd.DataFrame:
    """
    Synthetic Diabetes dataset matching our 16-feature schema.
    Columns:
      age, gender, bmi, glucose, hba1c, family_diabetes,
      smoking, physical_activity, diet_quality, stress_level,
      sleep_hours, hypertension, obesity, sym_polyuria,
      sym_polydipsia, sym_numbness  →  target
    """
    rng = np.random.default_rng(RANDOM_STATE)
    rows = []
    for _ in range(n):
        age            = int(rng.integers(18, 80))
        gender         = int(rng.integers(0, 2))          # 0=F, 1=M
        bmi            = float(rng.normal(27.5, 6.0))
        bmi            = np.clip(bmi, 15, 55)

        # Base risk score
        risk = 0.05
        risk += max(0, (age - 35) * 0.006)
        risk += (bmi - 22) * 0.012 if bmi > 22 else 0

        family_db = int(rng.choice([0, 1, 2], p=[0.60, 0.28, 0.12]))
        risk += family_db * 0.10

        smoking       = int(rng.choice([0, 1, 2], p=[0.55, 0.20, 0.25]))
        physical_act  = int(rng.choice([0, 1, 2], p=[0.25, 0.50, 0.25]))
        diet_quality  = int(rng.integers(1, 11))
        stress_level  = int(rng.integers(1, 11))
        sleep_hours   = float(round(rng.normal(7.0, 1.2), 1))
        sleep_hours   = np.clip(sleep_hours, 4.0, 10.0)

        risk += (smoking == 2) * 0.05
        risk += (physical_act == 0) * 0.07
        risk += max(0, (7 - diet_quality) * 0.01)

        hypertension  = int(rng.random() < 0.28 + risk * 0.3)
        obesity       = int(bmi >= 30)

        risk += hypertension * 0.08
        risk += obesity * 0.14
        risk = np.clip(risk, 0, 0.97)

        has_diabetes  = int(rng.random() < risk)

        # Lab values shaped by diabetes status
        if has_diabetes:
            glucose = float(rng.normal(155, 35))
            hba1c   = float(rng.normal(7.8, 1.2))
        else:
            glucose = float(rng.normal(92, 15))
            hba1c   = float(rng.normal(5.3, 0.4))

        glucose = np.clip(glucose, 50, 450)
        hba1c   = np.clip(hba1c, 3.5, 14.0)

        sym_polyuria   = int(rng.random() < (0.6 if has_diabetes else 0.03))
        sym_polydipsia = int(rng.random() < (0.55 if has_diabetes else 0.02))
        sym_numbness   = int(rng.random() < (0.35 if has_diabetes else 0.04))

        rows.append([
            age, gender, round(bmi, 1), round(glucose, 1), round(hba1c, 2),
            family_db, smoking, physical_act, diet_quality, stress_level,
            round(sleep_hours, 1), hypertension, obesity,
            sym_polyuria, sym_polydipsia, sym_numbness,
            has_diabetes
        ])

    cols = [
        "age", "gender", "bmi", "glucose", "hba1c",
        "family_diabetes", "smoking", "physical_activity",
        "diet_quality", "stress_level", "sleep_hours",
        "hypertension", "obesity",
        "sym_polyuria", "sym_polydipsia", "sym_numbness",
        "target"
    ]
    return pd.DataFrame(rows, columns=cols)


def generate_synthetic_heart(n: int = 1500) -> pd.DataFrame:
    """
    Synthetic Heart Disease dataset matching our 18-feature schema.
    Columns:
      age, gender, bmi, systolic, diastolic,
      cholesterol, ldl, hdl, triglycerides,
      family_heart, smoking, physical_activity, alcohol,
      stress_level, sleep_hours, hypertension,
      hyperlipidemia, sym_chest_pain  →  target
    """
    rng = np.random.default_rng(RANDOM_STATE + 1)
    rows = []
    for _ in range(n):
        age           = int(rng.integers(18, 80))
        gender        = int(rng.integers(0, 2))
        bmi           = float(rng.normal(27.5, 6.0))
        bmi           = np.clip(bmi, 15, 55)

        risk = 0.04
        risk += max(0, (age - 40) * 0.007)
        risk += (gender == 1) * 0.04   # male slightly higher base

        family_hd = int(rng.choice([0, 1, 2], p=[0.65, 0.26, 0.09]))
        risk += family_hd * 0.10

        smoking       = int(rng.choice([0, 1, 2], p=[0.55, 0.18, 0.27]))
        physical_act  = int(rng.choice([0, 1, 2], p=[0.25, 0.50, 0.25]))
        alcohol       = int(rng.choice([0, 1, 2], p=[0.40, 0.45, 0.15]))
        stress_level  = int(rng.integers(1, 11))
        sleep_hours   = float(round(rng.normal(7.0, 1.2), 1))
        sleep_hours   = np.clip(sleep_hours, 4.0, 10.0)

        risk += (smoking == 2) * 0.10
        risk += (physical_act == 0) * 0.06
        risk += (alcohol == 2) * 0.05
        risk += max(0, (stress_level - 5) * 0.012)
        risk += (bmi >= 30) * 0.06
        risk = np.clip(risk, 0, 0.97)

        has_heart = int(rng.random() < risk)

        hypertension   = int(rng.random() < (0.55 if has_heart else 0.22))
        hyperlipidemia = int(rng.random() < (0.50 if has_heart else 0.20))
        risk += hypertension * 0.12 + hyperlipidemia * 0.08

        if has_heart:
            systolic      = float(rng.normal(148, 22))
            diastolic     = float(rng.normal(94, 14))
            cholesterol   = float(rng.normal(238, 40))
            ldl           = float(rng.normal(152, 35))
            hdl           = float(rng.normal(38, 10) if gender == 1 else rng.normal(45, 10))
            triglycerides = float(rng.normal(210, 60))
        else:
            systolic      = float(rng.normal(118, 14))
            diastolic     = float(rng.normal(76, 10))
            cholesterol   = float(rng.normal(192, 32))
            ldl           = float(rng.normal(108, 28))
            hdl           = float(rng.normal(52, 12) if gender == 1 else rng.normal(60, 12))
            triglycerides = float(rng.normal(125, 45))

        systolic      = np.clip(systolic, 80, 220)
        diastolic     = np.clip(diastolic, 45, 130)
        cholesterol   = np.clip(cholesterol, 100, 450)
        ldl           = np.clip(ldl, 30, 330)
        hdl           = np.clip(hdl, 18, 120)
        triglycerides = np.clip(triglycerides, 40, 550)

        sym_chest_pain = int(rng.random() < (0.55 if has_heart else 0.04))

        rows.append([
            age, gender, round(bmi, 1),
            round(systolic, 0), round(diastolic, 0),
            round(cholesterol, 0), round(ldl, 0), round(hdl, 0), round(triglycerides, 0),
            family_hd, smoking, physical_act, alcohol,
            stress_level, round(sleep_hours, 1),
            hypertension, hyperlipidemia, sym_chest_pain,
            has_heart
        ])

    cols = [
        "age", "gender", "bmi",
        "systolic", "diastolic",
        "cholesterol", "ldl", "hdl", "triglycerides",
        "family_heart", "smoking", "physical_activity", "alcohol",
        "stress_level", "sleep_hours",
        "hypertension", "hyperlipidemia", "sym_chest_pain",
        "target"
    ]
    return pd.DataFrame(rows, columns=cols)


# ══════════════════════════════════════════════════════════════════════
# 2.  REAL DATASET LOADERS
# ══════════════════════════════════════════════════════════════════════

def load_pima_diabetes() -> pd.DataFrame:
    """
    PIMA Indians Diabetes dataset (768 rows, 8 features).
    Maps columns to our 16-feature schema.
    """
    log.info("📥 Downloading PIMA Indians Diabetes dataset...")
    try:
        resp = requests.get(PIMA_URL, timeout=15)
        resp.raise_for_status()
        raw_cols = [
            "pregnancies", "glucose", "diastolic", "skin_thickness",
            "insulin", "bmi", "dpf", "age", "target"
        ]
        df = pd.read_csv(io.StringIO(resp.text), header=None, names=raw_cols)
        log.info("  ✅ PIMA loaded: %d rows", len(df))

        # Map to our schema — fill unavailable features with population defaults
        out = pd.DataFrame()
        out["age"]             = df["age"]
        out["gender"]          = 0            # All female in PIMA
        out["bmi"]             = df["bmi"].replace(0, np.nan).fillna(27.5)
        out["glucose"]         = df["glucose"].replace(0, np.nan).fillna(99)
        out["hba1c"]           = (df["glucose"] / 18.0 * 0.15 + 4.0).clip(4.0, 12.0)  # Approx from glucose
        out["family_diabetes"] = (df["dpf"] > 0.5).astype(int)                        # 0 or 1
        out["smoking"]         = 0            # Not available → assume Never
        out["physical_activity"]= 1           # Not available → assume Medium
        out["diet_quality"]    = 6
        out["stress_level"]    = 5
        out["sleep_hours"]     = 7.0
        out["hypertension"]    = ((df["diastolic"] >= 90) | (df["diastolic"] == 0)).astype(int)
        out["obesity"]         = (df["bmi"] >= 30).astype(int)
        out["sym_polyuria"]    = (df["glucose"] >= 126).astype(int)
        out["sym_polydipsia"]  = (df["glucose"] >= 126).astype(int)
        out["sym_numbness"]    = 0
        out["target"]          = df["target"]
        return out.dropna()
    except Exception as e:
        log.warning("  ⚠️  PIMA download failed (%s) — will use synthetic only.", e)
        return pd.DataFrame()


def load_uci_heart() -> pd.DataFrame:
    """
    UCI/YBI Heart Disease dataset.
    Maps columns to our 18-feature schema.
    """
    log.info("📥 Downloading UCI Heart Disease dataset...")
    try:
        resp = requests.get(HEART_URL, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        log.info("  ✅ Heart dataset loaded: %d rows, cols: %s", len(df), list(df.columns)[:8])

        # Normalise column names
        df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

        # Try to find target column
        target_col = None
        for c in ["target", "heart_disease", "output", "num", "condition", "disease"]:
            if c in df.columns:
                target_col = c
                break
        if target_col is None:
            log.warning("  ⚠️  Could not identify target column in heart dataset.")
            return pd.DataFrame()

        out = pd.DataFrame()
        out["age"]              = df.get("age", 50)
        out["gender"]           = df.get("sex", df.get("gender", 1)).astype(int)
        out["bmi"]              = 27.5  # Not in Cleveland — use default

        # Map available columns
        cp = df.get("cp", df.get("chest_pain_type", 0))
        trestbps = df.get("trestbps", df.get("resting_bp", df.get("blood_pressure", 120)))
        chol     = df.get("chol", df.get("cholesterol", df.get("serum_cholestoral_in_mg/dl", 195)))
        thalach  = df.get("thalach", df.get("max_heart_rate", df.get("maximum_heart_rate_achieved", 150)))
        oldpeak  = df.get("oldpeak", df.get("st_depression", 0))
        fbs      = df.get("fbs", df.get("fasting_blood_sugar", 0))

        out["systolic"]         = trestbps
        out["diastolic"]        = (trestbps * 0.64).round(0)  # Approximate diastolic
        out["cholesterol"]      = chol
        out["ldl"]              = (chol * 0.55).round(0)       # Approximate LDL
        out["hdl"]              = (chol * 0.22).round(0)       # Approximate HDL
        out["triglycerides"]    = 130.0
        out["family_heart"]     = 0
        out["smoking"]          = 0
        out["physical_activity"]= 1
        out["alcohol"]          = 0
        out["stress_level"]     = 5
        out["sleep_hours"]      = 7.0
        out["hypertension"]     = (trestbps >= 130).astype(int)
        out["hyperlipidemia"]   = (chol >= 200).astype(int)
        out["sym_chest_pain"]   = (cp > 0).astype(int)
        out["target"]           = (df[target_col] > 0).astype(int)   # Binarise

        return out.dropna()
    except Exception as e:
        log.warning("  ⚠️  Heart dataset download failed (%s) — will use synthetic only.", e)
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════
# 3.  TRAINING FUNCTION
# ══════════════════════════════════════════════════════════════════════

DIABETES_FEATURES = [
    "age", "gender", "bmi", "glucose", "hba1c",
    "family_diabetes", "smoking", "physical_activity",
    "diet_quality", "stress_level", "sleep_hours",
    "hypertension", "obesity",
    "sym_polyuria", "sym_polydipsia", "sym_numbness"
]

HEART_FEATURES = [
    "age", "gender", "bmi",
    "systolic", "diastolic",
    "cholesterol", "ldl", "hdl", "triglycerides",
    "family_heart", "smoking", "physical_activity", "alcohol",
    "stress_level", "sleep_hours",
    "hypertension", "hyperlipidemia", "sym_chest_pain"
]


def build_ensemble(use_smote: bool = True):
    """
    Returns a soft-voting ensemble of:
      - RandomForest
      - GradientBoosting
      - LogisticRegression (calibrated)
    """
    rf  = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=2,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
    )
    gb  = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=4,
        subsample=0.8, random_state=RANDOM_STATE
    )
    lr  = LogisticRegression(
        C=0.5, max_iter=1000, class_weight="balanced",
        random_state=RANDOM_STATE
    )
    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb), ("lr", lr)],
        voting="soft",
        weights=[3, 2, 1]       # Weight RF & GB more than LR
    )
    return ensemble


def train_and_evaluate(X: np.ndarray, y: np.ndarray, label: str):
    """Train ensemble, evaluate, return (model, scaler)."""
    log.info("\n═══ Training: %s ═══", label)
    log.info("  Dataset size : %d rows | Positive class: %d (%.1f%%)",
             len(y), y.sum(), 100 * y.mean())

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    # Scale features
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # Optional SMOTE for class imbalance
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=5)
        X_res, y_res = smote.fit_resample(X_train_s, y_train)
        log.info("  SMOTE resampled: %d → %d rows", len(y_train), len(y_res))
    except ImportError:
        log.warning("  imbalanced-learn not installed — skipping SMOTE.")
        X_res, y_res = X_train_s, y_train

    model = build_ensemble()
    model.fit(X_res, y_res)

    # Evaluate
    y_pred  = model.predict(X_test_s)
    y_proba = model.predict_proba(X_test_s)[:, 1]

    acc  = accuracy_score(y_test, y_pred)
    auc  = roc_auc_score(y_test, y_proba)
    log.info("  Test Accuracy : %.3f", acc)
    log.info("  Test ROC-AUC  : %.3f", auc)
    log.info("  Confusion Matrix:\n%s", confusion_matrix(y_test, y_pred))
    log.info("  Classification Report:\n%s", classification_report(y_test, y_pred))

    # Cross-validation
    cv_scores = cross_val_score(
        build_ensemble(), scaler.transform(X), y,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE),
        scoring="roc_auc", n_jobs=-1
    )
    log.info("  5-Fold CV AUC : %.3f ± %.3f", cv_scores.mean(), cv_scores.std())

    return model, scaler


# ══════════════════════════════════════════════════════════════════════
# 4.  MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    log.info("🏥 HealthOracle AI — Model Training Pipeline")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # ────────────── DIABETES ──────────────────────────────────────
    log.info("\n📊 Building DIABETES training set...")
    synth_db = generate_synthetic_diabetes(n=2000)
    log.info("  Synthetic rows: %d", len(synth_db))

    real_db = load_pima_diabetes()
    if not real_db.empty:
        # Align columns
        for c in DIABETES_FEATURES:
            if c not in real_db.columns:
                real_db[c] = 0
        real_db = real_db[DIABETES_FEATURES + ["target"]]
        all_db = pd.concat([synth_db, real_db], ignore_index=True)
        log.info("  Real rows added: %d  →  Total: %d", len(real_db), len(all_db))
    else:
        all_db = synth_db

    all_db.to_csv(DATASET_DIR / "diabetes_training.csv", index=False)
    log.info("  Saved training CSV → dataset/diabetes_training.csv")

    X_db = all_db[DIABETES_FEATURES].values.astype(np.float64)
    y_db = all_db["target"].values.astype(int)

    db_model, db_scaler = train_and_evaluate(X_db, y_db, "Diabetes Risk Model")
    joblib.dump(db_model,  MODELS_DIR / "diabetes_model.pkl")
    joblib.dump(db_scaler, MODELS_DIR / "diabetes_scaler.pkl")
    log.info("  ✅ diabetes_model.pkl + diabetes_scaler.pkl saved.")

    # ────────────── HEART DISEASE ─────────────────────────────────
    log.info("\n📊 Building HEART DISEASE training set...")
    synth_hd = generate_synthetic_heart(n=2000)
    log.info("  Synthetic rows: %d", len(synth_hd))

    real_hd = load_uci_heart()
    if not real_hd.empty:
        for c in HEART_FEATURES:
            if c not in real_hd.columns:
                real_hd[c] = 0
        real_hd = real_hd[HEART_FEATURES + ["target"]]
        all_hd = pd.concat([synth_hd, real_hd], ignore_index=True)
        log.info("  Real rows added: %d  →  Total: %d", len(real_hd), len(all_hd))
    else:
        all_hd = synth_hd

    all_hd.to_csv(DATASET_DIR / "heart_training.csv", index=False)
    log.info("  Saved training CSV → dataset/heart_training.csv")

    X_hd = all_hd[HEART_FEATURES].values.astype(np.float64)
    y_hd = all_hd["target"].values.astype(int)

    hd_model, hd_scaler = train_and_evaluate(X_hd, y_hd, "Cardiovascular Risk Model")
    joblib.dump(hd_model,  MODELS_DIR / "heart_model.pkl")
    joblib.dump(hd_scaler, MODELS_DIR / "heart_scaler.pkl")
    log.info("  ✅ heart_model.pkl + heart_scaler.pkl saved.")

    # Save feature metadata for traceability
    meta = {
        "diabetes_features": DIABETES_FEATURES,
        "heart_features": HEART_FEATURES,
        "diabetes_train_rows": len(all_db),
        "heart_train_rows": len(all_hd),
        "diabetes_positive_rate": float(y_db.mean()),
        "heart_positive_rate": float(y_hd.mean()),
    }
    with open(MODELS_DIR / "model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    log.info("\n✅ All models trained and saved successfully!")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("Next step: uvicorn backend.app:app --reload")


if __name__ == "__main__":
    main()
