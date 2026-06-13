# Developer & AI Agent Context (AGENTS.md)

Welcome, AI Developer Agent! This document outlines key context, architectural patterns, and quality gates for maintaining and modifying the **HealthOracle AI** codebase.

---

## 🏗 Repository Architecture

```
HealthOracle-AI/
├── .specify/            # Spec-Kit configuration & templates
├── backend/
│   ├── app.py           # FastAPI entry point, endpoints, and CORS config
│   ├── model.py         # Singleton model manager (loads models, scales inputs, predicts)
│   ├── schemas.py       # Pydantic models for validation contracts
│   ├── train.py         # ML model training script (ingests data + synthetic, fits ensemble)
│   └── utils.py         # Feature engineering & patient clinical recommendations
├── frontend/
│   ├── index.html       # Apple-inspired layout (dashboard + forms)
│   ├── styles.css       # Glassmorphism dark mode custom stylesheet
│   └── script.js        # UI logic + API connection + fallback local inference
├── specs/               # Product/feature specs folder
└── tests/               # Backend endpoint & unit test cases
```

---

## 📜 Coding Principles & Rules

### I. Modular ML Pipeline (Library-First)
All data processing, feature scaling, model training, and predictions must remain separate from the web routing layer.
- Keep ML logic in `backend/model.py`, `backend/train.py`, and `backend/utils.py`.
- The routes in `backend/app.py` should only handle HTTP concerns (status codes, request payload validation, and CORS).

### II. Explicit Contracts (Pydantic Models)
Do not pass untyped dictionaries around. Define all request and response structures explicitly using Pydantic schemas in `backend/schemas.py`.

### III. Local Standalone execution
Do not add dependencies on external APIs or database services for core execution. The app must run completely locally.

### IV. Premium UI & No Placeholders
The frontend uses custom vanilla styling. Do not introduce half-implemented features or temporary placeholders. Keep the interface polished, responsive, and cohesive.

---

## 🛠 Tooling & Quality Gates

Ensure that changes do not break the repository quality score:

- **Linting & Formatting**: Enforced via **Ruff**, **Pylint**, and **Flake8**.
  - **Ruff**: Runs fast linter checks. Run `ruff check backend/ tests/`. Format validation runs via `ruff format --check backend/ tests/`. Configured in `pyproject.toml`.
  - **Pylint**: Runs code analysis and quality checks. Run `pylint backend/`. Configured in `.pylintrc` and `pyproject.toml`.
  - **Flake8**: Enforces pep8 style checking. Run `flake8 backend/`. Configured in `.flake8`.
- **Type Checking**: Enforced via **Mypy**. Run `mypy backend/ tests/`. Configured in `pyproject.toml`.
- **Dead Code Detection**: Enforced via **Vulture**. Run `vulture backend/`. Configured in `.vulture` and `pyproject.toml`.
- **Security & SAST Analysis**: Enforced via **Bandit** and **Semgrep**.
  - **Bandit**: Scans for Python security issues. Run `bandit -r backend/ -c bandit.yaml`. Configured in `bandit.yaml` and `pyproject.toml`.
  - **Semgrep**: Scans code with pattern matching. Run `semgrep --config=.semgrep.yaml backend/`. Configured in `.semgrep.yaml`.
- **Code Modernization**: Enforced via **Pyupgrade**. Run `find backend/ -name "*.py" | xargs pyupgrade --py311-plus`. Configured in `pyproject.toml`.
- **Unit Testing**: Enforced via **Pytest** with coverage checks. Run `pytest tests/`.
- **Pre-commit Checks**: Registered hooks check YAML files, trailing whitespaces, enforce Ruff formatting, run type-checking, search for secrets, and audit dependencies.
- **GitLab CI Pipeline**: Configured stages run all of the above tests automatically on commit (`test`, `lint`, `format`, `type_check`, `coverage`).

---

## 🔮 Future Roadmap & Enhancements

Developers and AI Agents should prepare to design and implement the following planned modules in future compliance phases:

### 1. Explainable AI (XAI) — Critical Upgrade
- **Goal**: Right now, the system shows "factors" but not true model explainability.
- **Features**:
  - SHAP (SHapley Additive exPlanations) integration.
  - Per-patient feature contribution graphs.
  - Clear text explanations detailing "Why risk increased/decreased".
- **Output Example**:
  - *Top Contributors*:
    - `+ HbA1c` → `+18%`
    - `+ BMI` → `+12%`
    - `- Physical Activity` → `-8%`
- **Clinical Impact**: Moves from a "black box" system to a trusted, transparent clinic-grade diagnostic companion.

### 🏥 2. Multi-Disease Expansion Engine
- **Goal**: Expand the pre-screening coverage beyond Diabetes and Cardiovascular disease.
- **Features**:
  - Modular disease plugins for:
    - Kidney Disease (Chronic Kidney Disease - CKD)
    - Liver Disease
    - Stroke Risk
    - Cancer pre-screening (basic risk parameters)
  - **Decoupled Architecture**: Models partitioned under `/models/<disease_name>/` (e.g. `diabetes/`, `heart/`, `kidney/`, `liver/`).
- **Clinical Impact**: Transforms HealthOracle AI into a full-scope clinical pre-screening diagnostic suite.

### 📊 3. Real-Time Health Monitoring (Streaming Mode)
- **Goal**: Support real-time streaming health telemetry.
- **Features**:
  - Integration with smartwatch APIs (heart rate, step counts, etc.) and mobile health sensors.
  - FastAPI WebSocket connections to continuously stream patient risk telemetry updates.
  - *Example*: Heart Risk warning triggered due to elevated resting heart rate over the last 24 hours.
- **Clinical Impact**: Transitions predictions from static one-time checks to continuous live health intelligence.

### 🧬 4. Personalized Risk Simulation Engine
- **Goal**: Provide interactive lifestyle simulation.
- **Features**:
  - "What-if" lifestyle changes simulation interface (e.g., losing weight, smoking cessation, sleep improvements).
  - *Output Example*: "If BMI decreases to 24, Diabetes Risk decreases from 42% to 28%".
- **Clinical Impact**: Empowers patients with behavior-changing interactive AI simulations.

### 🧾 5. Clinical Report Generator (PDF Export)
- **Goal**: Enable professional PDF report generation.
- **Features**:
  - Auto-generate standard patient and doctor-ready summaries.
  - Include calculated risk scores, contribution graphs, customized suggestions, and recommended clinical tests.
  - Standard format: `HealthOracle Clinical Summary v1.0`.
- **Clinical Impact**: Makes prediction results immediately actionable and shareable in clinic environments.

### 🧠 6. NLP Symptom Analyzer (Chat-Based Input)
- **Goal**: Support conversational symptom analysis instead of strictly form-based inputs.
- **Features**:
  - Interactive chat console (e.g., patient inputs: "I feel tired, urinate frequently, and lost weight").
  - Run spaCy or Transformers NLP pipelines to parse and map raw text descriptions to structured clinical features.
- **Clinical Impact**: Makes the pre-screening user experience natural, accessible, and intuitive.

### 🧪 7. Patient History & Longitudinal Tracking
- **Goal**: Retain past patient reports to map health progress.
- **Features**:
  - Database schema to store and retrieve sequential predictions.
  - Risk vs. Time interactive tracking graphs (e.g., Jan: 32% → Mar: 41% → June: 48% ⚠️).
- **Clinical Impact**: Enables predictive healthcare tracking and longitudinal preventive medicine.

### 🧪 8. Lab Integration API
- **Goal**: Support direct import of medical laboratory reports.
- **Features**:
  - Document upload portal (PDF/images).
  - OCR models (Tesseract OCR / LLM-based parsers) to extract clinical values.
- **Clinical Impact**: Removes tedious manual data entry and improves patient intake efficiency.

### ⚙️ 9. Model Auto-Retraining Pipeline
- **Goal**: Automate models adaptation based on new data.
- **Features**:
  - Store anonymized patient inputs.
  - Orchestrate cron jobs or Airflow DAGs to retrain models periodically.
  - Implement versioned model checkpoints.
- **Clinical Impact**: Keeps machine learning classifiers clinically relevant and updated.

### 🧠 10. Risk Confidence Calibration Dashboard
- **Goal**: Validate prediction calibration for research-grade accuracy.
- **Features**:
  - Generate calibration curves and reliability diagrams.
  - Compare model confidence scores directly against historical accuracy (e.g. Model confidence: 88% vs. Actual accuracy: 84%).
- **Clinical Impact**: Provides statistical validation required for peer-reviewed research-grade AI tools.

### 🌍 11. Multi-Language + Voice Interface
- **Goal**: Remove accessibility barriers for local adoption.
- **Features**:
  - Interactive voice input command ("Tell symptoms").
  - Support for regional languages (such as Telugu and Hindi).
  - Languages selection dropdown to select and switch client locale.
- **Clinical Impact**: Drives mass healthcare adoption across diverse populations.

### 🚨 12. Emergency Detection Layer
- **Goal**: Enforce rule-based overrides for acute conditions.
- **Features**:
  - Override logic: if acute inputs are detected (e.g., chest pain + high BP), display a prominent warning: "🚨 Possible emergency — seek immediate care".
- **Clinical Impact**: Ensures the pre-screening tool is life-saving and safe.

### 🧬 13. Genetic Risk Integration (Advanced)
- **Goal**: Expand clinical predictions with genetic markers.
- **Features**:
  - Weigh family medical history stronger in prediction algorithms.
  - Interface optional API connectors to DNA/genetic data providers.
- **Clinical Impact**: Advances predictions toward modern precision medicine.

### 📈 14. Doctor Dashboard (Admin Panel)
- **Goal**: Build an administrator dashboard for clinical operators.
- **Features**:
  - Multi-patient overview database showing triage queues.
  - Highlight and prioritize high-risk patients. (e.g., "High Risk Patients Today: 1. John — 78% ⚠️, 2. Priya — 64%").
- **Clinical Impact**: Prepares the platform for smooth hospital and clinical adoption.

### 🤖 15. AI Health Coach (Next-Level Feature)
- **Goal**: Serve as a daily health companion.
- **Features**:
  - Generate dynamic daily goals using a rule engine or reinforcement learning (e.g. "Today Goal: Walk 6,000 steps, reduce sugar intake").
- **Clinical Impact**: Acts as a continuous daily health coaching companion.


