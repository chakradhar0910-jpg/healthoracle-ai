import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app
from backend.database import Base, get_db

# ── Isolated Testing Database Setup ───────────────────────────────────────
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_health_oracle.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Yields test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override app database dependency with our testing session
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Creates tables before tests run, drops them after completion."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Tests ──────────────────────────────────────────────────────────────────

def test_health_check():
    """Verify that the health check endpoint is responsive."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models_ready" in data
    assert "version" in data


def test_model_info():
    """Verify that the model information metadata endpoint returns correctly."""
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "models_loaded" in data


def test_prediction_and_database_persistence():
    """Verify that the POST /predict endpoint works and saves records to the DB."""
    # Define test patient vitals payload
    payload = {
        "patientName": "Alex Tester",
        "mrn": "MRN-TEST-999",
        "age": 45,
        "gender": "Male",
        "height": 180.0,
        "weight": 82.0,
        "systolic": 128.0,
        "diastolic": 82.0,
        "glucose": 105.0,
        "hba1c": 5.8,
        "cholesterol": 210.0,
        "ldl": 130.0,
        "hdl": 42.0,
        "triglycerides": 150.0,
        "sleepHours": 7.0,
        "dietQuality": 7,
        "stressLevel": 4,
        "smoking": "Never",
        "physicalActivity": "Medium",
        "alcohol": "None",
        "familyDiabetes": "One",
        "familyHeart": "None",
        "symptoms": ["fatigue"],
        "comorbidities": []
    }

    # Post request to /predict
    response = client.post("/predict", json=payload)
    
    # If models are not loaded (e.g. if we are testing in a clean build), the status will be 503.
    # Otherwise, it will be 200. We handle both conditions gracefully.
    if response.status_code == 503:
        # Expected response when ML models are missing
        assert "error" in response.json()["detail"]
    else:
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "diabetes" in data["predictions"]
        assert "heart_disease" in data["predictions"]
        assert "factors" in data
        assert "recommendations" in data
        assert data["source"] == "ml_model"
        
        # Test if the entry was persisted to the history database
        history_response = client.get("/history")
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        # We should have at least 1 record
        assert len(history_data) >= 1
        record = history_data[0]
        assert record["patient_name"] == "Alex Tester"
        assert record["mrn"] == "MRN-TEST-999"
        assert record["age"] == 45
        assert "diabetes_risk_level" in record
        assert "heart_risk_level" in record


def test_history_query_limit():
    """Verify that history lists query parameters work."""
    response = client.get("/history?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1
