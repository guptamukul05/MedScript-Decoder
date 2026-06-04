# openfda_api.py
# Fetches drug information from OpenFDA API + Indian medicine database

import requests
import json
import time
import re

BASE_URL = "https://api.fda.gov/drug"

# ── Get drug label information ────────────────────────────────────
def get_drug_info(drug_name):
    print(f"\nFetching data for: {drug_name}")

    url    = f"{BASE_URL}/label.json"
    params = {"search": f"openfda.generic_name:{drug_name}", "limit": 1}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data    = response.json()
            results = data.get("results", [])
            if results:
                result = results[0]
                info = {
                    "drug_name":    drug_name,
                    "purpose":      get_field(result, "purpose"),
                    "indications":  get_field(result, "indications_and_usage"),
                    "warnings":     get_field(result, "warnings"),
                    "dosage":       get_field(result, "dosage_and_administration"),
                    "side_effects": get_field(result, "adverse_reactions"),
                    "brand_names":  result.get("openfda", {}).get("brand_name", []),
                    "source":       "OpenFDA"
                }
                print(f"Found OpenFDA data for {drug_name}")
                return info
    except Exception as e:
        print(f"OpenFDA error for {drug_name}: {e}")

    return get_fallback_info(drug_name)


# ── Get drug interactions ─────────────────────────────────────────
def get_drug_interactions(drug_name):
    print(f"Checking interactions for: {drug_name}")
    url    = f"{BASE_URL}/event.json"
    params = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "count":  "patient.reaction.reactionmeddrapt.exact",
        "limit":  5
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data    = response.json()
            results = data.get("results", [])
            return [r["term"] for r in results[:5]]
    except Exception as e:
        print(f"Interaction check error: {e}")
    return []


# ── Helper to safely get field ────────────────────────────────────
def get_field(result, field):
    value = result.get(field, [])
    if isinstance(value, list) and value:
        text = value[0]
        text = text.replace("<br>", " ").replace("<br/>", " ")
        text = " ".join(text.split())
        return text[:300] + "..." if len(text) > 300 else text
    return "Information not available"


# ── Indian medicine fallback database ────────────────────────────
def get_fallback_info(drug_name):
    fallback_db = {
        # Antibiotics
        "azithral": {
            "purpose":      "Antibiotic for bacterial infections",
            "indications":  "Chest, throat, ear, skin infections",
            "warnings":     "Complete full course. Tell doctor about heart conditions.",
            "side_effects": "Nausea, stomach pain, diarrhea",
            "brand_names":  ["Azithral", "Azee", "Zithromax"]
        },
        "azithromycin": {
            "purpose":      "Antibiotic for bacterial infections",
            "indications":  "Respiratory, skin, ear infections",
            "warnings":     "Complete full course.",
            "side_effects": "Nausea, diarrhea",
            "brand_names":  ["Azithral", "Azee"]
        },
        "ceftas": {
            "purpose":      "Cephalosporin antibiotic",
            "indications":  "Respiratory, urinary, skin infections",
            "warnings":     "Tell doctor if allergic to penicillin.",
            "side_effects": "Diarrhea, nausea, rash",
            "brand_names":  ["Ceftas", "Taxim-O", "Zifi"]
        },
        "cepodem": {
            "purpose":      "Cephalosporin antibiotic - Cefpodoxime",
            "indications":  "Throat, ear, chest, urinary tract infections",
            "warnings":     "Complete full course. Take with food.",
            "side_effects": "Diarrhea, nausea, stomach pain",
            "brand_names":  ["Cepodem", "Cefpodoxime", "Pecef"]
        },
        "cefpodoxime": {
            "purpose":      "Cephalosporin antibiotic",
            "indications":  "Respiratory and urinary tract infections",
            "warnings":     "Complete full course.",
            "side_effects": "Diarrhea, nausea",
            "brand_names":  ["Cepodem", "Pecef", "Cefoprox"]
        },
        "amoxicillin": {
            "purpose":      "Antibiotic for bacterial infections",
            "indications":  "Ear, throat, chest, urinary infections",
            "warnings":     "Complete full course. Penicillin allergy risk.",
            "side_effects": "Nausea, diarrhea, rash",
            "brand_names":  ["Mox", "Novamox", "Amoxil"]
        },
        "augmentin": {
            "purpose":      "Combination antibiotic - Amoxicillin and Clavulanate",
            "indications":  "Resistant bacterial infections, sinusitis, pneumonia",
            "warnings":     "Take with food. Complete full course.",
            "side_effects": "Diarrhea, nausea, rash",
            "brand_names":  ["Augmentin", "Clavam", "Amoxyclav"]
        },
        "cifran": {
            "purpose":      "Fluoroquinolone antibiotic - Ciprofloxacin",
            "indications":  "UTI, typhoid, respiratory infections, diarrhea",
            "warnings":     "Avoid sun exposure. Not for children under 18.",
            "side_effects": "Nausea, diarrhea, headache",
            "brand_names":  ["Cifran", "Ciplox", "Ciprofloxacin"]
        },
        "ciprofloxacin": {
            "purpose":      "Fluoroquinolone antibiotic",
            "indications":  "UTI, typhoid, respiratory, GI infections",
            "warnings":     "Avoid in pregnancy. No dairy with tablets.",
            "side_effects": "Nausea, diarrhea, headache, dizziness",
            "brand_names":  ["Cifran", "Ciplox", "Neofloxin"]
        },
        "doxycycline": {
            "purpose":      "Tetracycline antibiotic",
            "indications":  "Acne, chest infections, malaria prevention",
            "warnings":     "Take with water, not milk. Avoid sun.",
            "side_effects": "Nausea, photosensitivity, esophageal irritation",
            "brand_names":  ["Doxylin", "Microdox", "Doxy-1"]
        },
        "metronidazole": {
            "purpose":      "Antibiotic and antiprotozoal",
            "indications":  "Amoebiasis, giardia, dental infections, bacterial infections",
            "warnings":     "Strictly avoid alcohol during and 48h after treatment.",
            "side_effects": "Nausea, metallic taste, headache",
            "brand_names":  ["Flagyl", "Metrogyl", "Aldezole"]
        },
        "ornidazole": {
            "purpose":      "Antiprotozoal and antibacterial",
            "indications":  "Amoeba, giardia, bacterial infections",
            "warnings":     "Avoid alcohol.",
            "side_effects": "Nausea, headache, dizziness",
            "brand_names":  ["Ornof", "Orni", "Ornidazole"]
        },
        # Acid and GI
        "cyra": {
            "purpose":      "Proton pump inhibitor - reduces stomach acid",
            "indications":  "Acidity, GERD, stomach ulcers, gastritis",
            "warnings":     "Take 30 min before meals. Long-term use affects bone density.",
            "side_effects": "Headache, nausea, diarrhea",
            "brand_names":  ["Cyra", "Pantocid", "Pan-D"]
        },
        "pantoprazole": {
            "purpose":      "Proton pump inhibitor",
            "indications":  "Acidity, GERD, peptic ulcer",
            "warnings":     "Take 30 min before meals.",
            "side_effects": "Headache, diarrhea, nausea",
            "brand_names":  ["Pantocid", "Pan", "Cyra", "Pantop"]
        },
        "omeprazole": {
            "purpose":      "Proton pump inhibitor",
            "indications":  "Acidity, GERD, H. pylori eradication",
            "warnings":     "Take before meals.",
            "side_effects": "Headache, nausea, abdominal pain",
            "brand_names":  ["Omez", "Ocid", "Prilosec"]
        },
        "ranitidine": {
            "purpose":      "H2 blocker - reduces stomach acid",
            "indications":  "Acidity, peptic ulcer, GERD",
            "warnings":     "May interact with antacids.",
            "side_effects": "Headache, constipation, diarrhea",
            "brand_names":  ["Zinetac", "Rantac", "Aciloc"]
        },
        "ondansetron": {
            "purpose":      "Anti-nausea medication",
            "indications":  "Nausea, vomiting after surgery or chemotherapy",
            "warnings":     "Tell doctor about heart rhythm problems.",
            "side_effects": "Headache, constipation, fatigue",
            "brand_names":  ["Oncet", "Emeset", "Vomikind"]
        },
        "oncet": {
            "purpose":      "Anti-nausea and anti-vomiting",
            "indications":  "Nausea, vomiting, morning sickness",
            "warnings":     "May cause constipation.",
            "side_effects": "Headache, constipation, dizziness",
            "brand_names":  ["Oncet", "Emeset", "Vomikind"]
        },
        "domperidone": {
            "purpose":      "Prokinetic - improves stomach emptying",
            "indications":  "Nausea, vomiting, bloating, slow digestion",
            "warnings":     "Avoid in cardiac patients. Short-term use only.",
            "side_effects": "Dry mouth, headache, diarrhea",
            "brand_names":  ["Domstal", "Vomistop", "Motilium"]
        },
        "meftal": {
            "purpose":      "Antispasmodic pain reliever",
            "indications":  "Abdominal pain, period pain, colic",
            "warnings":     "Take with food.",
            "side_effects": "Stomach upset, nausea, drowsiness",
            "brand_names":  ["Meftal Spas", "Meftal-P"]
        },
        "meftal spas": {
            "purpose":      "Antispasmodic pain reliever",
            "indications":  "Abdominal cramps, colic, period pain",
            "warnings":     "Take with food. Avoid on empty stomach.",
            "side_effects": "Stomach upset, nausea, drowsiness",
            "brand_names":  ["Meftal Spas"]
        },
        "buscopan": {
            "purpose":      "Antispasmodic for abdominal cramps",
            "indications":  "IBS, abdominal cramps, period pain",
            "warnings":     "Avoid in glaucoma and enlarged prostate.",
            "side_effects": "Dry mouth, blurred vision, dizziness",
            "brand_names":  ["Buscopan", "Hyoscine"]
        },
        "norflox": {
            "purpose":      "Antibiotic for GI and urinary infections",
            "indications":  "Travelers diarrhea, UTI, gastroenteritis",
            "warnings":     "Take on empty stomach. Avoid antacids.",
            "side_effects": "Nausea, dizziness, headache",
            "brand_names":  ["Norflox", "Norfloxacin", "Norflo-TZ"]
        },
        # Pain and Fever
        "paracetamol": {
            "purpose":      "Fever reducer and pain reliever",
            "indications":  "Fever, headache, body pain, toothache",
            "warnings":     "Do not exceed 4g per day. Avoid alcohol.",
            "side_effects": "Rare at normal doses. Liver damage if overdosed.",
            "brand_names":  ["Crocin", "Dolo 650", "Calpol", "Panadol"]
        },
        "dolo": {
            "purpose":      "Fever and pain relief - Paracetamol 650mg",
            "indications":  "Fever, body pain, headache",
            "warnings":     "Do not exceed 4g per day.",
            "side_effects": "Rare at normal doses.",
            "brand_names":  ["Dolo 650", "Dolo-650"]
        },
        "ibuprofen": {
            "purpose":      "Anti-inflammatory pain reliever",
            "indications":  "Pain, fever, inflammation, arthritis",
            "warnings":     "Take with food. Avoid in kidney disease.",
            "side_effects": "Stomach upset, nausea, ulcers with long use",
            "brand_names":  ["Brufen", "Combiflam", "Advil"]
        },
        "combiflam": {
            "purpose":      "Paracetamol and Ibuprofen combination",
            "indications":  "Fever, pain, inflammation",
            "warnings":     "Take with food. Avoid in kidney and liver disease.",
            "side_effects": "Stomach upset, nausea",
            "brand_names":  ["Combiflam"]
        },
        "diclofenac": {
            "purpose":      "Anti-inflammatory pain reliever - NSAID",
            "indications":  "Joint pain, muscle pain, arthritis, injury",
            "warnings":     "Take with food. Avoid in heart disease and kidney issues.",
            "side_effects": "Stomach pain, nausea, headache",
            "brand_names":  ["Voveran", "Voltaren", "Diclofenac"]
        },
        "voveran": {
            "purpose":      "Anti-inflammatory for pain and swelling",
            "indications":  "Arthritis, injury, post-surgery pain",
            "warnings":     "Take with food. Short-term use preferred.",
            "side_effects": "Stomach pain, nausea, headache",
            "brand_names":  ["Voveran", "Diclofenac"]
        },
        # Antiallergic
        "lez": {
            "purpose":      "Antihistamine - Levocetirizine",
            "indications":  "Allergic rhinitis, urticaria, sneezing, runny nose",
            "warnings":     "May cause mild drowsiness.",
            "side_effects": "Mild drowsiness, dry mouth, headache",
            "brand_names":  ["Lez", "Lcz", "Xyzal", "Levozet"]
        },
        "levocetirizine": {
            "purpose":      "Antihistamine for allergies",
            "indications":  "Allergic rhinitis, skin allergy, urticaria",
            "warnings":     "Avoid alcohol. May cause drowsiness.",
            "side_effects": "Drowsiness, dry mouth",
            "brand_names":  ["Lez", "Lcz", "Levorid"]
        },
        "cetirizine": {
            "purpose":      "Antihistamine for allergies",
            "indications":  "Hay fever, urticaria, allergic rhinitis",
            "warnings":     "May cause drowsiness.",
            "side_effects": "Drowsiness, dry mouth, headache",
            "brand_names":  ["Zyrtec", "Cetzine", "Alerid"]
        },
        "montair": {
            "purpose":      "Leukotriene antagonist for allergy and asthma",
            "indications":  "Asthma, allergic rhinitis, exercise-induced bronchospasm",
            "warnings":     "Report mood changes or depression to doctor.",
            "side_effects": "Headache, stomach pain, fatigue",
            "brand_names":  ["Montair", "Singulair", "Montelukast"]
        },
        "montelukast": {
            "purpose":      "Controls asthma and allergy symptoms",
            "indications":  "Asthma, allergic rhinitis",
            "warnings":     "Report mood changes to doctor.",
            "side_effects": "Headache, stomach pain, sleep problems",
            "brand_names":  ["Montair", "Singulair", "Romilast"]
        },
        # Cough and Respiratory
        "brozedem": {
            "purpose":      "Cough syrup - expectorant and suppressant",
            "indications":  "Wet and dry cough, chest congestion",
            "warnings":     "Shake well before use.",
            "side_effects": "Mild nausea, drowsiness",
            "brand_names":  ["Brozedem LS", "Brozedex"]
        },
        "brozedex": {
            "purpose":      "Cough expectorant syrup",
            "indications":  "Productive cough, chest congestion",
            "warnings":     "Shake well before use.",
            "side_effects": "Nausea, drowsiness",
            "brand_names":  ["Brozedex LS", "Brozedem"]
        },
        "ascoril": {
            "purpose":      "Combination cough syrup",
            "indications":  "Cough with congestion, bronchitis, asthma cough",
            "warnings":     "Avoid in hypertension. Shake before use.",
            "side_effects": "Palpitations, nausea, tremor",
            "brand_names":  ["Ascoril", "Ascoril LS", "Ascoril D"]
        },
        "alex": {
            "purpose":      "Cough syrup - antiallergic and expectorant",
            "indications":  "Cough, cold, allergic rhinitis",
            "warnings":     "May cause drowsiness.",
            "side_effects": "Drowsiness, dry mouth",
            "brand_names":  ["Alex", "Alex Syrup"]
        },
        "levolin": {
            "purpose":      "Bronchodilator - opens airways",
            "indications":  "Asthma, wheezing, COPD, bronchospasm",
            "warnings":     "Use exactly as directed. Do not exceed dose.",
            "side_effects": "Tremor, rapid heartbeat, headache",
            "brand_names":  ["Levolin", "Levosalbutamol"]
        },
        "budecort": {
            "purpose":      "Inhaled steroid - reduces airway inflammation",
            "indications":  "Asthma, COPD, allergic bronchitis",
            "warnings":     "Rinse mouth after use. Not for acute attacks.",
            "side_effects": "Hoarseness, oral thrush",
            "brand_names":  ["Budecort", "Budesonide", "Pulmicort"]
        },
        "salbutamol": {
            "purpose":      "Bronchodilator for asthma attacks",
            "indications":  "Acute asthma, wheezing, bronchospasm",
            "warnings":     "Rescue inhaler only - not for daily prevention.",
            "side_effects": "Tremor, rapid heartbeat, headache",
            "brand_names":  ["Asthalin", "Ventolin", "Salamol"]
        },
        "asthalin": {
            "purpose":      "Bronchodilator for asthma relief",
            "indications":  "Asthma attack, wheezing, bronchospasm",
            "warnings":     "Rescue inhaler - not for prevention.",
            "side_effects": "Tremor, palpitations, headache",
            "brand_names":  ["Asthalin", "Salbutamol", "Ventolin"]
        },
        "nexaclean": {
            "purpose":      "Nasal saline irrigation solution",
            "indications":  "Nasal congestion, sinusitis, nasal hygiene",
            "warnings":     "For nasal use only.",
            "side_effects": "Mild stinging on application",
            "brand_names":  ["Nexaclean", "Nasoclear"]
        },
        # Vitamins and Supplements
        "shelcal": {
            "purpose":      "Calcium and Vitamin D3 supplement",
            "indications":  "Calcium deficiency, osteoporosis, bone health",
            "warnings":     "Take with meals. Adequate water intake needed.",
            "side_effects": "Constipation, nausea if taken on empty stomach",
            "brand_names":  ["Shelcal", "Calcirol", "Calcium Sandoz"]
        },
        "becosules": {
            "purpose":      "Vitamin B complex supplement",
            "indications":  "B vitamin deficiency, fatigue, nerve health",
            "warnings":     "Generally safe. Urine may turn yellow - this is normal.",
            "side_effects": "Rare. Mild nausea occasionally.",
            "brand_names":  ["Becosules", "Becadexamin"]
        },
        "vitamin d3": {
            "purpose":      "Vitamin D3 supplement",
            "indications":  "Vitamin D deficiency, bone health, immunity",
            "warnings":     "Take with fatty meal for better absorption.",
            "side_effects": "Nausea if overdosed",
            "brand_names":  ["Calcirol", "D-Rise", "Uprise-D3"]
        },
        "uprise": {
            "purpose":      "Vitamin D3 high dose supplement",
            "indications":  "Severe Vitamin D deficiency",
            "warnings":     "Take with fatty food. Do not exceed prescribed dose.",
            "side_effects": "Nausea, weakness if overdosed",
            "brand_names":  ["Uprise D3", "Arachitol"]
        },
        "pregabalin": {
            "purpose":      "Nerve pain and anxiety medication",
            "indications":  "Neuropathic pain, fibromyalgia, anxiety, epilepsy",
            "warnings":     "May cause dizziness and drowsiness. Avoid driving.",
            "side_effects": "Dizziness, drowsiness, weight gain, blurred vision",
            "brand_names":  ["Pregabalin", "Lyrica", "Pregeb"]
        },
        # Diabetes
        "metformin": {
            "purpose":      "Controls blood sugar in Type 2 Diabetes",
            "indications":  "Type 2 Diabetes management",
            "warnings":     "Take with food. Monitor kidney function.",
            "side_effects": "Nausea, stomach upset, diarrhea initially",
            "brand_names":  ["Glycomet", "Glucophage", "Obimet"]
        },
        "glycomet": {
            "purpose":      "Metformin - blood sugar control",
            "indications":  "Type 2 Diabetes",
            "warnings":     "Take with meals. Regular kidney function tests needed.",
            "side_effects": "Nausea, diarrhea, stomach cramps",
            "brand_names":  ["Glycomet", "Glycomet GP", "Glucomet"]
        },
        "glimepiride": {
            "purpose":      "Sulfonylurea - lowers blood sugar",
            "indications":  "Type 2 Diabetes",
            "warnings":     "Do not skip meals after taking.",
            "side_effects": "Low blood sugar, weight gain",
            "brand_names":  ["Amaryl", "Glimestar", "Diapride"]
        },
        "januvia": {
            "purpose":      "DPP-4 inhibitor for Type 2 Diabetes",
            "indications":  "Type 2 Diabetes - controls blood sugar",
            "warnings":     "Report severe joint pain to doctor.",
            "side_effects": "Headache, runny nose, sore throat",
            "brand_names":  ["Januvia", "Sitagliptin", "Istavel"]
        },
        # Blood Pressure
        "amlodipine": {
            "purpose":      "Calcium channel blocker for high blood pressure",
            "indications":  "Hypertension, angina, coronary artery disease",
            "warnings":     "Do not stop suddenly. Monitor BP regularly.",
            "side_effects": "Ankle swelling, flushing, headache",
            "brand_names":  ["Amlovas", "Stamlo", "Amlip"]
        },
        "telmisartan": {
            "purpose":      "ARB for high blood pressure",
            "indications":  "Hypertension, heart failure, kidney protection in diabetes",
            "warnings":     "Avoid in pregnancy. Monitor kidney function.",
            "side_effects": "Dizziness, back pain, diarrhea",
            "brand_names":  ["Telma", "Telmikind", "Telsartan"]
        },
        "atenolol": {
            "purpose":      "Beta-blocker for heart and BP",
            "indications":  "Hypertension, angina, rapid heart rate",
            "warnings":     "Do not stop suddenly - taper dose.",
            "side_effects": "Fatigue, cold hands and feet, slow heartbeat",
            "brand_names":  ["Aten", "Tenormin", "Betacard"]
        },
        "losartan": {
            "purpose":      "ARB for high blood pressure",
            "indications":  "Hypertension, heart failure, diabetic kidney disease",
            "warnings":     "Avoid in pregnancy. Monitor potassium levels.",
            "side_effects": "Dizziness, headache, increased potassium",
            "brand_names":  ["Losar", "Covance", "Repace"]
        },
        # Thyroid
        "thyronorm": {
            "purpose":      "Thyroid hormone replacement - Levothyroxine",
            "indications":  "Hypothyroidism, thyroid hormone deficiency",
            "warnings":     "Take on empty stomach 30 min before breakfast. Lifelong therapy.",
            "side_effects": "Palpitations if overdosed, hair loss initially",
            "brand_names":  ["Thyronorm", "Eltroxin", "Thyrox"]
        },
        "levothyroxine": {
            "purpose":      "Thyroid hormone replacement",
            "indications":  "Hypothyroidism",
            "warnings":     "Empty stomach only. Many drug interactions.",
            "side_effects": "Palpitations, weight loss, sweating if overdosed",
            "brand_names":  ["Thyronorm", "Eltroxin", "Synthroid"]
        },
    }

    # Clean the drug name for lookup
    key       = drug_name.lower().strip()
    key_clean = re.sub(r"\d+$", "", key).strip()

    # Try exact match
    info = fallback_db.get(key)

    # Try without trailing numbers
    if not info:
        info = fallback_db.get(key_clean)

    # Try partial match
    if not info:
        for db_key in fallback_db:
            if key_clean.startswith(db_key) or db_key.startswith(key_clean):
                info = fallback_db[db_key]
                break

    # Final fallback
    if not info:
        info = {
            "purpose":      "Please consult your doctor or pharmacist for details",
            "indications":  "Information not available for this medicine",
            "warnings":     "Always follow your doctors instructions carefully",
            "side_effects": "Consult your doctor or pharmacist",
            "brand_names":  []
        }

    import copy
    info = copy.deepcopy(info)
    info["drug_name"] = drug_name
    info["source"]    = "Indian Medicine Database"
    return info



# ── Run test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    test_drugs = ["paracetamol", "cepodem", "azithral", "cyra", "meftal spas"]
    for drug in test_drugs:
        info = get_drug_info(drug)
        print(f"\n{drug.upper()}")
        print(f"  Purpose    : {info.get('purpose', 'N/A')}")
        print(f"  Warnings   : {info.get('warnings', 'N/A')}")
        print(f"  Brand names: {info.get('brand_names', [])}")
        print(f"  Source     : {info.get('source', 'N/A')}")
        time.sleep(0.3)