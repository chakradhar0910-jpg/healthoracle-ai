# HealthOracle AI — User Manual

This manual explains how to set up, train, and run **HealthOracle AI**, an intelligent pre-screening suite designed to predict patient risk levels for **Diabetes** and **Cardiovascular Disease**.

---

## 📌 Features
- **Intelligent Pre-Screening**: Evaluates custom biometric, demographic, and laboratory values to estimate risk percentages.
- **Machine Learning Backend**: Powered by an ensemble classifier (Random Forest, Gradient Boosting, and Logistic Regression).
- **Offline Mode (Local Fallback)**: The application features an offline inference engine built in Vanilla JavaScript. If the backend API cannot be reached, the frontend switches to rule-based logic automatically.
- **Explainability Checklist**: Generates a summary checklist explaining the positive and negative risk factors leading to a given prediction.

---

## ⚙️ Requirements & Installation

Ensure you have **Python 3.9+** and `pip` installed on your machine.

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```
Key packages include:
- `fastapi` & `uvicorn` (Backend API Web Server)
- `scikit-learn` (Machine Learning models and pipelines)
- `pandas` & `numpy` (Data ingestion and manipulation)
- `imbalanced-learn` (SMOTE implementation for handling class imbalance)

---

## 📊 Training the ML Models

Before starting the web server, you must train the models to generate the serialized pipeline files:

```bash
python backend/train.py
```

### What this script does:
1. Downloads the baseline dataset files:
   - **PIMA Indians Diabetes** dataset for diabetes training.
   - **UCI Cleveland Heart Disease** dataset for cardiovascular risk training.
2. Augments the dataset by generating **2,000 synthetic rows** per model using medical distributions to ensure robust predictions.
3. Trains a **VotingClassifier Ensemble** combining:
   - Random Forest (300 estimators)
   - Gradient Boosting (200 estimators)
   - Logistic Regression (Calibrated)
4. Saves the resulting model packages and feature scalers to `backend/models/`.

---

## ⚡ Running the Application

### 1. Start the Backend API
Run the Uvicorn ASGI server to expose the REST API:
```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```
- The backend API will be available at `http://127.0.0.1:8000`.
- Access the interactive documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

### 2. Open the Frontend UI
Since the frontend is built entirely using HTML5, Vanilla CSS, and Vanilla JavaScript:
1. Locate the `frontend/` directory.
2. Open `frontend/index.html` directly in any modern web browser.
3. A **green status pill** labeled "CONNECTED" in the top-right header verifies that the frontend has successfully established a connection with the local API.

---

## ⚠️ Clinical Disclaimer

> [!WARNING]
> HealthOracle AI is a screening tool designed strictly for **educational and early-awareness purposes**. It is **NOT** a substitute for professional medical advice, clinical diagnosis, or treatment. 
> Always consult a qualified medical professional for health evaluations. In case of emergency medical issues (e.g., sudden chest pain or shortness of breath), call your local emergency number immediately.
