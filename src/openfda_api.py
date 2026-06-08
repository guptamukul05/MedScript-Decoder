# openfda_api.py
# Drug info: OpenFDA API → RxNorm fuzzy → Indian database fallback

import os
import requests
import json
import time
import re
import copy
from dotenv import load_dotenv

BASE_URL = "https://api.fda.gov/drug"


# ── Helper ────────────────────────────────────────────────────────
def get_field(result, field):
    value = result.get(field, [])
    if isinstance(value, list) and value:
        text = value[0]
        text = text.replace("<br>", " ").replace("<br/>", " ")
        text = " ".join(text.split())
        return text[:300] + "..." if len(text) > 300 else text
    return "Information not available"


# ── RxNorm fuzzy search ───────────────────────────────────────────
def search_rxnorm_fuzzy(drug_name):
    """
    Searches RxNorm for any drug name including Indian brand names.
    Returns generic name if found.
    """
    try:
        url      = "https://rxnav.nlm.nih.gov/REST/drugs.json"
        params   = {"name": drug_name}
        response = requests.get(url, params=params, timeout=8)

        if response.status_code == 200:
            data      = response.json()
            grps      = (data.get("drugGroup", {})
                             .get("conceptGroup", []))
            for grp in grps:
                concepts = grp.get("conceptProperties", [])
                if concepts:
                    name  = concepts[0].get("name", "")
                    rxcui = concepts[0].get("rxcui", "")
                    if name and rxcui:
                        return {"generic_name": name, "rxcui": rxcui}
    except Exception as e:
        print(f"RxNorm search error for {drug_name}: {e}")
    return None


# ── OpenFDA search by name ────────────────────────────────────────
def search_openfda(drug_name):
    try:
        url      = f"{BASE_URL}/label.json"
        params   = {
            "search": f"openfda.generic_name:{drug_name}",
            "limit":  1
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data    = response.json()
            results = data.get("results", [])
            if results:
                result = results[0]
                return {
                    "drug_name":    drug_name,
                    "purpose":      get_field(result, "purpose"),
                    "indications":  get_field(result,
                                              "indications_and_usage"),
                    "warnings":     get_field(result, "warnings"),
                    "side_effects": get_field(result, "adverse_reactions"),
                    "brand_names":  result.get(
                        "openfda", {}).get("brand_name", []),
                    "source":       "OpenFDA"
                }
    except Exception as e:
        print(f"OpenFDA error for {drug_name}: {e}")
    return None


# ── Main get_drug_info ────────────────────────────────────────────
def get_drug_info(drug_name):
    print(f"Fetching info for: {drug_name}")

    # Step 1 — try OpenFDA directly
    result = search_openfda(drug_name)
    if result:
        print(f"Found on OpenFDA: {drug_name}")
        return result

    # Step 2 — try RxNorm to get generic name
    rxnorm = search_rxnorm_fuzzy(drug_name)
    if rxnorm:
        generic = rxnorm.get("generic_name", "")
        print(f"RxNorm: {drug_name} -> {generic}")
        if generic and generic.lower() != drug_name.lower():
            result = search_openfda(generic)
            if result:
                result["drug_name"]    = drug_name
                result["generic_name"] = generic
                result["source"]       = "OpenFDA via RxNorm"
                return result

    # Step 3 — Indian database fallback
    print(f"Using Indian database for: {drug_name}")
    return get_fallback_info(drug_name)


# ── Drug interactions ─────────────────────────────────────────────
def get_drug_interactions(drug_name):
    try:
        url      = f"{BASE_URL}/event.json"
        params   = {
            "search": f"patient.drug.medicinalproduct:{drug_name}",
            "count":  "patient.reaction.reactionmeddrapt.exact",
            "limit":  5
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data    = response.json()
            results = data.get("results", [])
            return [r["term"] for r in results[:3]]
    except Exception:
        pass
    return []


# ── Indian medicine database ──────────────────────────────────────
def get_fallback_info(drug_name):
    db = {
        "azithral": {
            "purpose":      "Antibiotic for bacterial infections",
            "indications":  "Chest, throat, ear, skin infections",
            "warnings":     "Complete full course. Inform doctor about heart conditions.",
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
            "warnings":     "Inform doctor if allergic to penicillin.",
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
            "indications":  "Amoebiasis, giardia, dental and bacterial infections",
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
        "cyra": {
            "purpose":      "Proton pump inhibitor - reduces stomach acid",
            "indications":  "Acidity, GERD, stomach ulcers, gastritis",
            "warnings":     "Take 30 min before meals. Long-term use affects bone density.",
            "side_effects": "Headache, nausea, diarrhea",
            "brand_names":  ["Cyra", "Pantocid", "Pan-D"]
        },
        "pantocid": {
            "purpose":      "Proton pump inhibitor - reduces stomach acid",
            "indications":  "Acidity, GERD, stomach ulcers, gastritis",
            "warnings":     "Take 30 min before meals.",
            "side_effects": "Headache, diarrhea, nausea",
            "brand_names":  ["Pantocid", "Pan", "Pantop", "Cyra"]
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
            "warnings":     "Inform doctor about heart rhythm problems.",
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
        "lez": {
            "purpose":      "Antihistamine - Levocetirizine for allergies",
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
        "lorfast": {
            "purpose":      "Antihistamine - Loratadine for allergies",
            "indications":  "Allergic rhinitis, urticaria, hay fever, sneezing",
            "warnings":     "Generally non-drowsy. Avoid alcohol.",
            "side_effects": "Headache, dry mouth, fatigue",
            "brand_names":  ["Lorfast", "Loratadine", "Claritin", "Alavert"]
        },
        "lorfast am": {
            "purpose":      "Antihistamine - Loratadine for allergies and congestion",
            "indications":  "Allergic rhinitis with nasal congestion, urticaria",
            "warnings":     "Avoid in heart disease and hypertension.",
            "side_effects": "Headache, dry mouth, palpitations",
            "brand_names":  ["Lorfast AM", "Loratadine + Pseudoephedrine"]
        },
        "loratadine": {
            "purpose":      "Non-drowsy antihistamine for allergies",
            "indications":  "Hay fever, urticaria, allergic rhinitis",
            "warnings":     "Generally safe. Avoid alcohol.",
            "side_effects": "Headache, dry mouth, fatigue",
            "brand_names":  ["Lorfast", "Claritin", "Alavert"]
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
        "flomist": {
            "purpose":      "Nasal corticosteroid spray - reduces nasal inflammation",
            "indications":  "Allergic rhinitis, nasal congestion, sinusitis, nasal polyps",
            "warnings":     "Use regularly as directed. Takes 1-2 weeks for full effect.",
            "side_effects": "Nasal dryness, mild nosebleed, sneezing after use",
            "brand_names":  ["Flomist", "Fluticasone", "Flonase", "Nasoflo"]
        },
        "fluticasone": {
            "purpose":      "Corticosteroid nasal spray for allergy",
            "indications":  "Allergic rhinitis, nasal congestion, nasal polyps",
            "warnings":     "Use regularly. Do not stop suddenly if used long-term.",
            "side_effects": "Nasal dryness, mild nosebleed",
            "brand_names":  ["Flomist", "Flonase", "Nasoflo"]
        },
        "natvie": {
            "purpose":      "Vitamin and mineral supplement - Nattokinase based",
            "indications":  "Nutritional deficiency, general health supplement",
            "warnings":     "Take with food. Consult doctor if on blood thinners.",
            "side_effects": "Mild nausea if taken on empty stomach",
            "brand_names":  ["Natvie", "Nattokinase supplement"]
        },
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

    key       = drug_name.lower().strip()
    key_clean = re.sub(r"\d+$", "", key).strip()

    info = (db.get(key)
            or db.get(key_clean))

    if not info:
        for db_key in db:
            if (key_clean.startswith(db_key)
                    or db_key.startswith(key_clean)):
                info = db[db_key]
                break

    if not info:
        info = {
            "purpose":      "Please consult your doctor or pharmacist for details",
            "indications":  "Information not available for this medicine",
            "warnings":     "Always follow your doctors instructions carefully",
            "side_effects": "Consult your doctor or pharmacist",
            "brand_names":  []
        }

    info = copy.deepcopy(info)
    info["drug_name"] = drug_name
    info["source"]    = "Indian Medicine Database"
    return info

def check_drug_interactions(drug_list):
    """
    Checks interactions between all medicine combinations.
    Uses OpenFDA + RxNorm + Groq AI for analysis.
    Returns only combinations that have potential interactions.
    """
    if len(drug_list) < 2:
        return []

    from itertools import combinations
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY", "")

    # Build all pairs
    pairs = list(combinations(drug_list, 2))

    if not pairs:
        return []

    # Build prompt for Groq to check all pairs at once
    pairs_text = "\n".join([
        f"{i+1}. {p[0].title()} + {p[1].title()}"
        for i, p in enumerate(pairs)
    ])

    prompt = f"""Check drug interactions for these medicine combinations:

{pairs_text}

For each combination:
- If there is a KNOWN clinically significant interaction: describe it briefly
- If there is NO significant interaction: say "No significant interaction"

Rules:
- Be medically accurate and concise
- Only mention interactions that are well-documented
- Do not guess or hallucinate interactions
- For Indian brand names, consider their generic equivalents
- Keep each response to 1-2 lines maximum
- Format your response EXACTLY like this for each pair:

1. [Medicine A] + [Medicine B]: [interaction description or "No significant interaction"]
2. [Medicine A] + [Medicine B]: [interaction description or "No significant interaction"]

Only list pairs that have significant interactions at the end as a summary."""

    try:
        if api_key:
            client   = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role":    "system",
                        "content": "You are a clinical pharmacist. "
                                   "You provide accurate, concise drug "
                                   "interaction information. You never "
                                   "fabricate interactions."
                    },
                    {
                        "role":    "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.1  # Low temperature for factual accuracy
            )
            raw = response.choices[0].message.content.strip()

            # Parse the response
            interactions = []
            lines        = raw.split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Match numbered lines like "1. DrugA + DrugB: description"
                match = re.match(
                    r"^\d+\.\s*(.+?)\s*\+\s*(.+?):\s*(.+)$",
                    line
                )
                if match:
                    drug_a = match.group(1).strip()
                    drug_b = match.group(2).strip()
                    desc   = match.group(3).strip()

                    # Only include if there IS an interaction
                    if "no significant interaction" not in desc.lower() \
                            and "no known interaction" not in desc.lower() \
                            and len(desc) > 5:

                        # Determine severity
                        desc_lower = desc.lower()
                        if any(w in desc_lower for w in [
                            "serious", "severe", "avoid", "contraindicated",
                            "dangerous", "fatal", "life-threatening"
                        ]):
                            severity = "serious"
                            icon     = "🔴"
                        elif any(w in desc_lower for w in [
                            "monitor", "caution", "may", "can",
                            "possible", "potential", "risk"
                        ]):
                            severity = "moderate"
                            icon     = "🟡"
                        else:
                            severity = "mild"
                            icon     = "🟠"

                        interactions.append({
                            "drug_a":   drug_a,
                            "drug_b":   drug_b,
                            "desc":     desc,
                            "severity": severity,
                            "icon":     icon
                        })

            return interactions

        else:
            return []

    except Exception as e:
        print(f"Interaction check error: {e}")
        return []

# ── Test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_drugs = ["cepodem", "pantocid", "lorfast am",
                  "flomist", "natvie", "azithral"]
    for drug in test_drugs:
        info = get_drug_info(drug)
        print(f"\n{drug.upper()}")
        print(f"  Purpose : {info.get('purpose','N/A')}")
        print(f"  Warning : {info.get('warnings','N/A')[:80]}")
        print(f"  Source  : {info.get('source','N/A')}")
        time.sleep(0.2)