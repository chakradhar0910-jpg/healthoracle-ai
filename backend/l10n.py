"""
HealthOracle AI — Backend Localization (l10n) Package
======================================================
This module provides decoupled, middleware-based localization services
without modifying the core machine learning or routing algorithms.
It intercepts incoming requests to capture language preferences,
translates static risk scores, rule-based clinical statements,
and redirects LLM requests to generate output in Telugu and Hindi.
"""

import logging
import json
from contextvars import ContextVar
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import backend.gemini

log = logging.getLogger("healthoracle.l10n")

# Context variable to hold the preferred language for the lifetime of the request
request_lang: ContextVar[str] = ContextVar("request_lang", default="en")

TRANSLATIONS = {
    "te": {
        # Risk Levels
        "Low": "అల్పం",
        "Medium": "మితం",
        "High": "అధికం",
        # SHAP Factors
        "Age": "వయస్సు",
        "High Blood Pressure": "అధిక రక్తపోటు",
        "Sleep Quality": "నిద్ర నాణ్యత",
        "Diet Quality": "ఆహార నాణ్యత",
        "Physical Inactivity": "శారీరక శ్రమ లేకపోవడం",
        "Smoking Habit": "ధూమపాన అలవాటు",
        "Alcohol Intake": "మద్యపానం",
        "High HbA1c": "అధిక HbA1c",
        "High Glucose": "అధిక గ్లూకోజ్",
        "High Cholesterol": "అధిక కొలెస్ట్రాల్",
        "High Stress": "అధిక ఒత్తిడి",
        "Comorbidities": "సహ-వ్యాధులు",
        "Family History": "కుటుంబ చరిత్ర",
        "BMI Factor": "BMI కారకం",
        "- Active Defense": "- క్రియాశీల రక్షణ",
        "- Healthy Heart HDL": "- ఆరోగ్యకరమైన గుండె HDL",
        "- Consistent Sleep Schedule": "- స్థిరమైన నిద్ర షెడ్యూల్",
        # Rule-based Recommendations
        "🚨 Urgent: Report any chest tightness radiating to the arm or jaw to emergency clinical personnel immediately.": 
            "🚨 అత్యవసరం: చేతికి లేదా దవడకు వ్యాపించే ఛాతీ నొప్పి లేదా ఒత్తిడి ఉంటే వెంటనే అత్యవసర వైద్య సిబ్బందికి నివేదించండి.",
        "Schedule an urgent endocrinology consultation — lab markers indicate possible diabetes diagnosis requiring treatment.": 
            "వెంటనే ఎండోక్రినాలజీ సంప్రదింపులను షెడ్యూల్ చేయండి — ల్యాబ్ మార్కర్లు చికిత్స అవసరమయ్యే మధుమేహం నిర్ధారణను సూచిస్తున్నాయి.",
        "🚨 Hypertensive crisis detected. Seek emergency medical care immediately.": 
            "🚨 తీవ్రమైన రక్తపోటు (హైపర్‌టెన్సివ్ క్రైసిస్) గుర్తించబడింది. వెంటనే అత్యవసర వైద్య సహాయం తీసుకోండి.",
        "Begin structured glucose monitoring (morning fasting readings). Consult a certified diabetes educator for a personalized management plan.": 
            "క్రమబద్ధమైన గ్లూకోజ్ పర్యవేక్షణను ప్రారంభించండి (ఉదయం ఖాళీ కడుపుతో రీడింగులు). వ్యక్తిగతీకరించిన నిర్వహణ ప్రణాళిక కోసం సర్టిఫైడ్ డయాబెటిస్ ఎడ్యుకేటర్‌ను సంప్రదించండి.",
        "Schedule a laboratory HbA1c review with a primary care physician to verify glycemic status and rule out prediabetes.": 
            "గ్లైసెమిక్ స్థితిని ధృవీకరించడానికి మరియు ప్రీడయాబెటిస్‌ను నివారించడానికి ప్రాథమిక సంరక్షణ వైద్యుడితో ప్రయోగశాల HbA1c సమీక్షను షెడ్యూల్ చేయండి.",
        "Cardiology referral advised: request a lipid panel, ECG, and echocardiogram to assess cardiac function.": 
            "కార్డియాలజీ రెఫరల్ సూచించబడింది: గుండె పనిచేసే తీరును అంచనా వేయడానికి లిపిడ్ ప్యానెల్, ECG మరియు ఎకోకార్డియోగ్రామ్‌ను అభ్యర్థించండి.",
        "Monitor cardiovascular markers: schedule a follow-up lipid panel and blood pressure checks every 3 months.": 
            "కార్డియోవాస్కులర్ మార్కర్లను పర్యవేక్షించండి: ప్రతి 3 నెలలకు ఒకసారి ఫాలో-అప్ లిపిడ్ ప్యానెల్ మరియు రక్తపోటు తనిఖీలను షెడ్యూల్ చేయండి.",
        "Access tobacco cessation counseling. Halting nicotine cuts coronary event odds by 50% within 12 months.": 
            "పొగాకు విరమణ కౌన్సెలింగ్‌ను పొందండి. నికోటిన్‌ను ఆపడం ద్వారా 12 నెలల్లో గుండె జబ్బుల ముప్పు 50% తగ్గుతుంది.",
        "Pursue an energy-deficit whole food plan targeting 5–10% bodyweight reduction. Even modest weight loss significantly lowers diabetes and cardiovascular risk.": 
            "5-10% శరీర బరువు తగ్గించే లక్ష్యంతో తక్కువ కేలరీల సంపూర్ణ ఆహార ప్రణాళికను అనుసరించండి. స్వల్ప బరువు తగ్గడం కూడా మధుమేహం మరియు గుండె జబ్బుల ప్రమాదాన్ని గణనీయంగా తగ్గిస్తుంది.",
        "Introduce 30 minutes of low-impact cardiovascular training (brisk walking, swimming) 5 times per week to improve insulin sensitivity and cardiac output.": 
            "ఇన్సులిన్ సున్నితత్వాన్ని మరియు గుండె పనితీరును మెరుగుపరచడానికి వారానికి 5 సార్లు 30 నిమిషాల తక్కువ-తీవ్రత గల వ్యాయామం (వేగంగా నడవడం, ఈత కొట్టడం) ప్రారంభించండి.",
        "Integrate mindfulness-based stress reduction (MBSR) protocols, progressive muscle relaxation, or structured breathing techniques to lower cortisol levels.": 
            "కార్టిసాల్ స్థాయిలను తగ్గించడానికి మైండ్‌ఫుల్‌నెస్-ఆధారిత ఒత్తిడి తగ్గింపు (MBSR) పద్ధతులు, ప్రగతిశీల కండరాల సడలింపు లేదా క్రమబద్ధమైన శ్వాస పద్ధతులను అలవర్చుకోండి.",
        "Develop a consistent sleep routine targeting 7–8 hours of restorative circadian sleep; poor sleep is independently linked to glucose dysregulation.": 
            "7-8 గంటల నిరంతర నిద్రను అందించే స్థికమైన నిద్ర దినచర్యను అలవర్చుకోండి; సరిపోని నిద్ర నేరుగా గ్లూకోజ్ అసమతుల్యతకు దారితీస్తుంది.",
        "Reduce dietary saturated/trans-fats; incorporate daily soluble fiber (oat bran, legumes) and omega-3 fatty acids (wild fish, flaxseeds, walnuts).": 
            "ఆహారంలో సంతృప్త/ట్రాన్స్-ఫ్యాట్స్‌ను తగ్గించండి; ప్రతిరోజూ కరిగే పీచు పదార్థం (ఓట్స్, పప్పుధాన్యాలు) మరియు ఒమేగా-3 కొవ్వు ఆమ్లాలు (చేపలు, అవిసె గింజలు, అక్రోట్లు) చేర్చుకోండి.",
        "Limit sodium intake below 1,500 mg daily and track blood pressure twice weekly using a home monitor.": 
            "రోజువారీ సోడియం తీసుకోవడం 1,500 mg కంటే తక్కువకు పరిమితం చేయండి మరియు హోమ్ మానిటర్ ఉపయోగించి వారానికి రెండుసార్లు రక్తపోటును ట్రాక్ చేయండి.",
        "Reduce alcohol to ≤ 2 standard drinks/day (men) or ≤ 1 (women). Heavy intake elevates triglycerides and blood pressure.": 
            "మద్యపానాన్ని రోజుకు ≤ 2 ప్రామాణిక పానీయాలకు (పురుషులు) లేదా ≤ 1 (స్త్రీలు) తగ్గించండి. అధిక వినియోగం ట్రైగ్లిజరైడ్స్ మరియు రక్తపోటును పెంచుతుంది.",
        "Shift from ultra-processed foods to a Mediterranean-pattern diet rich in vegetables, legumes, whole grains, and olive oil.": 
            "అల్ట్రా-ప్రాసెస్డ్ ఆహారాల నుండి కూరగాయలు, పప్పుధాన్యాలు, తృణధాన్యాలు మరియు ఆలివ్ నూనెతో కూడిన మధ్యధరా తరహా ఆహారానికి మారండి.",
        "Maintain your positive lifestyle and schedule a yearly routine medical checkup to track metabolic and cardiovascular health indicators.": 
            "మీ సానుకూల జీవనశైలిని కొనసాగించండి మరియు జీవక్రియ మరియు గుండె ఆరోగ్య సూచికలను ట్రాక్ చేయడానికి వార్షిక సాధారణ వైద్య పరీక్షలను షెడ్యూల్ చేయండి.",
        "Support arterial flexibility by consuming healthy omega-3 fatty acids (flaxseeds, walnuts, wild-caught fish) 3× per week.": 
            "వారానికి 3 సార్లు ఆరోగ్యకరమైన ఒమేగా-3 కొవ్వు ఆమ్లాలను (అవిసె గింజలు, అక్రోట్లు, చేపలు) తీసుకోవడం ద్వారా ధమనుల వశ్యతకు మద్దతు ఇవ్వండి.",
    },
    "hi": {
        # Risk Levels
        "Low": "कम",
        "Medium": "मध्यम",
        "High": "उच्च",
        # SHAP Factors
        "Age": "आयु",
        "High Blood Pressure": "उच्च रक्तचाप",
        "Sleep Quality": "नींद की गुणवत्ता",
        "Diet Quality": "आहार की गुणवत्ता",
        "Physical Inactivity": "शारीरिक निष्क्रियता",
        "Smoking Habit": "धूम्रपान की आदत",
        "Alcohol Intake": "शराब का सेवन",
        "High HbA1c": "उच्च HbA1c",
        "High Glucose": "उच्च ग्लूकोज",
        "High Cholesterol": "उच्च कोलेस्ट्रॉल",
        "High Stress": "उच्च तनाव",
        "Comorbidities": "सह-रुग्णता",
        "Family History": "पारिवारिक इतिहास",
        "BMI Factor": "बीएमआई कारक",
        "- Active Defense": "- सक्रिय रक्षा",
        "- Healthy Heart HDL": "- स्वस्थ हृदय एचडीएल",
        "- Consistent Sleep Schedule": "- लगातार नींद का कार्यक्रम",
        # Rule-based Recommendations
        "🚨 Urgent: Report any chest tightness radiating to the arm or jaw to emergency clinical personnel immediately.": 
            "🚨 तत्काल: हाथ या जबड़े तक फैलने वाली छाती की जकड़न या दर्द की सूचना तुरंत आपातकालीन चिकित्सा कर्मियों को दें।",
        "Schedule an urgent endocrinology consultation — lab markers indicate possible diabetes diagnosis requiring treatment.": 
            "तत्काल एंडोक्रिनोलॉजी परामर्श शेड्यूल करें — लैब मार्कर संभावित मधुमेह निदान का संकेत देते हैं जिसके लिए उपचार की आवश्यकता है।",
        "🚨 Hypertensive crisis detected. Seek emergency medical care immediately.": 
            "🚨 उच्च रक्तचाप संकट (हाइपरटेंसिव क्राइसिस) का पता चला। तुरंत आपातकालीन चिकित्सा सहायता लें।",
        "Begin structured glucose monitoring (morning fasting readings). Consult a certified diabetes educator for a personalized management plan.": 
            "व्यवस्थित ग्लूकोज निगरानी शुरू करें (सुबह खाली पेट रीडिंग)। व्यक्तिगत प्रबंधन योजना के लिए एक प्रमाणित मधुमेह शिक्षक से परामर्श लें।",
        "Schedule a laboratory HbA1c review with a primary care physician to verify glycemic status and rule out prediabetes.": 
            "ग्लाइसेमिक स्थिति को सत्यापित करने और प्रीडायबिटीज को खारिज करने के लिए प्राथमिक उपचार चिकित्सक के साथ प्रयोगशाला HbA1c समीक्षा शेड्यूल करें।",
        "Cardiology referral advised: request a lipid panel, ECG, and echocardiogram to assess cardiac function.": 
            "हृदय रोग विशेषज्ञ (कार्डियोलॉजी) रेफरल की सलाह दी जाती है: हृदय की कार्यप्रणाली का आकलन करने के लिए लिपिड प्रोफाइल, ईसीजी और इकोकार्डियोग्राम का अनुरोध करें।",
        "Monitor cardiovascular markers: schedule a follow-up lipid panel and blood pressure checks every 3 months.": 
            "हृदय संबंधी संकेतकों की निगरानी करें: हर 3 महीने में लिपिड प्रोफाइल और रक्तचाप की जांच शेड्यूल करें।",
        "Access tobacco cessation counseling. Halting nicotine cuts coronary event odds by 50% within 12 months.": 
            "तंबाकू मुक्ति परामर्श प्राप्त करें। निकोटीन बंद करने से 12 महीनों के भीतर कोरोनरी घटनाओं की संभावना 50% कम हो जाती है।",
        "Pursue an energy-deficit whole food plan targeting 5–10% bodyweight reduction. Even modest weight loss significantly lowers diabetes and cardiovascular risk.": 
            "5-10% शरीर के वजन को कम करने के लक्ष्य के साथ कैलोरी-कमी वाले संपूर्ण आहार योजना का पालन करें। मामूली वजन घटाने से भी मधुमेह और हृदय जोखिम काफी कम हो जाता है।",
        "Introduce 30 minutes of low-impact cardiovascular training (brisk walking, swimming) 5 times per week to improve insulin sensitivity and cardiac output.": 
            "इंसुलिन संवेदनशीलता और हृदय कार्यप्रणाली में सुधार के लिए प्रति सप्ताह 5 बार 30 मिनट का कम प्रभाव वाला हृदय व्यायाम (तेज चलना, तैरना) शुरू करें।",
        "Integrate mindfulness-based stress reduction (MBSR) protocols, progressive muscle relaxation, or structured breathing techniques to lower cortisol levels.": 
            "कोर्टिसोल के स्तर को कम करने के लिए माइंडफुलनेस-आधारित तनाव प्रबंधन (MBSR) प्रोटोकॉल, प्रगतिशील मांसपेशी विश्राम, या व्यवस्थित श्वास तकनीक को अपनाएं।",
        "Develop a consistent sleep routine targeting 7–8 hours of restorative circadian sleep; poor sleep is independently linked to glucose dysregulation.": 
            "7-8 घंटे की आरामदायक नींद का लक्ष्य रखते हुए एक सुसंगत नींद की दिनचर्या विकसित करें; खराब नींद स्वतंत्र रूप से ग्लूकोज असंतुलन से जुड़ी है।",
        "Reduce dietary saturated/trans-fats; incorporate daily soluble fiber (oat bran, legumes) and omega-3 fatty acids (wild fish, flaxseeds, walnuts).": 
            "आहार में संतृप्त/ट्रांस-फैट को कम करें; दैनिक घुलनशील फाइबर (जई की भूसी, फलियां) और ओमेगा -3 फैटी एसिड (मछली, अलसी के बीज, अखरोट) को शामिल करें।",
        "Limit sodium intake below 1,500 mg daily and track blood pressure twice weekly using a home monitor.": 
            "सोडियम का सेवन प्रतिदिन 1,500 मिलीग्राम से कम तक सीमित करें और होम मॉनिटर का उपयोग करके सप्ताह में दो बार रक्तचाप को ट्रैक करें।",
        "Reduce alcohol to ≤ 2 standard drinks/day (men) or ≤ 1 (women). Heavy intake elevates triglycerides and blood pressure.": 
            "शराब का सेवन पुरुषों के लिए ≤ 2 मानक पेय/दिन या महिलाओं के लिए ≤ 1 तक कम करें। भारी मात्रा में सेवन ट्राइग्लिसराइड्स और रक्तचाप को बढ़ाता है।",
        "Shift from ultra-processed foods to a Mediterranean-pattern diet rich in vegetables, legumes, whole grains, and olive oil.": 
            "अति-प्रसंस्कृत (अल्ट्रा-प्रोसेस्ड) खाद्य पदार्थों से सब्जियों, फलियों, साबुत अनाज और जैतून के तेल से भरपूर भूमध्यसागरीय शैली के आहार पर जाएं।",
        "Maintain your positive lifestyle and schedule a yearly routine medical checkup to track metabolic and cardiovascular health indicators.": 
            "अपनी सकारात्मक जीवन शैली बनाए रखें और चयापचय तथा हृदय स्वास्थ्य संकेतकों को ट्रैक करने के लिए वार्षिक नियमित चिकित्सा जांच शेड्यूल करें।",
        "Support arterial flexibility by consuming healthy omega-3 fatty acids (flaxseeds, walnuts, wild-caught fish) 3× per week.": 
            "सप्ताह में 3 बार स्वस्थ ओमेगा -3 फैटी एसिड (अलसी, अखरोट, मछली) का सेवन करके धमनियों के लचीलेपन को बनाए रखें।",
    },
    "es": {
        "Low": "Bajo",
        "Medium": "Medio",
        "High": "Alto",
        "Age": "Edad",
        "High Blood Pressure": "Presión arterial alta",
        "Sleep Quality": "Calidad de sueño",
        "Diet Quality": "Calidad de dieta",
        "Physical Inactivity": "Inactividad física",
        "Smoking Habit": "Hábito de fumar",
        "Alcohol Intake": "Consumo de alcohol",
        "High HbA1c": "HbA1c alta",
        "High Glucose": "Glucosa alta",
        "High Cholesterol": "Colesterol alto",
        "High Stress": "Estrés alto",
        "Comorbidities": "Comorbilidades",
        "Family History": "Historia familiar",
        "BMI Factor": "Factor de IMC",
        "- Active Defense": "- Defensa activa",
        "- Healthy Heart HDL": "- HDL de corazón sano",
        "- Consistent Sleep Schedule": "- Horario de sueño constante",
    },
    "fr": {
        "Low": "Faible",
        "Medium": "Moyen",
        "High": "Élevé",
        "Age": "Âge",
        "High Blood Pressure": "Tension artérielle élevée",
        "Sleep Quality": "Qualité de sommeil",
        "Diet Quality": "Qualité d'alimentation",
        "Physical Inactivity": "Inactivité physique",
        "Smoking Habit": "Tabagisme",
        "Alcohol Intake": "Consommation d'alcool",
        "High HbA1c": "HbA1c élevée",
        "High Glucose": "Glycémie élevée",
        "High Cholesterol": "Cholestérol élevé",
        "High Stress": "Stress élevé",
        "Comorbidities": "Comorbidités",
        "Family History": "Antécédents familiaux",
        "BMI Factor": "Facteur IMC",
        "- Active Defense": "- Défense active",
        "- Healthy Heart HDL": "- HDL cardiaque sain",
        "- Consistent Sleep Schedule": "- Horaire de sommeil régulier",
    },
    "de": {
        "Low": "Niedrig",
        "Medium": "Mittel",
        "High": "Hoch",
        "Age": "Alter",
        "High Blood Pressure": "Bluthochdruck",
        "Sleep Quality": "Schlafqualität",
        "Diet Quality": "Ernährungsqualität",
        "Physical Inactivity": "Körperliche Inaktivität",
        "Smoking Habit": "Tabakkonsum",
        "Alcohol Intake": "Alkoholkonsum",
        "High HbA1c": "Erhöhter HbA1c",
        "High Glucose": "Erhöhter Glukosewert",
        "High Cholesterol": "Erhöhtes Cholesterin",
        "High Stress": "Hohe Stressbelastung",
        "Comorbidities": "Komorbiditäten",
        "Family History": "Familiengeschichte",
        "BMI Factor": "BMI-Faktor",
        "- Active Defense": "- Aktive Abwehr",
        "- Healthy Heart HDL": "- Gesundes Herz HDL",
        "- Consistent Sleep Schedule": "- Regelmäßiger Schlafplan",
    }
}

def translate_val(val: str, lang: str) -> str:
    if not val or lang == "en":
        return val
    return TRANSLATIONS.get(lang, {}).get(val, val)

def translate_response_content(content_dict: dict, lang: str) -> dict:
    if lang == "en" or not isinstance(content_dict, dict):
        return content_dict

    # Translate risk predictions
    if "predictions" in content_dict:
        preds = content_dict["predictions"]
        for disease in preds:
            if "risk_level" in preds[disease]:
                preds[disease]["risk_level"] = translate_val(preds[disease]["risk_level"], lang)

    # Translate SHAP factors
    if "factors" in content_dict:
        for f in content_dict["factors"]:
            if isinstance(f, dict) and "name" in f:
                f["name"] = translate_val(f["name"], lang)

    # Translate clinical recommendations list
    if "recommendations" in content_dict:
        recs = content_dict["recommendations"]
        if isinstance(recs, list):
            content_dict["recommendations"] = [translate_val(r, lang) for r in recs]

    return content_dict

# ── Intercept call_llm globally to inject dynamic translation instruction ─────
original_call_llm = backend.gemini.call_llm

def patched_call_llm(prompt: str, *args, **kwargs):
    lang = request_lang.get()
    if lang == "te":
        prompt += "\n\nIMPORTANT: You must write the output clinical recommendations or chat responses entirely in Telugu language (తెలుగు)."
    elif lang == "hi":
        prompt += "\n\nIMPORTANT: You must write the output clinical recommendations or chat responses entirely in Hindi language (हिन्दी)."
    elif lang == "es":
        prompt += "\n\nIMPORTANT: You must write the output clinical recommendations or chat responses entirely in Spanish language (Español)."
    elif lang == "fr":
        prompt += "\n\nIMPORTANT: You must write the output clinical recommendations or chat responses entirely in French language (Français)."
    elif lang == "de":
        prompt += "\n\nIMPORTANT: You must write the output clinical recommendations or chat responses entirely in German language (Deutsch)."
    return original_call_llm(prompt, *args, **kwargs)

backend.gemini.call_llm = patched_call_llm

# ── Setup Localization Middleware on FastAPI app ─────────────────────────────
def initialize_l10n(app):
    @app.middleware("http")
    async def l10n_middleware(request: Request, call_next):
        # 1. Parse preferred language from Accept-Language header
        header_lang = request.headers.get("Accept-Language", "en").lower()
        if "te" in header_lang:
            lang = "te"
        elif "hi" in header_lang:
            lang = "hi"
        elif "es" in header_lang:
            lang = "es"
        elif "fr" in header_lang:
            lang = "fr"
        elif "de" in header_lang:
            lang = "de"
        else:
            lang = "en"

        # 2. Store the language in context variable for downstream LLM prompts
        token = request_lang.set(lang)
        try:
            response = await call_next(request)
            
            # 3. Intercept JSONResponse outputs to translate clinical metrics in-flight
            if lang != "en" and hasattr(response, "body"):
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Capture and decode response content
                    body_content = b""
                    async for chunk in response.body_iterator:
                        body_content += chunk
                    try:
                        data = json.loads(body_content.decode("utf-8"))
                        if isinstance(data, dict):
                            data = translate_response_content(data, lang)
                        elif isinstance(data, list):
                            data = [translate_response_content(item, lang) if isinstance(item, dict) else item for item in data]
                        
                        # Reconstruct translated JSONResponse
                        translated_body = json.dumps(data).encode("utf-8")
                        response = Response(
                            content=translated_body,
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type="application/json"
                        )
                        # Re-add Content-Length
                        response.headers["content-length"] = str(len(translated_body))
                    except Exception as e:
                        log.error("Failed to translate json body in middleware: %s", e)
            
            return response
        finally:
            request_lang.reset(token)

    log.info("📡 Localization engine initialized. Telugu (te), Hindi (hi), Spanish (es), French (fr), and German (de) locales active.")
