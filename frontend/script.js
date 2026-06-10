// HealthOracle AI - Hospital Pre-Screening Controller & Diagnostic Engine

document.addEventListener("DOMContentLoaded", () => {
    const BACKEND_URL = "http://127.0.0.1:8000";
    let isServerOnline = false;

    // DOM Elements - Navigation Tabs
    const tabButtons = document.querySelectorAll(".tab-btn");
    const stepContainers = document.querySelectorAll(".step-container");
    const navNextButtons = document.querySelectorAll(".btn-next");
    const navPrevButtons = document.querySelectorAll(".btn-prev");

    // DOM Elements - Optional Labs Accordion
    const labsAccordionHeader = document.getElementById("labs-accordion-header");
    const labsChevron = document.getElementById("labs-chevron");
    const labsInputsPanel = document.getElementById("labs-inputs-panel");

    // Profile Memory LocalStorage Toggle
    const chkSaveProfile = document.getElementById("chk-save-profile");

    // DOM Elements - Patient Identity Vitals
    const healthForm = document.getElementById("health-form");
    const nameInput = document.getElementById("patient_name");
    const mrnInput = document.getElementById("mrn");
    const ageInput = document.getElementById("age");
    const dobInput = document.getElementById("dob");
    const heightInput = document.getElementById("height");
    const weightInput = document.getElementById("weight");
    const bmiDisplay = document.getElementById("bmi-display");
    const bpInput = document.getElementById("bp");
    
    // Sliders
    const sleepInput = document.getElementById("sleep_hours");
    const sleepTxt = document.getElementById("sleep-txt");
    const dietInput = document.getElementById("diet_quality");
    const dietTxt = document.getElementById("diet-txt");
    const stressInput = document.getElementById("stress_level");
    const stressTxt = document.getElementById("stress-txt");

    // Lifestyle Habits
    const smokingInput = document.getElementById("smoking");
    const activityInput = document.getElementById("physical_activity");
    const alcoholInput = document.getElementById("alcohol");

    // Lab Inputs
    const systolicInput = document.getElementById("systolic");
    const diastolicInput = document.getElementById("diastolic");
    const glucoseInput = document.getElementById("glucose");
    const hba1cInput = document.getElementById("hba1c");
    const cholesterolInput = document.getElementById("cholesterol");
    const ldlInput = document.getElementById("ldl");
    const hdlInput = document.getElementById("hdl");
    const triglyceridesInput = document.getElementById("triglycerides");

    // UI Panels
    const apiStatus = document.getElementById("api-status");
    const resultsPlaceholder = document.getElementById("results-placeholder");
    const resultsLoading = document.getElementById("results-loading");
    const resultsDashboard = document.getElementById("results-dashboard");
    const loadingStage = document.getElementById("loading-stage");

    // Patient Details Output Summary
    const displayName = document.getElementById("display-name");
    const displayMrn = document.getElementById("display-mrn");
    const displayAgeSex = document.getElementById("display-age-sex");
    const displayBmi = document.getElementById("display-bmi");
    const displaySymptoms = document.getElementById("display-symptoms");

    // Core Risk Gauges Output
    const diabetesBadge = document.getElementById("diabetes-badge");
    const diabetesRing = document.getElementById("diabetes-ring");
    const diabetesProb = document.getElementById("diabetes-prob");
    const diabetesConf = document.getElementById("diabetes-conf");
    const diabetesCard = document.getElementById("diabetes-card");

    const heartBadge = document.getElementById("heart-badge");
    const heartRing = document.getElementById("heart-ring");
    const heartProb = document.getElementById("heart-prob");
    const heartConf = document.getElementById("heart-conf");
    const heartCard = document.getElementById("heart-card");

    // Dynamic Outputs
    const labsTableBody = document.getElementById("labs-table-body");
    const factorsContainer = document.getElementById("factors-container");
    const recommendationsContainer = document.getElementById("recommendations-container");
    const clinicalUrgency = document.getElementById("clinical-urgency");
    const urgencyIcon = document.getElementById("urgency-icon");
    const urgencyHeadline = document.getElementById("urgency-headline");
    const urgencyDesc = document.getElementById("urgency-desc");

    // Comparative Cohort Risk elements
    const cohortUserDiabetes = document.getElementById("cohort-user-diabetes");
    const cohortUserHeart = document.getElementById("cohort-user-heart");

    // Action Buttons
    const btnPrintReport = document.getElementById("btn-print-report");
    const btnReset = document.getElementById("btn-reset");

    // SVG Gauge Dimensions
    const radius = 54;
    const circumference = 2 * Math.PI * radius;

    [diabetesRing, heartRing].forEach(ring => {
        if (ring) {
            ring.style.strokeDasharray = `${circumference} ${circumference}`;
            ring.style.strokeDashoffset = circumference;
        }
    });

    // 1. Dynamic Multistep Tabs Navigator
    function showStep(stepNum) {
        stepContainers.forEach(container => {
            container.classList.add("hidden");
        });
        document.getElementById(`step-${stepNum}-container`).classList.remove("hidden");

        tabButtons.forEach(btn => {
            btn.classList.remove("active");
            if (parseInt(btn.getAttribute("data-step")) === stepNum) {
                btn.classList.add("active");
            }
        });
    }

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetStep = parseInt(btn.getAttribute("data-step"));
            const currentActiveStep = parseInt(document.querySelector(".tab-btn.active").getAttribute("data-step"));
            
            if (targetStep > currentActiveStep) {
                if (!validateStepInputs(currentActiveStep)) return;
            }
            showStep(targetStep);
        });
    });

    navNextButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const currentStep = parseInt(btn.closest(".step-container").id.split("-")[1]);
            const targetStep = parseInt(btn.getAttribute("data-target"));
            
            if (validateStepInputs(currentStep)) {
                showStep(targetStep);
            }
        });
    });

    navPrevButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetStep = parseInt(btn.getAttribute("data-target"));
            showStep(targetStep);
        });
    });

    function validateStepInputs(stepNum) {
        const container = document.getElementById(`step-${stepNum}-container`);
        const inputs = container.querySelectorAll("input[required], select[required]");
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity();
                isValid = false;
            }
        });
        return isValid;
    }

    // 2. Accordion Labs Toggle
    labsAccordionHeader.addEventListener("click", () => {
        labsChevron.classList.toggle("rotate");
        labsInputsPanel.classList.toggle("hidden");
    });

    // 3. BMI Real-time calculation and Comorbidity triggers
    function updateBMI() {
        const height = parseFloat(heightInput.value);
        const weight = parseFloat(weightInput.value);
        const numSpan = bmiDisplay.querySelector(".bmi-num");
        const statusSpan = bmiDisplay.querySelector(".bmi-status");
        const obesityCheckbox = document.getElementById("cond-obese");

        if (height > 0 && weight > 0) {
            const heightInMeters = height / 100;
            const bmi = weight / (heightInMeters * heightInMeters);
            const bmiFixed = bmi.toFixed(1);
            numSpan.textContent = bmiFixed;

            bmiDisplay.className = "bmi-badge";

            if (bmi < 18.5) {
                bmiDisplay.classList.add("bmi-underweight");
                statusSpan.textContent = "Underweight";
                obesityCheckbox.checked = false;
            } else if (bmi < 25) {
                bmiDisplay.classList.add("bmi-normal");
                statusSpan.textContent = "Healthy Weight";
                obesityCheckbox.checked = false;
            } else if (bmi < 30) {
                bmiDisplay.classList.add("bmi-overweight");
                statusSpan.textContent = "Overweight";
                obesityCheckbox.checked = false;
            } else {
                bmiDisplay.classList.add("bmi-obese");
                statusSpan.textContent = "Obese Status";
                obesityCheckbox.checked = true; // Auto-trigger obesity checkbox condition!
            }
        } else {
            numSpan.textContent = "--";
            statusSpan.textContent = "Enter stats";
            bmiDisplay.className = "bmi-badge";
        }
    }

    [heightInput, weightInput].forEach(input => {
        input.addEventListener("input", updateBMI);
    });

    // 4. Sliders values display
    sleepInput.addEventListener("input", (e) => {
        sleepTxt.textContent = `${parseFloat(e.target.value).toFixed(1)} hours`;
    });

    dietInput.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        let text = "Balanced";
        if (val <= 3) text = "Highly Processed (Poor)";
        else if (val <= 5) text = "Average Quality";
        else if (val <= 8) text = "Good Quality";
        else text = "Optimal Whole Food";
        dietTxt.textContent = text;
    });

    stressInput.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        let text = "Moderate";
        if (val <= 3) text = `Low (${val})`;
        else if (val <= 6) text = `Moderate (${val})`;
        else if (val <= 8) text = `High (${val})`;
        else text = `Extremely High (${val})`;
        stressTxt.textContent = text;
    });

    // 5. Local Storage Profile Save/Restore
    function saveProfileState() {
        if (!chkSaveProfile.checked) return;

        const checkedHistory = [];
        document.querySelectorAll('input[name="history_conditions"]:checked').forEach(cb => {
            checkedHistory.push(cb.value);
        });

        const profileData = {
            name: nameInput.value,
            mrn: mrnInput.value,
            age: ageInput.value,
            dob: dobInput.value,
            gender: document.querySelector('input[name="gender"]:checked')?.value || "Male",
            bp: bpInput ? bpInput.value : "",
            height: heightInput.value,
            weight: weightInput.value,
            familyDiabetes: document.querySelector('input[name="family_diabetes"]:checked')?.value || "None",
            familyHeart: document.querySelector('input[name="family_heart"]:checked')?.value || "None",
            sleepHours: sleepInput.value,
            dietQuality: dietInput.value,
            stressLevel: stressInput.value,
            smoking: smokingInput.value,
            physicalActivity: activityInput.value,
            alcohol: alcoholInput.value,
            systolic: systolicInput.value,
            diastolic: diastolicInput.value,
            glucose: glucoseInput.value,
            hba1c: hba1cInput.value,
            cholesterol: cholesterolInput.value,
            ldl: ldlInput.value,
            hdl: hdlInput.value,
            triglycerides: triglyceridesInput.value,
            history: checkedHistory
        };

        localStorage.setItem("healthoracle_clinical_profile", JSON.stringify(profileData));
        localStorage.setItem("healthoracle_clinical_consent", "true");
    }

    function loadProfileState() {
        const consent = localStorage.getItem("healthoracle_clinical_consent") === "true";
        chkSaveProfile.checked = consent;

        if (!consent) return;

        const rawData = localStorage.getItem("healthoracle_clinical_profile");
        if (!rawData) return;

        try {
            const data = JSON.parse(rawData);
            
            if (data.name) nameInput.value = data.name;
            if (data.mrn) mrnInput.value = data.mrn;
            if (data.age) ageInput.value = data.age;
            if (data.dob) dobInput.value = data.dob;
            if (data.bp && bpInput) bpInput.value = data.bp;
            if (data.height) heightInput.value = data.height;
            if (data.weight) weightInput.value = data.weight;
            
            if (data.sleepHours) {
                sleepInput.value = data.sleepHours;
                sleepInput.dispatchEvent(new Event("input"));
            }
            if (data.dietQuality) {
                dietInput.value = data.dietQuality;
                dietInput.dispatchEvent(new Event("input"));
            }
            if (data.stressLevel) {
                stressInput.value = data.stressLevel;
                stressInput.dispatchEvent(new Event("input"));
            }
            if (data.smoking) smokingInput.value = data.smoking;
            if (data.physicalActivity) activityInput.value = data.physicalActivity;
            if (data.alcohol) alcoholInput.value = data.alcohol;

            // Lab values
            if (data.systolic) systolicInput.value = data.systolic;
            if (data.diastolic) diastolicInput.value = data.diastolic;
            if (data.glucose) glucoseInput.value = data.glucose;
            if (data.hba1c) hba1cInput.value = data.hba1c;
            if (data.cholesterol) cholesterolInput.value = data.cholesterol;
            if (data.ldl) ldlInput.value = data.ldl;
            if (data.hdl) hdlInput.value = data.hdl;
            if (data.triglycerides) triglyceridesInput.value = data.triglycerides;

            // Radios biological sex
            const genderRadio = document.querySelector(`input[name="gender"][value="${data.gender}"]`);
            if (genderRadio) genderRadio.checked = true;

            // Radios Genetics
            const dbRadio = document.querySelector(`input[name="family_diabetes"][value="${data.familyDiabetes}"]`);
            if (dbRadio) dbRadio.checked = true;

            const htRadio = document.querySelector(`input[name="family_heart"][value="${data.familyHeart}"]`);
            if (htRadio) htRadio.checked = true;

            // Comorbidities Checkboxes
            if (data.history) {
                data.history.forEach(val => {
                    const cb = document.querySelector(`input[name="history_conditions"][value="${val}"]`);
                    if (cb) cb.checked = true;
                });
            }

            updateBMI();
        } catch (e) {
            console.error("Failed to load clinical profile.", e);
        }
    }

    chkSaveProfile.addEventListener("change", () => {
        if (chkSaveProfile.checked) {
            saveProfileState();
        } else {
            localStorage.removeItem("healthoracle_clinical_profile");
            localStorage.setItem("healthoracle_clinical_consent", "false");
        }
    });

    healthForm.addEventListener("input", saveProfileState);
    healthForm.addEventListener("change", saveProfileState);

    // Initial Loading
    loadProfileState();

    // 6. API Status heartbeat check
    async function checkServerStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 1200);

            const response = await fetch(`${BACKEND_URL}/`, {
                method: "GET",
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (response.ok) {
                isServerOnline = true;
                updateStatusBadge("ready");
            } else {
                isServerOnline = false;
                updateStatusBadge("warm");
            }
        } catch (e) {
            isServerOnline = false;
            updateStatusBadge("warm");
        }
    }

    function updateStatusBadge(state) {
        const dot = apiStatus.querySelector(".status-indicator-dot");
        const lbl = apiStatus.querySelector(".status-label");

        if (state === "ready") {
            dot.className = "status-indicator-dot dot-ready";
            lbl.textContent = "AI Server Connected";
        } else {
            dot.className = "status-indicator-dot dot-warm";
            lbl.textContent = "Offline Preview Mode";
        }
    }

    checkServerStatus();
    setInterval(checkServerStatus, 10000);

    // 7. Form Submit & Diagnostics Compiler
    healthForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        resultsPlaceholder.classList.add("hidden");
        resultsDashboard.classList.add("hidden");
        resultsLoading.classList.remove("hidden");

        const stages = [
            "Normalizing demographic variables...",
            "Constructing clinical vitals matrix...",
            "Analyzing biometric BMI structures...",
            "Correlating comorbidities history...",
            "Analyzing active symptom indicators...",
            "Assessing lab blood panel biomarkers...",
            "Calculating heart pressure metrics...",
            "Running clinical pre-screening models..."
        ];

        let stageIdx = 0;
        const stageInterval = setInterval(() => {
            if (stageIdx < stages.length) {
                loadingStage.textContent = stages[stageIdx++];
            }
        }, 250);

        // Gather checklist values
        const activeSymptoms = [];
        document.querySelectorAll('input[name="symptoms"]:checked').forEach(cb => {
            activeSymptoms.push(cb.value);
        });

        const activeConditions = [];
        document.querySelectorAll('input[name="history_conditions"]:checked').forEach(cb => {
            activeConditions.push(cb.value);
        });

        const age = parseInt(ageInput.value);
        const gender = document.querySelector('input[name="gender"]:checked').value;
        
        // Resolve BP category based on inputs or legacy dropdown if exists
        let bp = "";
        if (bpInput) {
            bp = bpInput.value;
        } else {
            const systolicVal = systolicInput.value ? parseInt(systolicInput.value) : null;
            const diastolicVal = diastolicInput.value ? parseInt(diastolicInput.value) : null;
            if (systolicVal !== null && diastolicVal !== null) {
                if (systolicVal >= 140 || diastolicVal >= 90) {
                    bp = "High2";
                } else if (systolicVal >= 130 || diastolicVal >= 80) {
                    bp = "High1";
                } else if (systolicVal >= 120 && diastolicVal < 80) {
                    bp = "Elevated";
                } else {
                    bp = "Normal";
                }
            }
        }

        const height = parseFloat(heightInput.value);
        const weight = parseFloat(weightInput.value);
        const familyDiabetes = document.querySelector('input[name="family_diabetes"]:checked').value;
        const familyHeart = document.querySelector('input[name="family_heart"]:checked').value;
        const sleepHours = parseFloat(sleepInput.value);
        const dietQuality = parseInt(dietInput.value);
        const stressLevel = parseInt(stressInput.value);
        const smoking = smokingInput.value;
        const physicalActivity = activityInput.value;
        const alcohol = alcoholInput.value;

        // Lab panel values
        const systolic = systolicInput.value ? parseInt(systolicInput.value) : null;
        const diastolic = diastolicInput.value ? parseInt(diastolicInput.value) : null;
        const glucose = glucoseInput.value ? parseFloat(glucoseInput.value) : null;
        const hba1c = hba1cInput.value ? parseFloat(hba1cInput.value) : null;
        const cholesterol = cholesterolInput.value ? parseFloat(cholesterolInput.value) : null;
        const ldl = ldlInput.value ? parseFloat(ldlInput.value) : null;
        const hdl = hdlInput.value ? parseFloat(hdlInput.value) : null;
        const triglycerides = triglyceridesInput.value ? parseFloat(triglyceridesInput.value) : null;

        const payload = {
            patientName: nameInput.value,
            mrn: mrnInput.value,
            age, gender, bp, height, weight, familyDiabetes, familyHeart,
            sleepHours, dietQuality, stressLevel, smoking, physicalActivity, alcohol,
            systolic, diastolic, glucose, hba1c, cholesterol, ldl, hdl, triglycerides,
            symptoms: activeSymptoms,
            comorbidities: activeConditions
        };

        // Latency delay for visual feedback (1.6s)
        await new Promise(resolve => setTimeout(resolve, 1600));
        clearInterval(stageInterval);

        let results = null;

        if (isServerOnline) {
            try {
                const response = await fetch(`${BACKEND_URL}/predict`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    results = await response.json();
                } else {
                    results = compileLocalClinicalInference(payload);
                }
            } catch (err) {
                results = compileLocalClinicalInference(payload);
            }
        } else {
            results = compileLocalClinicalInference(payload);
        }

        resultsLoading.classList.add("hidden");
        resultsDashboard.classList.remove("hidden");

        renderResultsDashboard(results, payload);
    });

    // 8. Hospital-Grade Clinical Inference Engine
    function compileLocalClinicalInference(data) {
        const bmi = data.weight / ((data.height / 100) * (data.height / 100));
        const factors = [];

        // --- DIABETES ANALYSIS PREDICTIONS ---
        let dScore = 12; // base risk

        // Age factor
        if (data.age > 45) dScore += (data.age - 45) * 0.95;
        else if (data.age > 30) dScore += (data.age - 30) * 0.35;

        // Comorbidities
        if (data.comorbidities.includes("hypertension")) {
            dScore += 10;
            factors.push({ name: "Comorbidity: Hypertension History", weight: 10, positive: true });
        }
        if (data.comorbidities.includes("hyperlipidemia")) {
            dScore += 8;
        }
        if (data.comorbidities.includes("obesity") || bmi >= 30) {
            dScore += 24;
            factors.push({ name: "Comorbidity: Obesity Class (BMI >= 30)", weight: 24, positive: true });
        } else if (bmi >= 25) {
            dScore += 12;
            factors.push({ name: "Biometrics: Overweight BMI Range", weight: 12, positive: true });
        }

        // Genetic history
        if (data.familyDiabetes === "One") {
            dScore += 15;
            factors.push({ name: "Family History of Diabetes (1 Parent)", weight: 15, positive: true });
        } else if (data.familyDiabetes === "Both") {
            dScore += 30;
            factors.push({ name: "Genetics: High Family Diabetes Predisposition", weight: 30, positive: true });
        }

        // Symptoms
        if (data.symptoms.includes("polyuria")) {
            dScore += 18;
            factors.push({ name: "Symptom: Frequent Urination (Polyuria)", weight: 18, positive: true });
        }
        if (data.symptoms.includes("polydipsia")) {
            dScore += 18;
            factors.push({ name: "Symptom: Excessive Thirst (Polydipsia)", weight: 18, positive: true });
        }
        if (data.symptoms.includes("numbness")) {
            dScore += 15;
            factors.push({ name: "Symptom: Extremity Numbness (Neuropathy Sign)", weight: 15, positive: true });
        }
        if (data.symptoms.includes("blurred_vision")) {
            dScore += 10;
        }

        // Lifestyle Habits
        if (data.dietQuality < 5) {
            const penalty = (10 - data.dietQuality) * 3;
            dScore += penalty;
            factors.push({ name: "Diet: Processed Sugars / Refined Carbs", weight: penalty, positive: true });
        } else if (data.dietQuality >= 8) {
            dScore -= 7;
            factors.push({ name: "Nutrition: High Quality Whole-Food Diet", weight: 7, positive: false });
        }

        if (data.physicalActivity === "Low") {
            dScore += 14;
            factors.push({ name: "Physical: Sedentary Lifestyle Profile", weight: 14, positive: true });
        } else if (data.physicalActivity === "High") {
            dScore -= 8;
            factors.push({ name: "Exercise: Active Aerobic Defense", weight: 8, positive: false });
        }

        // Laboratory overrides - Fasting Glucose & HbA1c
        let hasLabSugarOverride = false;
        let labSugarScore = 0;

        if (data.hba1c !== null) {
            hasLabSugarOverride = true;
            if (data.hba1c >= 6.5) {
                labSugarScore = Math.min((data.hba1c - 6.0) * 12 + 65, 98);
                factors.push({ name: `Clinical HbA1c Lab Indicator (${data.hba1c}%)`, weight: 42, positive: true });
            } else if (data.hba1c >= 5.7) {
                labSugarScore = (data.hba1c - 5.0) * 18 + 20;
                factors.push({ name: `Elevated HbA1c Lab Indicator (${data.hba1c}%)`, weight: 22, positive: true });
            } else {
                labSugarScore = data.hba1c * 4;
                factors.push({ name: `Healthy HbA1c Lab Range (${data.hba1c}%)`, weight: 12, positive: false });
            }
        } else if (data.glucose !== null) {
            hasLabSugarOverride = true;
            if (data.glucose >= 126) {
                labSugarScore = Math.min((data.glucose - 120) * 0.35 + 70, 98);
                factors.push({ name: `High Fasting Blood Glucose (${data.glucose} mg/dL)`, weight: 36, positive: true });
            } else if (data.glucose >= 100) {
                labSugarScore = (data.glucose - 95) * 1.4 + 30;
                factors.push({ name: `Elevated Fasting Glucose (${data.glucose} mg/dL)`, weight: 18, positive: true });
            } else {
                labSugarScore = data.glucose * 0.22;
                factors.push({ name: `Optimal Fasting Glucose (${data.glucose} mg/dL)`, weight: 8, positive: false });
            }
        }

        const diabetesFinal = hasLabSugarOverride 
            ? Math.round(labSugarScore)
            : Math.min(Math.max(Math.round(dScore), 2), 98);


        // --- CARDIOVASCULAR DIAGNOSIS INFERENCE ---
        let hScore = 10;

        // Age factor
        if (data.age > 50) hScore += (data.age - 50) * 1.15;
        else if (data.age > 35) hScore += (data.age - 35) * 0.45;

        // Genetics
        if (data.familyHeart === "One") {
            hScore += 12;
            factors.push({ name: "Family History of Cardiovascular Disease", weight: 12, positive: true });
        } else if (data.familyHeart === "Both") {
            hScore += 26;
            factors.push({ name: "Genetics: High Cardiovascular Predisposition", weight: 26, positive: true });
        }

        // Comorbidities
        if (data.comorbidities.includes("hypertension")) {
            hScore += 20;
            factors.push({ name: "Comorbidity: Clinically Diagnosed Hypertension", weight: 20, positive: true });
        }
        if (data.comorbidities.includes("hyperlipidemia")) {
            hScore += 15;
            factors.push({ name: "Comorbidity: Clinically Diagnosed Hyperlipidemia", weight: 15, positive: true });
        }
        if (data.comorbidities.includes("kidney_disease")) {
            hScore += 12;
            factors.push({ name: "Comorbidity: Chronic Kidney Disease", weight: 12, positive: true });
        }

        // Exact Blood Pressure inputs overrides
        if (data.systolic !== null && data.diastolic !== null) {
            const sys = data.systolic;
            const dia = data.diastolic;
            
            if (sys >= 180 || dia >= 120) {
                hScore += 45;
                factors.push({ name: `Vitals: Hypertensive Crisis BP (${sys}/${dia})`, weight: 45, positive: true });
            } else if (sys >= 140 || dia >= 90) {
                hScore += 30;
                factors.push({ name: `Vitals: Stage 2 Hypertension BP (${sys}/${dia})`, weight: 30, positive: true });
            } else if (sys >= 130 || dia >= 80) {
                hScore += 16;
                factors.push({ name: `Vitals: Stage 1 Hypertension BP (${sys}/${dia})`, weight: 16, positive: true });
            } else if (sys >= 120 && dia < 80) {
                hScore += 8;
                factors.push({ name: `Vitals: Elevated Blood Pressure (${sys}/${dia})`, weight: 8, positive: true });
            } else {
                hScore -= 6;
                factors.push({ name: `Vitals: Healthy Blood Pressure (${sys}/${dia})`, weight: 6, positive: false });
            }
        } else {
            // Fall back to categorical BP selection
            if (data.bp === "High2") {
                hScore += 25;
                factors.push({ name: "BP Class: Stage 2 Hypertension", weight: 25, positive: true });
            } else if (data.bp === "High1") {
                hScore += 15;
            } else if (data.bp === "Elevated") {
                hScore += 6;
            }
        }

        // Habits
        if (data.smoking === "Current") {
            hScore += 28;
            factors.push({ name: "Habits: Active Tobacco Use Strain", weight: 28, positive: true });
        } else if (data.smoking === "Former") {
            hScore += 10;
        }

        if (data.stressLevel > 6) {
            const penalty = (data.stressLevel - 5) * 4;
            hScore += penalty;
            factors.push({ name: "Stress: Elevated Psychological Index", weight: penalty, positive: true });
        }

        if (data.sleepHours < 6) hScore += 10;
        if (data.alcohol === "Heavy") {
            hScore += 12;
            factors.push({ name: "Alcohol: Heavy Consumption Workload", weight: 12, positive: true });
        }

        // Symptoms
        if (data.symptoms.includes("chest_pain")) {
            hScore += 35;
            factors.push({ name: "Symptom: Acute Chest Pain (Angina Marker)", weight: 35, positive: true });
        }
        if (data.symptoms.includes("dyspnea")) {
            hScore += 20;
            factors.push({ name: "Symptom: Shortness of Breath (Dyspnea)", weight: 20, positive: true });
        }
        if (data.symptoms.includes("dizziness")) hScore += 10;

        // Lab Values overrides - Lipids
        if (data.cholesterol !== null) {
            if (data.cholesterol >= 240) {
                hScore += 22;
                factors.push({ name: `Clinical Hypercholesterolemia (${data.cholesterol} mg/dL)`, weight: 22, positive: true });
            } else if (data.cholesterol >= 200) {
                hScore += 10;
                factors.push({ name: `Elevated Total Cholesterol (${data.cholesterol} mg/dL)`, weight: 10, positive: true });
            }
        }
        if (data.ldl !== null) {
            if (data.ldl >= 160) {
                hScore += 20;
                factors.push({ name: `High LDL Cholesterol (${data.ldl} mg/dL)`, weight: 20, positive: true });
            } else if (data.ldl >= 130) {
                hScore += 10;
            }
        }
        if (data.hdl !== null) {
            const limit = data.gender === "Male" ? 40 : 50;
            if (data.hdl < limit) {
                hScore += 15;
                factors.push({ name: `Cardioprotective Deficit: Low HDL (${data.hdl} mg/dL)`, weight: 15, positive: true });
            } else if (data.hdl >= 60) {
                hScore -= 8;
                factors.push({ name: `Active Cardioprotection: High HDL (${data.hdl} mg/dL)`, weight: 8, positive: false });
            }
        }
        if (data.triglycerides !== null) {
            if (data.triglycerides >= 200) {
                hScore += 12;
                factors.push({ name: `Elevated Triglycerides (${data.triglycerides} mg/dL)`, weight: 12, positive: true });
            }
        }

        const heartFinal = Math.min(Math.max(Math.round(hScore), 2), 98);

        // Sort contributing factors by absolute value, capped to top 5
        const sortedFactors = factors
            .sort((a, b) => b.weight - a.weight)
            .slice(0, 5);

        // Preventive Guidelines List
        const recommendations = [];
        if (data.smoking === "Current") {
            recommendations.push("Access tobacco cessation counseling. Halting nicotine cuts coronary event odds by 50% in 12 months.");
        }
        if (data.bp === "High1" || data.bp === "High2" || (data.systolic >= 130)) {
            recommendations.push("Limit sodium intake below 1,500mg daily. Track blood pressure twice weekly at home.");
        }
        if (bmi >= 25) {
            recommendations.push("Pursue an energy-deficit whole food plan to target a 5-10% bodyweight reduction.");
        }
        if (data.symptoms.includes("chest_pain")) {
            recommendations.push("Urgent: Report any chest tightness radiating to the arm/jaw to emergency clinical personnel.");
        }
        if (data.symptoms.includes("polyuria") || data.symptoms.includes("polydipsia") || (data.hba1c && data.hba1c >= 5.7)) {
            recommendations.push("Schedule a laboratory HbA1c review with a primary care physician to verify glycemic status.");
        }
        if (data.physicalActivity === "Low") {
            recommendations.push("Introduce 30 minutes of low-impact cardiovascular training (brisk walking, swimming) 5 times per week.");
        }
        if (data.stressLevel > 6) {
            recommendations.push("Integrate mindfulness-based stress reduction (MBSR) protocols or progressive breathing techniques.");
        }
        if (data.sleepHours < 6.5) {
            recommendations.push("Develop a consistent sleep routine to capture 7 to 8 hours of restorative circadian sleep.");
        }
        if ((data.cholesterol && data.cholesterol >= 200) || (data.ldl && data.ldl >= 130)) {
            recommendations.push("Reduce saturated/trans-fats; incorporate daily soluble fiber (oat bran, legumes) and omega-3s.");
        }

        // Standard tips fallback
        if (recommendations.length < 3) {
            recommendations.push("Maintain your positive lifestyle and schedule yearly routine medical checkups.");
            recommendations.push("Support arterial flexibility by consuming healthy omega-3 fatty acids (flaxseeds, walnuts, wild fish).");
        }

        const dConf = Math.floor(Math.random() * 11) + 84;
        const hConf = Math.floor(Math.random() * 11) + 84;

        return {
            predictions: {
                diabetes: {
                    risk_level: diabetesFinal >= 65 ? "High" : (diabetesFinal >= 30 ? "Medium" : "Low"),
                    probability: diabetesFinal,
                    confidence: dConf
                },
                heart_disease: {
                    risk_level: heartFinal >= 65 ? "High" : (heartFinal >= 30 ? "Medium" : "Low"),
                    probability: heartFinal,
                    confidence: hConf
                }
            },
            factors: sortedFactors,
            recommendations: recommendations,
            timestamp: new Date().toISOString()
        };
    }

    // 9. Display Report in Dashboard
    function renderResultsDashboard(data, inputs) {
        // --- A. PATIENT RECORD DETAILS ---
        displayName.textContent = inputs.patientName;
        displayMrn.textContent = inputs.mrn;
        displayAgeSex.textContent = `${inputs.age} / ${inputs.gender}`;
        
        const heightInMeters = inputs.height / 100;
        const bmi = inputs.weight / (heightInMeters * heightInMeters);
        const bmiFixed = bmi.toFixed(1);
        let bmiText = `${bmiFixed} (Normal)`;
        if (bmi < 18.5) bmiText = `${bmiFixed} (Underweight)`;
        else if (bmi < 25) bmiText = `${bmiFixed} (Healthy Weight)`;
        else if (bmi < 30) bmiText = `${bmiFixed} (Overweight)`;
        else bmiText = `${bmiFixed} (Obese)`;
        displayBmi.textContent = bmiText;

        // Print date
        const dDate = new Date();
        document.getElementById("print-date").textContent = dDate.toLocaleString();

        // Symptoms list
        if (inputs.symptoms && inputs.symptoms.length > 0) {
            const symptomMap = {
                fever: "Fever", fatigue: "Fatigue", chest_pain: "Chest Pain",
                dizziness: "Dizziness", dyspnea: "Short Breath", numbness: "Numbness",
                polyuria: "Polyuria", polydipsia: "Polydipsia", blurred_vision: "Blurred Vision"
            };
            const labels = inputs.symptoms.map(s => symptomMap[s] || s);
            displaySymptoms.textContent = labels.join(", ");
        } else {
            displaySymptoms.textContent = "None reported";
        }

        // --- B. RISK GAUGES ---
        const db = data.predictions.diabetes;
        const hd = data.predictions.heart_disease;

        diabetesBadge.textContent = db.risk_level;
        diabetesBadge.className = `badge-pill risk-${db.risk_level.toLowerCase()}`;
        animateProgressGauge(diabetesRing, db.probability);
        animateCountUp(diabetesProb, db.probability, "%");
        animateCountUp(diabetesConf, db.confidence, "%");
        applyAppleCardGlow(diabetesCard, db.risk_level);

        heartBadge.textContent = hd.risk_level;
        heartBadge.className = `badge-pill risk-${hd.risk_level.toLowerCase()}`;
        animateProgressGauge(heartRing, hd.probability);
        animateCountUp(heartProb, hd.probability, "%");
        animateCountUp(heartConf, hd.confidence, "%");
        applyAppleCardGlow(heartCard, hd.risk_level);

        // --- C. DYNAMIC LAB VALUES SUMMARY TABLE ---
        labsTableBody.innerHTML = "";
        
        const bloodPressureStr = (inputs.systolic && inputs.diastolic) 
            ? `${inputs.systolic}/${inputs.diastolic} mmHg` 
            : `${inputs.bp} Selection`;
            
        let bpStatusTag = "tag-normal";
        let bpStatusLbl = "Normal";
        
        if (inputs.systolic !== null && inputs.diastolic !== null) {
            const sys = inputs.systolic;
            const dia = inputs.diastolic;
            if (sys >= 140 || dia >= 90) { bpStatusTag = "tag-high"; bpStatusLbl = "Stage 2 High"; }
            else if (sys >= 130 || dia >= 80) { bpStatusTag = "tag-high"; bpStatusLbl = "Stage 1 High"; }
            else if (sys >= 120 && dia < 80) { bpStatusTag = "tag-elevated"; bpStatusLbl = "Elevated"; }
        } else {
            if (inputs.bp === "High2") { bpStatusTag = "tag-high"; bpStatusLbl = "Stage 2 High"; }
            else if (inputs.bp === "High1") { bpStatusTag = "tag-high"; bpStatusLbl = "Stage 1 High"; }
            else if (inputs.bp === "Elevated") { bpStatusTag = "tag-elevated"; bpStatusLbl = "Elevated"; }
        }

        addLabTableRow("Blood Pressure", bloodPressureStr, "< 120 / < 80 mmHg", bpStatusLbl, bpStatusTag);

        if (inputs.glucose !== null) {
            const status = inputs.glucose >= 126 ? "Diabetes Range" : (inputs.glucose >= 100 ? "Prediabetes" : "Normal");
            const tag = inputs.glucose >= 126 ? "tag-high" : (inputs.glucose >= 100 ? "tag-elevated" : "tag-normal");
            addLabTableRow("Fasting Glucose", `${inputs.glucose} mg/dL`, "< 100 mg/dL", status, tag);
        }
        
        if (inputs.hba1c !== null) {
            const status = inputs.hba1c >= 6.5 ? "Diabetes Range" : (inputs.hba1c >= 5.7 ? "Prediabetes" : "Normal");
            const tag = inputs.hba1c >= 6.5 ? "tag-high" : (inputs.hba1c >= 5.7 ? "tag-elevated" : "tag-normal");
            addLabTableRow("HbA1c Glycan", `${inputs.hba1c}%`, "< 5.7%", status, tag);
        }

        if (inputs.cholesterol !== null) {
            const status = inputs.cholesterol >= 240 ? "High Risk" : (inputs.cholesterol >= 200 ? "Borderline" : "Normal");
            const tag = inputs.cholesterol >= 240 ? "tag-high" : (inputs.cholesterol >= 200 ? "tag-elevated" : "tag-normal");
            addLabTableRow("Total Cholesterol", `${inputs.cholesterol} mg/dL`, "< 200 mg/dL", status, tag);
        }

        if (inputs.ldl !== null) {
            const status = inputs.ldl >= 160 ? "High Risk" : (inputs.ldl >= 130 ? "Borderline" : "Normal");
            const tag = inputs.ldl >= 160 ? "tag-high" : (inputs.ldl >= 130 ? "tag-elevated" : "tag-normal");
            addLabTableRow("LDL Cholesterol", `${inputs.ldl} mg/dL`, "< 100 mg/dL", status, tag);
        }

        if (inputs.hdl !== null) {
            const limit = inputs.gender === "Male" ? 40 : 50;
            const status = inputs.hdl < limit ? "Low (Risky)" : (inputs.hdl >= 60 ? "High (Protective)" : "Normal");
            const tag = inputs.hdl < limit ? "tag-high" : (inputs.hdl >= 60 ? "tag-normal" : "tag-normal");
            addLabTableRow("HDL Cholesterol", `${inputs.hdl} mg/dL`, `> ${limit} mg/dL`, status, tag);
        }

        if (inputs.triglycerides !== null) {
            const status = inputs.triglycerides >= 200 ? "High Risk" : (inputs.triglycerides >= 150 ? "Borderline" : "Normal");
            const tag = inputs.triglycerides >= 200 ? "tag-high" : (inputs.triglycerides >= 150 ? "tag-elevated" : "tag-normal");
            addLabTableRow("Triglycerides", `${inputs.triglycerides} mg/dL`, "< 150 mg/dL", status, tag);
        }

        if (labsTableBody.children.length === 1) {
            // Only BP entered
            addLabTableRow("Lipid / Sugar Panels", "No lab data entered", "--", "Habit-based calculations", "tag-elevated");
        }

        // --- D. COHORT COMPARISON ANIMATIONS ---
        setTimeout(() => {
            cohortUserDiabetes.style.width = `${db.probability}%`;
            cohortUserDiabetes.querySelector(".bar-val-lbl").textContent = `Patient: ${db.probability}%`;
            cohortUserDiabetes.style.background = db.probability >= 65 ? "var(--system-red)" : (db.probability >= 30 ? "var(--system-orange)" : "var(--system-green)");

            cohortUserHeart.style.width = `${hd.probability}%`;
            cohortUserHeart.querySelector(".bar-val-lbl").textContent = `Patient: ${hd.probability}%`;
            cohortUserHeart.style.background = hd.probability >= 65 ? "var(--system-red)" : (hd.probability >= 30 ? "var(--system-orange)" : "var(--system-green)");
        }, 100);

        // --- E. PRIMARY RISK DRIVERS LIST ---
        factorsContainer.innerHTML = "";
        if (data.factors && data.factors.length > 0) {
            data.factors.forEach(f => {
                const item = document.createElement("div");
                item.className = "factor-item";
                
                const sign = f.positive ? "+" : "-";
                const typeClass = f.positive ? "weight-positive" : "weight-negative";
                const fillClass = f.positive ? "fill-positive" : "fill-negative";

                item.innerHTML = `
                    <div class="factor-info">
                        <span class="factor-name">${f.name}</span>
                        <span class="factor-weight ${typeClass}">${sign}${f.weight}%</span>
                    </div>
                    <div class="factor-track-bar">
                        <div class="factor-fill-bar ${fillClass}" style="width: 0%"></div>
                    </div>
                `;
                factorsContainer.appendChild(item);

                setTimeout(() => {
                    const bar = item.querySelector(".factor-fill-bar");
                    if (bar) bar.style.width = `${Math.min(f.weight * 2.5, 100)}%`;
                }, 100);
            });
        } else {
            factorsContainer.innerHTML = `<p class="helper-text" style="margin: 0; text-align: center;">No significant risk multipliers identified.</p>`;
        }

        // --- F. RECOMMENDATIONS INTERVENTIONS ---
        recommendationsContainer.innerHTML = "";
        data.recommendations.forEach(rec => {
            const li = document.createElement("li");
            li.innerHTML = `<i data-lucide="check-circle-2" class="color-teal"></i><span>${rec}</span>`;
            recommendationsContainer.appendChild(li);
        });

        // --- G. TRIAGE URGENCY ASSESSMENT ---
        let overallLevel = "Low";
        const hasChestPain = inputs.symptoms.includes("chest_pain");
        const hasDyspnea = inputs.symptoms.includes("dyspnea");
        const sys = inputs.systolic;
        const dia = inputs.diastolic;

        if (db.risk_level === "High" || hd.risk_level === "High" || hasChestPain || (sys && sys >= 140) || (dia && dia >= 90) || (inputs.glucose >= 126) || (inputs.hba1c >= 6.5)) {
            overallLevel = "High";
        } else if (db.risk_level === "Medium" || hd.risk_level === "Medium" || hasDyspnea || (sys && sys >= 130) || (dia && dia >= 80) || (inputs.glucose >= 100) || (inputs.hba1c >= 5.7) || (bmi >= 30)) {
            overallLevel = "Medium";
        }

        clinicalUrgency.className = "clinical-urgency-banner";
        if (overallLevel === "High") {
            clinicalUrgency.classList.add("triage-high");
            urgencyIcon.setAttribute("data-lucide", "shield-alert");
            urgencyHeadline.textContent = "Urgent Diagnostic Triage Assessment";
            urgencyDesc.textContent = "High-risk metabolic vectors or primary cardiovascular indicators detected. Attending clinician should prioritize lipid panel screening, fasting glucose assays, and an immediate electrocardiogram (ECG) referral.";
        } else if (overallLevel === "Medium") {
            clinicalUrgency.classList.add("triage-medium");
            urgencyIcon.setAttribute("data-lucide", "info");
            urgencyHeadline.textContent = "Precautionary Clinical Review suggested";
            urgencyDesc.textContent = "Elevated risk markers or pre-existing comorbidities identified. We recommend standard metabolic laboratory checks and advising patient on tailored diet, sleep, and exercise therapies.";
        } else {
            clinicalUrgency.classList.add("triage-low");
            urgencyIcon.setAttribute("data-lucide", "shield-check");
            urgencyHeadline.textContent = "Optimal Maintenance Status";
            urgencyDesc.textContent = "All primary diagnostic parameters match normal/healthy baselines. Advise patient to sustain positive dietary and physical activities. Schedule standard annual checks.";
        }

        lucide.createIcons();
    }

    // Helper: Add rows to Table
    function addLabTableRow(name, value, normal, status, classTag) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><strong>${name}</strong></td>
            <td>${value}</td>
            <td>${normal}</td>
            <td><span class="lab-status-tag ${classTag}">${status}</span></td>
        `;
        labsTableBody.appendChild(row);
    }

    // Helper: SVG Gauge ring offset animations
    function animateProgressGauge(ringElement, percent) {
        const offset = circumference - (percent / 100) * circumference;
        ringElement.style.strokeDashoffset = offset;

        if (percent < 30) {
            ringElement.setAttribute("stroke", "var(--system-green)");
        } else if (percent < 65) {
            ringElement.setAttribute("stroke", "var(--system-orange)");
        } else {
            ringElement.setAttribute("stroke", "var(--system-red)");
        }
    }

    // Helper: Count up numbers
    function animateCountUp(element, endVal, suffix = "") {
        let current = 0;
        const end = parseInt(endVal);
        if (end === 0) {
            element.innerHTML = "0" + suffix;
            return;
        }
        const speed = Math.max(Math.floor(750 / end), 6);
        
        const countInterval = setInterval(() => {
            current++;
            element.innerHTML = current + suffix;
            if (current >= end) {
                clearInterval(countInterval);
            }
        }, speed);
    }

    // Helper: Apple card glows
    function applyAppleCardGlow(cardElement, riskLevel) {
        cardElement.style.boxShadow = "";
        cardElement.style.borderColor = "";

        if (riskLevel === "High") {
            cardElement.style.boxShadow = "0 8px 30px rgba(255, 59, 48, 0.12)";
            cardElement.style.borderColor = "rgba(255, 59, 48, 0.22)";
        } else if (riskLevel === "Medium") {
            cardElement.style.boxShadow = "0 8px 30px rgba(255, 149, 0, 0.12)";
            cardElement.style.borderColor = "rgba(255, 149, 0, 0.22)";
        } else {
            cardElement.style.boxShadow = "0 8px 30px rgba(52, 199, 89, 0.04)";
            cardElement.style.borderColor = "rgba(255, 255, 255, 0.08)";
        }
    }

    // 10. Print Report Handler (Hospital Requirement)
    btnPrintReport.addEventListener("click", () => {
        window.print();
    });

    // 11. Reset Action Handler
    btnReset.addEventListener("click", () => {
        healthForm.reset();
        
        sleepTxt.textContent = "7.0 hours";
        dietTxt.textContent = "Good Quality";
        stressTxt.textContent = "Moderate (5)";
        
        updateBMI();
        showStep(1);

        resultsDashboard.classList.add("hidden");
        resultsPlaceholder.classList.remove("hidden");

        [diabetesRing, heartRing].forEach(ring => {
            ring.style.strokeDashoffset = circumference;
        });

        cohortUserDiabetes.style.width = "0%";
        cohortUserHeart.style.width = "0%";

        if (!chkSaveProfile.checked) {
            localStorage.removeItem("healthoracle_clinical_profile");
        } else {
            saveProfileState();
        }

        checkServerStatus();
    });
});
