import urllib.request, json

payload = json.dumps({
    "patientName": "Test Patient", "mrn": "MRN-TEST-001",
    "age": 52, "gender": "Male", "height": 175, "weight": 90,
    "systolic": 138, "diastolic": 88, "glucose": 115, "hba1c": 6.1,
    "cholesterol": 225, "ldl": 148, "hdl": 38, "triglycerides": 195,
    "sleepHours": 5.5, "dietQuality": 4, "stressLevel": 8,
    "smoking": "Former", "physicalActivity": "Low", "alcohol": "Moderate",
    "familyDiabetes": "One", "familyHeart": "None",
    "symptoms": ["fatigue", "polyuria"],
    "comorbidities": ["hypertension"]
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8000/predict",
    data=payload,
    headers={"Content-Type": "application/json"}
)
r = urllib.request.urlopen(req)
data = json.loads(r.read())

db = data["predictions"]["diabetes"]
hd = data["predictions"]["heart_disease"]

print("=== DIABETES PREDICTION ===")
print("  Risk Level :", db["risk_level"])
print("  Probability:", str(db["probability"]) + "%")
print("  Confidence :", str(db["confidence"]) + "%")
print("=== HEART PREDICTION ===")
print("  Risk Level :", hd["risk_level"])
print("  Probability:", str(hd["probability"]) + "%")
print("  Confidence :", str(hd["confidence"]) + "%")
print("=== TOP RISK FACTORS ===")
for f in data["factors"][:3]:
    sign = "+" if f["positive"] else "-"
    print("  [" + sign + "] " + f["name"] + " (" + str(f["weight"]) + "%)")
print("=== SOURCE ===", data["source"])
print("=== RECOMMENDATIONS (first 2) ===")
for r in data["recommendations"][:2]:
    print(" -", r)
