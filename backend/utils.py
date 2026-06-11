"""
HealthOracle AI — Feature Engineering & Recommendation Engine
Converts raw PatientPayload into ML feature vectors and generates clinical recommendations.
"""


import numpy as np

# ─────────────────────────────────────────────────────────────────
# POPULATION DEFAULTS  (used when optional lab fields are absent)
# Source: CDC / AHA average adult US population estimates
# ─────────────────────────────────────────────────────────────────
POPULATION_DEFAULTS = {
    "glucose":       99.0,    # mg/dL
    "hba1c":          5.6,    # %
    "cholesterol":  196.0,    # mg/dL
    "ldl":          116.0,    # mg/dL
    "hdl_male":      47.0,    # mg/dL
    "hdl_female":    57.0,    # mg/dL
    "triglycerides": 131.0,   # mg/dL
    "systolic":      119.0,   # mmHg
    "diastolic":      76.0,   # mmHg
}

SMOKING_MAP      = {"Never": 0, "Former": 1, "Current": 2}
ACTIVITY_MAP     = {"Low": 0, "Medium": 1, "High": 2}
ALCOHOL_MAP      = {"None": 0, "Moderate": 1, "Heavy": 2}
FAMILY_MAP       = {"None": 0, "One": 1, "Both": 2}
BP_CATEGORY_MAP  = {"Normal": 0, "Elevated": 1, "High1": 2, "High2": 3}


def _bp_from_categorical(bp_str: str) -> tuple[float, float]:
    """Converts legacy categorical BP string to (systolic, diastolic)."""
    if bp_str == "High2":   return (145.0, 92.0)
    if bp_str == "High1":   return (133.0, 83.0)
    if bp_str == "Elevated": return (124.0, 76.0)
    return (118.0, 75.0)  # Normal


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    h = height_cm / 100.0
    return round(weight_kg / (h * h), 1)


def engineer_features(payload) -> dict[str, np.ndarray]:
    """
    Converts PatientPayload into two feature vectors:
      - diabetes_features  (16 features)
      - heart_features     (18 features)

    Returns a dict with both arrays ready for model.predict_proba()
    """
    gender_val = 1 if payload.gender == "Male" else 0
    bmi = compute_bmi(payload.weight, payload.height)

    # ── Resolve optional lab values ──────────────────────────────
    hdl_default = POPULATION_DEFAULTS["hdl_male"] if payload.gender == "Male" \
                  else POPULATION_DEFAULTS["hdl_female"]

    glucose      = payload.glucose      if payload.glucose      is not None else POPULATION_DEFAULTS["glucose"]
    hba1c        = payload.hba1c        if payload.hba1c        is not None else POPULATION_DEFAULTS["hba1c"]
    cholesterol  = payload.cholesterol  if payload.cholesterol  is not None else POPULATION_DEFAULTS["cholesterol"]
    ldl          = payload.ldl          if payload.ldl          is not None else POPULATION_DEFAULTS["ldl"]
    hdl          = payload.hdl          if payload.hdl          is not None else hdl_default
    triglycerides= payload.triglycerides if payload.triglycerides is not None else POPULATION_DEFAULTS["triglycerides"]

    # Resolve blood pressure
    if payload.systolic is not None and payload.diastolic is not None:
        systolic  = payload.systolic
        diastolic = payload.diastolic
    elif payload.bp:
        systolic, diastolic = _bp_from_categorical(payload.bp)
    else:
        systolic  = POPULATION_DEFAULTS["systolic"]
        diastolic = POPULATION_DEFAULTS["diastolic"]

    # ── Symptom flags ────────────────────────────────────────────
    syms = payload.symptoms or []
    sym_polyuria      = 1 if "polyuria"      in syms else 0
    sym_polydipsia    = 1 if "polydipsia"    in syms else 0
    sym_fatigue       = 1 if "fatigue"       in syms else 0
    sym_blurred_vision= 1 if "blurred_vision" in syms else 0
    sym_numbness      = 1 if "numbness"      in syms else 0
    sym_chest_pain    = 1 if "chest_pain"    in syms else 0
    sym_dyspnea       = 1 if "dyspnea"       in syms else 0
    sym_dizziness     = 1 if "dizziness"     in syms else 0

    # ── Comorbidity flags ────────────────────────────────────────
    combs = payload.comorbidities or []
    has_hypertension  = 1 if "hypertension"  in combs else 0
    has_hyperlipidemia= 1 if "hyperlipidemia" in combs else 0
    has_obesity       = 1 if "obesity"        in combs else 0
    has_kidney        = 1 if "kidney_disease" in combs else 0

    # ── Encoded categoricals ─────────────────────────────────────
    smoking_enc  = SMOKING_MAP.get(payload.smoking, 0)
    activity_enc = ACTIVITY_MAP.get(payload.physicalActivity, 1)
    alcohol_enc  = ALCOHOL_MAP.get(payload.alcohol, 0)
    fam_db_enc   = FAMILY_MAP.get(payload.familyDiabetes, 0)
    fam_hd_enc   = FAMILY_MAP.get(payload.familyHeart, 0)

    # ────────────────────────────────────────────────────────────
    # DIABETES FEATURE VECTOR  (must match train.py column order)
    # ────────────────────────────────────────────────────────────
    diabetes_features = np.array([[
        payload.age,            # 0
        gender_val,             # 1
        bmi,                    # 2
        glucose,                # 3
        hba1c,                  # 4
        fam_db_enc,             # 5
        smoking_enc,            # 6
        activity_enc,           # 7
        payload.dietQuality,    # 8
        payload.stressLevel,    # 9
        payload.sleepHours,     # 10
        has_hypertension,       # 11
        has_obesity,            # 12
        sym_polyuria,           # 13
        sym_polydipsia,         # 14
        sym_numbness,           # 15
    ]], dtype=np.float64)

    # ────────────────────────────────────────────────────────────
    # HEART DISEASE FEATURE VECTOR  (must match train.py column order)
    # ────────────────────────────────────────────────────────────
    heart_features = np.array([[
        payload.age,            # 0
        gender_val,             # 1
        bmi,                    # 2
        systolic,               # 3
        diastolic,              # 4
        cholesterol,            # 5
        ldl,                    # 6
        hdl,                    # 7
        triglycerides,          # 8
        fam_hd_enc,             # 9
        smoking_enc,            # 10
        activity_enc,           # 11
        alcohol_enc,            # 12
        payload.stressLevel,    # 13
        payload.sleepHours,     # 14
        has_hypertension,       # 15
        has_hyperlipidemia,     # 16
        sym_chest_pain,         # 17
    ]], dtype=np.float64)

    return {
        "diabetes": diabetes_features,
        "heart":    heart_features,
        # Raw resolved values for factor/recommendation logic
        "_resolved": {
            "bmi": bmi, "glucose": glucose, "hba1c": hba1c,
            "systolic": systolic, "diastolic": diastolic,
            "cholesterol": cholesterol, "ldl": ldl, "hdl": hdl,
            "triglycerides": triglycerides,
        }
    }


# ─────────────────────────────────────────────────────────────────
# CONTRIBUTING FACTORS ENGINE
# Returns top-5 factors with name, weight, positive flag
# ─────────────────────────────────────────────────────────────────
def compute_contributing_factors(payload, resolved: dict, db_prob: int, hd_prob: int) -> list[dict]:
    factors = []
    bmi = resolved["bmi"]
    syms = payload.symptoms or []
    combs = payload.comorbidities or []

    # ── Diabetes factors ──
    if payload.familyDiabetes == "Both":
        factors.append({"name": "Genetics: High Family Diabetes Predisposition", "weight": 30, "positive": True})
    elif payload.familyDiabetes == "One":
        factors.append({"name": "Family History of Diabetes (1 Parent)", "weight": 15, "positive": True})

    if resolved["hba1c"] >= 6.5:
        factors.append({"name": f"Clinical HbA1c Lab Indicator ({resolved['hba1c']}%)", "weight": 42, "positive": True})
    elif resolved["hba1c"] >= 5.7:
        factors.append({"name": f"Elevated HbA1c ({resolved['hba1c']}%)", "weight": 22, "positive": True})

    if resolved["glucose"] >= 126:
        factors.append({"name": f"High Fasting Blood Glucose ({resolved['glucose']} mg/dL)", "weight": 36, "positive": True})
    elif resolved["glucose"] >= 100:
        factors.append({"name": f"Elevated Fasting Glucose ({resolved['glucose']} mg/dL)", "weight": 18, "positive": True})

    if bmi >= 30 or "obesity" in combs:
        factors.append({"name": "Comorbidity: Obesity Class (BMI ≥ 30)", "weight": 24, "positive": True})
    elif bmi >= 25:
        factors.append({"name": "Biometrics: Overweight BMI Range", "weight": 12, "positive": True})

    if "polyuria" in syms:
        factors.append({"name": "Symptom: Frequent Urination (Polyuria)", "weight": 18, "positive": True})
    if "polydipsia" in syms:
        factors.append({"name": "Symptom: Excessive Thirst (Polydipsia)", "weight": 18, "positive": True})
    if "numbness" in syms:
        factors.append({"name": "Symptom: Extremity Numbness (Neuropathy Sign)", "weight": 15, "positive": True})

    if payload.physicalActivity == "Low":
        factors.append({"name": "Physical: Sedentary Lifestyle Profile", "weight": 14, "positive": True})
    elif payload.physicalActivity == "High":
        factors.append({"name": "Exercise: Active Aerobic Defense", "weight": 8, "positive": False})

    if payload.dietQuality >= 8:
        factors.append({"name": "Nutrition: High Quality Whole-Food Diet", "weight": 7, "positive": False})
    elif payload.dietQuality <= 4:
        factors.append({"name": "Diet: Processed Sugars / Refined Carbs", "weight": 15, "positive": True})

    # ── Cardiovascular factors ──
    if payload.familyHeart == "Both":
        factors.append({"name": "Genetics: High Cardiovascular Predisposition", "weight": 26, "positive": True})
    elif payload.familyHeart == "One":
        factors.append({"name": "Family History of Cardiovascular Disease", "weight": 12, "positive": True})

    if "hypertension" in combs:
        factors.append({"name": "Comorbidity: Clinically Diagnosed Hypertension", "weight": 20, "positive": True})
    if "hyperlipidemia" in combs:
        factors.append({"name": "Comorbidity: Clinically Diagnosed Hyperlipidemia", "weight": 15, "positive": True})
    if "kidney_disease" in combs:
        factors.append({"name": "Comorbidity: Chronic Kidney Disease", "weight": 12, "positive": True})

    sys_bp = resolved["systolic"]
    dia_bp = resolved["diastolic"]
    if sys_bp >= 180 or dia_bp >= 120:
        factors.append({"name": f"Vitals: Hypertensive Crisis BP ({int(sys_bp)}/{int(dia_bp)})", "weight": 45, "positive": True})
    elif sys_bp >= 140 or dia_bp >= 90:
        factors.append({"name": f"Vitals: Stage 2 Hypertension BP ({int(sys_bp)}/{int(dia_bp)})", "weight": 30, "positive": True})
    elif sys_bp >= 130 or dia_bp >= 80:
        factors.append({"name": f"Vitals: Stage 1 Hypertension BP ({int(sys_bp)}/{int(dia_bp)})", "weight": 16, "positive": True})
    elif sys_bp < 120 and dia_bp < 80:
        factors.append({"name": f"Vitals: Healthy Blood Pressure ({int(sys_bp)}/{int(dia_bp)})", "weight": 6, "positive": False})

    if payload.smoking == "Current":
        factors.append({"name": "Habits: Active Tobacco Use Strain", "weight": 28, "positive": True})
    elif payload.smoking == "Former":
        factors.append({"name": "History: Former Tobacco Use", "weight": 10, "positive": True})

    if resolved["cholesterol"] >= 240:
        factors.append({"name": f"Clinical Hypercholesterolemia ({resolved['cholesterol']} mg/dL)", "weight": 22, "positive": True})
    elif resolved["cholesterol"] >= 200:
        factors.append({"name": f"Elevated Total Cholesterol ({resolved['cholesterol']} mg/dL)", "weight": 10, "positive": True})

    if resolved["ldl"] >= 160:
        factors.append({"name": f"High LDL Cholesterol ({resolved['ldl']} mg/dL)", "weight": 20, "positive": True})

    hdl_limit = 40 if payload.gender == "Male" else 50
    if resolved["hdl"] < hdl_limit:
        factors.append({"name": f"Cardioprotective Deficit: Low HDL ({resolved['hdl']} mg/dL)", "weight": 15, "positive": True})
    elif resolved["hdl"] >= 60:
        factors.append({"name": f"Active Cardioprotection: High HDL ({resolved['hdl']} mg/dL)", "weight": 8, "positive": False})

    if resolved["triglycerides"] >= 200:
        factors.append({"name": f"Elevated Triglycerides ({resolved['triglycerides']} mg/dL)", "weight": 12, "positive": True})

    if "chest_pain" in syms:
        factors.append({"name": "Symptom: Acute Chest Pain (Angina Marker)", "weight": 35, "positive": True})
    if "dyspnea" in syms:
        factors.append({"name": "Symptom: Shortness of Breath (Dyspnea)", "weight": 20, "positive": True})

    if payload.stressLevel > 6:
        factors.append({"name": "Stress: Elevated Psychological Index", "weight": (payload.stressLevel - 5) * 4, "positive": True})

    if payload.alcohol == "Heavy":
        factors.append({"name": "Alcohol: Heavy Consumption Workload", "weight": 12, "positive": True})
    if payload.sleepHours < 6:
        factors.append({"name": "Sleep Deprivation: < 6 Hours Average", "weight": 10, "positive": True})

    # Deduplicate by name, sort by weight descending, return top 5
    seen = set()
    unique = []
    for f in sorted(factors, key=lambda x: x["weight"], reverse=True):
        if f["name"] not in seen:
            seen.add(f["name"])
            unique.append(f)

    return unique[:5]


# ─────────────────────────────────────────────────────────────────
# CLINICAL RECOMMENDATIONS ENGINE
# ─────────────────────────────────────────────────────────────────
def generate_recommendations(payload, resolved: dict, db_risk: str, hd_risk: str) -> list[str]:
    recs = []
    syms = payload.symptoms or []
    combs = payload.comorbidities or []
    bmi = resolved["bmi"]

    # Urgent flags first
    if "chest_pain" in syms:
        recs.append("🚨 Urgent: Report any chest tightness radiating to the arm or jaw to emergency clinical personnel immediately.")
    if resolved["hba1c"] >= 6.5 or resolved["glucose"] >= 126:
        recs.append("Schedule an urgent endocrinology consultation — lab markers indicate possible diabetes diagnosis requiring treatment.")
    if resolved["systolic"] >= 180 or resolved["diastolic"] >= 120:
        recs.append("🚨 Hypertensive crisis detected. Seek emergency medical care immediately.")

    # Disease-specific
    if db_risk == "High":
        recs.append("Begin structured glucose monitoring (morning fasting readings). Consult a certified diabetes educator for a personalized management plan.")
    elif db_risk == "Medium" or resolved["hba1c"] >= 5.7 or resolved["glucose"] >= 100:
        recs.append("Schedule a laboratory HbA1c review with a primary care physician to verify glycemic status and rule out prediabetes.")

    if hd_risk == "High":
        recs.append("Cardiology referral advised: request a lipid panel, ECG, and echocardiogram to assess cardiac function.")
    elif hd_risk == "Medium":
        recs.append("Monitor cardiovascular markers: schedule a follow-up lipid panel and blood pressure checks every 3 months.")

    # Lifestyle interventions
    if payload.smoking == "Current":
        recs.append("Access tobacco cessation counseling. Halting nicotine cuts coronary event odds by 50% within 12 months.")

    if bmi >= 25:
        recs.append("Pursue an energy-deficit whole food plan targeting 5–10% bodyweight reduction. Even modest weight loss significantly lowers diabetes and cardiovascular risk.")

    if payload.physicalActivity == "Low":
        recs.append("Introduce 30 minutes of low-impact cardiovascular training (brisk walking, swimming) 5 times per week to improve insulin sensitivity and cardiac output.")

    if payload.stressLevel > 6:
        recs.append("Integrate mindfulness-based stress reduction (MBSR) protocols, progressive muscle relaxation, or structured breathing techniques to lower cortisol levels.")

    if payload.sleepHours < 6.5:
        recs.append("Develop a consistent sleep routine targeting 7–8 hours of restorative circadian sleep; poor sleep is independently linked to glucose dysregulation.")

    if resolved["cholesterol"] >= 200 or resolved["ldl"] >= 130:
        recs.append("Reduce dietary saturated/trans-fats; incorporate daily soluble fiber (oat bran, legumes) and omega-3 fatty acids (wild fish, flaxseeds, walnuts).")

    if resolved["systolic"] >= 130:
        recs.append("Limit sodium intake below 1,500 mg daily and track blood pressure twice weekly using a home monitor.")

    if payload.alcohol == "Heavy":
        recs.append("Reduce alcohol to ≤ 2 standard drinks/day (men) or ≤ 1 (women). Heavy intake elevates triglycerides and blood pressure.")

    if payload.dietQuality <= 4:
        recs.append("Shift from ultra-processed foods to a Mediterranean-pattern diet rich in vegetables, legumes, whole grains, and olive oil.")

    # Positive reinforcement fallbacks
    if len(recs) < 2:
        recs.append("Maintain your positive lifestyle and schedule a yearly routine medical checkup to track metabolic and cardiovascular health indicators.")
        recs.append("Support arterial flexibility by consuming healthy omega-3 fatty acids (flaxseeds, walnuts, wild-caught fish) 3× per week.")

    return recs[:8]  # Cap at 8 recommendations
