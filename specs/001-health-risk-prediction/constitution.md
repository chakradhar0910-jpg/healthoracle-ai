# HealthOracle AI Constitution

## Core Principles

### I. Modular ML Pipeline (Library-First)
The machine learning models, training scripts, and preprocessing logic must exist as a self-contained library in the backend, completely independent of the FastAPI routing layer. This ensures that the ML model can be run, trained, and tested from the command line interface (CLI) or inside Python scripts without running the web server.

### II. Explicit Request/Response Contracts
All inputs and outputs for health predictions must be strictly validated. The backend must use Pydantic models to define clear validation rules for symptom indicators, lifestyle parameters (diet, sleep hours, smoking status), and demographics (age, gender). The API must return explicit types for risk level, confidence scores, and recommendations.

### III. Test-Driven Development (TDD)
Before implementing prediction endpoint logic or dataset parsing, write appropriate test cases. Prediction accuracy must be validated using unit tests, and FastAPI request routing must have integration tests to ensure reliable, green-light API behavior under bad, missing, or malformed inputs.

### IV. Safety & Medical Disclaimers
Because HealthOracle AI predicts disease risk levels, every response payload and the frontend UI must show a prominent medical disclaimer. Predictions are for educational and awareness purposes only and must explicitly advise the user to seek professional medical advice.

### V. Simplicity & Local Standalone Execution
The application should require zero external cloud services (excluding standard local Python environment packages) to execute. The dataset, models, backend API, and frontend should run entirely locally to protect mock patient/user privacy and maintain simple execution for developers.

## Health Risk Prediction System Constraints

- **Technology Stack**: Python 3.11 (FastAPI, Scikit-learn, Pandas, NumPy), HTML/CSS/JavaScript.
- **Model Accuracy**: Trained models must achieve a minimum accuracy and F1-score of 80% on test datasets before being integrated.
- **Data Protection**: All mock health data inputs are kept local and must not be sent to external logging databases.

## Development Workflow & Quality Gates

1. **Model Checkpoint**: Models must be evaluated and output prediction reports to console before serialization.
2. **API Gate**: Code style must follow standard Python coding rules (PEP 8), and all tests in `backend/tests/` must pass.
3. **Frontend Gate**: No UI placeholders. The layout must be fully responsive and tested for visual clarity.

## Governance

Any structural changes to the dataset schema, Pydantic inputs, or ML model packaging must be documented and update the contracts first.

**Version**: 1.0.0 | **Ratified**: 2026-06-09 | **Last Amended**: 2026-06-09
