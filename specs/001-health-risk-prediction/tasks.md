# Tasks: Health Risk Prediction

**Input**: Design documents from `/specs/001-health-risk-prediction/`

**Prerequisites**: plan.md (required), spec.md (required), constitution.md

**Organization**: Tasks are organized into chronological development phases, separating setup, model construction, backend development, frontend construction, and final verification.

---

## Phase 1: Setup & Infrastructure

**Purpose**: Set up directories, files, package files, and configuration.

- [ ] T001 Create folders: `dataset/`, `backend/src`, `backend/tests`, `frontend/`
- [ ] T002 Create `backend/requirements.txt` with dependencies: `fastapi`, `uvicorn`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `pydantic`, `pytest`
- [ ] T003 [P] Configure python virtual environment and verify dependencies can install

---

## Phase 2: Foundational Data & ML Model (Priority: P1)

**Purpose**: Prepare dataset and train the machine learning models.

- [ ] T004 Create `dataset/health_data.csv` with columns: `age`, `gender`, `fever`, `fatigue`, `sleep_hours`, `diet_quality`, `smoking`, `diabetes_risk`, `heart_disease_risk` (seed with mock data)
- [ ] T005 Create `backend/src/model.py` containing class/functions to preprocess data, train models, and serialize to `diabetes_model.joblib` and `heart_model.joblib`
- [ ] T006 Write tests in `backend/tests/test_model.py` to verify dataset loader, shape checks, and classifier training scores (F1 > 0.8)
- [ ] T007 Execute model training script once to generate serialization files

---

## Phase 3: Backend API Development (Priority: P2)

**Purpose**: Create FastAPI endpoints to accept user input, load models, predict risk, and output suggestions.

- [ ] T008 Implement Pydantic schema contracts in `backend/src/app.py` for `/predict` request inputs and response outputs (containing risk levels, probability, confidence, recommendations, and disclaimer)
- [ ] T009 Implement model loading and prediction logic in `backend/src/app.py` (loads joblib files and runs inference)
- [ ] T010 Implement lifestyle recommendation rules in `backend/src/utils.py` based on output risk and lifestyle parameters
- [ ] T011 Write tests in `backend/tests/test_routes.py` for `/predict` to verify valid inputs, negative values, missing parameters, and formatting of response payload

---

## Phase 4: Frontend User Interface (Priority: P3)

**Purpose**: Build the client side interface to submit data and view prediction reports.

- [ ] T012 Design a modern, premium form layout in `frontend/index.html` with inputs for age, gender, symptom checkboxes, and lifestyle sliders
- [ ] T013 Create dynamic stylesheet `frontend/styles.css` using sleek dark mode and HSL tailoring colors
- [ ] T014 Implement API fetch handler in `frontend/script.js` to send user inputs to FastAPI `/predict` route
- [ ] T015 Render prediction outcome cards in the UI dynamically (color code risk levels: red for High, orange for Medium, green for Low)
- [ ] T016 Include static and response-driven medical disclaimers prominently in the frontend layout

---

## Phase 5: Verification & Polish

**Purpose**: Cross-cutting verification and final verification checks.

- [ ] T017 Run backend unit and integration test suites using `pytest` and confirm all tests pass
- [ ] T018 Perform end-to-end manual testing from browser client to ensure prediction is output correctly
- [ ] T019 Clean up codebase, format Python files with black/flake8, and update project documentation
