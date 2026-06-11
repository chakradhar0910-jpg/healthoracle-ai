from backend.ocr import (
    extract_vitals_from_report,
    generate_mock_report_data,
    parse_vitals_from_text,
)


def test_parse_vitals_from_text():
    """Verify that regex parser identifies clinical markers in text block reports."""
    sample_report_text = """
    Clinical Lab Report
    Patient Name: John Smith
    Fasting Glucose: 112 mg/dL
    HbA1c Level: 6.2 %
    Blood Pressure (BP): 135/88 mmHg
    Total Cholesterol: 224 mg/dL
    LDL-C: 142 mg/dL
    HDL: 45 mg/dL
    Triglycerides: 185 mg/dL
    """

    vitals = parse_vitals_from_text(sample_report_text)

    assert vitals["glucose"] == 112.0
    assert vitals["hba1c"] == 6.2
    assert vitals["systolic"] == 135.0
    assert vitals["diastolic"] == 88.0
    assert vitals["cholesterol"] == 224.0
    assert vitals["ldl"] == 142.0
    assert vitals["hdl"] == 45.0
    assert vitals["triglycerides"] == 185.0


def test_parse_vitals_partial():
    """Verify regex parses sparse text reports containing only a few indicators."""
    sample_text = "Fasting sugar is 134, a1c is 7.1. Blood pressure is 150 / 95"
    vitals = parse_vitals_from_text(sample_text)

    assert vitals["glucose"] == 134.0
    assert vitals["hba1c"] == 7.1
    assert vitals["systolic"] == 150.0
    assert vitals["diastolic"] == 95.0
    assert "cholesterol" not in vitals


def test_generate_mock_report_data():
    """Verify mock report generators respond based on keyword rules in filename."""
    diabetic_data = generate_mock_report_data("diabetic_screening_lab.jpg")
    assert diabetic_data["glucose"] == 168.0
    assert diabetic_data["hba1c"] == 7.6

    cardio_data = generate_mock_report_data("cardio_lipid_panel.png")
    assert cardio_data["cholesterol"] == 265.0
    assert cardio_data["ldl"] == 178.0

    normal_data = generate_mock_report_data("generic_report.jpg")
    assert normal_data["glucose"] == 95.0
    assert normal_data["hba1c"] == 5.4


def test_extract_vitals_from_report_fallback():
    """Verify that extract_vitals_from_report completes successfully."""
    # Test file upload processing
    dummy_bytes = b"fake image bytes"
    vitals = extract_vitals_from_report(dummy_bytes, "diabetic_test.jpg")

    assert vitals is not None
    assert vitals["glucose"] == 168.0
    assert vitals["hba1c"] == 7.6
