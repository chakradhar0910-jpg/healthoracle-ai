# 🧠 HealthOracle AI — Clinical Pre-Screening Suite
### *Predict Before It Hurts* — v4.0 Hospital Grade

---

## 📌 Overview
**HealthOracle AI** is an intelligent health risk prediction system that analyzes patient data (symptoms, lifestyle, biometrics, lab values) to **predict Diabetes and Cardiovascular disease risk** with ML-powered confidence scores and clinical recommendations.

---
##live demo 
           https://healthoracle-ai-1.onrender.com

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, Vanilla CSS, Vanilla JS (no framework) |
| Backend | Python · FastAPI · Uvicorn |
| ML Models | scikit-learn (Random Forest + GradientBoosting + LR Ensemble) |
| Data | PIMA Indians Diabetes + UCI Cleveland Heart + Synthetic augmentation |
| Feature Scaling | StandardScaler (saved with model) |
| Class Balance | SMOTE (imbalanced-learn) |

---

## 📂 Project Structure

```
HealthOracle-AI/
│
├── backend/
│   ├── __init__.py        # Python package marker
│   ├── app.py             # FastAPI entry point + CORS + endpoints
│   ├── model.py           # ML model singleton loader + prediction
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── train.py           # Training pipeline (real data + synthetic)
│   ├── utils.py           # Feature engineering + recommendations
│   └── models/            # Trained .pkl files (auto-generated)
│       ├── diabetes_model.pkl
│       ├── diabetes_scaler.pkl
│       ├── heart_model.pkl
│       ├── heart_scaler.pkl
│       └── model_meta.json
│
├── dataset/               # Auto-generated training datasets
│   ├── diabetes_training.csv
│   └── heart_training.csv
│
├── frontend/
│   ├── index.html         # Main app shell (3-step form + results dashboard)
│   ├── styles.css         # Apple-inspired glassmorphism dark UI
│   └── script.js          # Form logic + local inference fallback + API calls
│
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the ML Models
```bash
python backend/train.py
```
This will:
- Download the real **PIMA Indians Diabetes** dataset (~768 rows)
- Download the real **UCI Heart Disease** dataset (~303 rows)  
- Generate **2,000 synthetic rows** per disease with realistic medical distributions
- Train a **VotingClassifier ensemble** (Random Forest + Gradient Boosting + Logistic Regression)
- Print accuracy, ROC-AUC, and 5-fold cross-validation scores
- Save models to `backend/models/`

### 3. Start the API Server
```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

### 4. Open the Frontend
Just open `frontend/index.html` in your browser.

The **green status pill** in the header confirms the backend is connected.

---

## 🔌 API Reference

### `GET /`
Health check — polled by the frontend every 10 seconds.

```json
{ "status": "ok", "models_ready": true, "version": "4.0.0" }
```

### `POST /predict`
Submit patient data, receive ML predictions.

**Request body** (all optional lab fields supported):
```json
{
  "patientName": "John Doe",
  "age": 52,
  "gender": "Male",
  "height": 175,
  "weight": 85,
  "systolic": 135,
  "diastolic": 85,
  "glucose": 108,
  "hba1c": 5.9,
  "cholesterol": 210,
  "ldl": 135,
  "hdl": 42,
  "triglycerides": 160,
  "sleepHours": 6.5,
  "dietQuality": 6,
  "stressLevel": 7,
  "smoking": "Former",
  "physicalActivity": "Medium",
  "alcohol": "Moderate",
  "familyDiabetes": "One",
  "familyHeart": "None",
  "symptoms": ["fatigue", "polyuria"],
  "comorbidities": ["hypertension"]
}
```

**Response:**
```json
{
  "predictions": {
    "diabetes":      { "risk_level": "Medium", "probability": 42, "confidence": 88 },
    "heart_disease": { "risk_level": "Low",    "probability": 21, "confidence": 86 }
  },
  "factors": [
    { "name": "Elevated HbA1c (5.9%)", "weight": 22, "positive": true },
    { "name": "Family History of Diabetes (1 Parent)", "weight": 15, "positive": true }
  ],
  "recommendations": [
    "Schedule a laboratory HbA1c review with a primary care physician.",
    "Monitor cardiovascular markers..."
  ],
  "timestamp": "2026-06-10T12:00:00",
  "source": "ml_model"
}
```

### `GET /docs`
Interactive Swagger UI for the API.

### `GET /model-info`
Returns training metadata (feature list, dataset sizes, positive rates).

---

## 🤖 ML Model Details

### Architecture: Soft-Voting Ensemble
| Model | Weight |
|-------|--------|
| Random Forest (300 trees, max_depth=12) | 3× |
| Gradient Boosting (200 trees, lr=0.05) | 2× |
| Logistic Regression (L2, calibrated) | 1× |

### Training Data
| Disease | Real Rows | Synthetic Rows | Total |
|---------|-----------|----------------|-------|
| Diabetes | 768 (PIMA) | 2,000 | 2,768 |
| Heart Disease | 303 (Cleveland) | 2,000 | 2,303 |

### Features
**Diabetes (16 features):** Age, Gender, BMI, Fasting Glucose, HbA1c, Family History, Smoking, Physical Activity, Diet Quality, Stress Level, Sleep Hours, Hypertension, Obesity, Polyuria, Polydipsia, Numbness

**Cardiovascular (18 features):** Age, Gender, BMI, Systolic BP, Diastolic BP, Cholesterol, LDL, HDL, Triglycerides, Family History, Smoking, Physical Activity, Alcohol, Stress Level, Sleep Hours, Hypertension, Hyperlipidemia, Chest Pain

### Offline Fallback
The frontend includes a complete **local rule-based inference engine** (`compileLocalClinicalInference`) that activates automatically if the backend is unreachable. The ML backend always takes priority when online.

---

## ⚠️ Clinical Disclaimer
HealthOracle AI is a **screening tool for educational and early awareness purposes only**.  
It is **NOT** a substitute for professional medical advice, diagnosis, or treatment.  
Emergency symptoms (chest pain, severe breathlessness) → call emergency services immediately.

---

## 👨‍💻 Authors
HealthOracle AI Project · 2026 · Hackathon Edition
