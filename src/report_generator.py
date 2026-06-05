# report_generator.py
# Combines OCR + NER + API data into structured patient report

import json
import os
import re
import time
import requests
from datetime import datetime


# ── Normal ranges for common lab parameters ───────────────────────
NORMAL_RANGES = {
    'hemoglobin':     {'min': 12.0,  'max': 17.0,  'unit': 'g/dL'},
    'blood_sugar':    {'min': 70.0,  'max': 100.0, 'unit': 'mg/dL'},
    'hba1c':          {'min': 4.0,   'max': 5.7,   'unit': '%'},
    'tsh':            {'min': 0.4,   'max': 4.0,   'unit': 'mIU/L'},
    'creatinine':     {'min': 0.6,   'max': 1.2,   'unit': 'mg/dL'},
    'platelet_count': {'min': 150.0, 'max': 400.0, 'unit': 'thousand/uL'},
    'wbc':            {'min': 4.0,   'max': 11.0,  'unit': 'thousand/uL'},
    'cholesterol':    {'min': 0.0,   'max': 200.0, 'unit': 'mg/dL'},
    'triglycerides':  {'min': 0.0,   'max': 150.0, 'unit': 'mg/dL'},
    'sgpt':           {'min': 7.0,   'max': 56.0,  'unit': 'U/L'},
    'sgot':           {'min': 10.0,  'max': 40.0,  'unit': 'U/L'},
    'uric_acid':      {'min': 2.4,   'max': 7.0,   'unit': 'mg/dL'},
    'vitamin_d':      {'min': 20.0,  'max': 100.0, 'unit': 'ng/mL'},
    'vitamin_b12':    {'min': 200.0, 'max': 900.0, 'unit': 'pg/mL'},
}


# ── Dynamic report value analyzer ────────────────────────────────
def analyze_report_values(report_text):
    """
    Dynamically parses any lab report PDF.
    Extracts test name, value, unit and reference range from the text.
    Compares actual value against the reference range in the report.
    No hardcoded ranges needed.
    """
    abnormal = []
    normal   = []
    lines    = report_text.split("\n")

    # Pattern: test name, value, optional unit, min - max
    number_pattern = re.compile(
        r"^(.*?)\s+([\d]+\.?\d*)\s*"
        r"(g/dL|%|thou/mm3|mill/mm3|fL|pg|mm/hr|mg/dL|U/L|"
        r"mEq/L|IU/mL|µIU/mL|uIU/mL|ng/mL|pg/mL|umol/L|mmol/L|"
        r"thou/uL|10\^3/uL|10\^6/uL|mL/min.*?)?\s*"
        r"([\d]+\.?\d*)\s*[-–]\s*([\d]+\.?\d*)?\s*$"
    )

    # Pattern for < or > reference ranges
    lt_gt_pattern = re.compile(
        r"^(.*?)\s+([\d]+\.?\d*)\s*"
        r"(g/dL|%|thou/mm3|mg/dL|U/L|mEq/L|IU/mL|µIU/mL|uIU/mL)?\s*"
        r"([<>][\d]+\.?\d*)\s*$"
    )

    skip_keywords = [
        "test name", "bio. ref", "reference", "page", "note",
        "comment", "interpretation", "collected", "processed",
        "name", "age", "gender", "lab no", "ref by", "reported",
        "important", "dr lal", "tel", "fax", "email", "www",
        "factors", "measurement", "hemoglobin variant",
        "end of report", "authenticity", "scan", "qr code",
        "dr rajni", "dr divya", "dr gaurav", "dr rachna",
        "consultant", "pathologist", "biochemist", "laboratory",
        "test conducted", "sample", "kindly", "court",
        "medico", "computer generated", "signature"
    ]

    seen = set()  # Avoid duplicate entries

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        line_lower = line.lower()
        if any(kw in line_lower for kw in skip_keywords):
            continue

        # Try main pattern
        match = number_pattern.match(line)
        if match:
            test_name = match.group(1).strip()
            value_str = match.group(2)
            unit      = (match.group(3) or "").strip()
            ref_min   = match.group(4)
            ref_max   = match.group(5)

            # Clean test name
            test_name = re.sub(r"\s*\(.*?\)\s*$", "", test_name).strip()
            test_name = re.sub(r"\*+", "", test_name).strip()
            test_name = re.sub(r"\s+", " ", test_name).strip()

            if len(test_name) < 3 or re.match(r"^\d+$", test_name):
                continue
            if test_name in seen:
                continue

            try:
                value   = float(value_str)
                ref_min = float(ref_min) if ref_min else None
                ref_max = float(ref_max) if ref_max else None

                if ref_min is not None and ref_max is not None:
                    is_low  = value < ref_min
                    is_high = value > ref_max

                    entry = {
                        "parameter": test_name,
                        "value":     value,
                        "unit":      unit,
                        "min":       ref_min,
                        "max":       ref_max,
                        "status":    "HIGH" if is_high else
                                     "LOW"  if is_low  else "NORMAL"
                    }
                    seen.add(test_name)
                    if is_low or is_high:
                        abnormal.append(entry)
                    else:
                        normal.append(entry)

            except (ValueError, TypeError):
                continue

        else:
            # Try < or > pattern
            match2 = lt_gt_pattern.match(line)
            if match2:
                test_name = match2.group(1).strip()
                value_str = match2.group(2)
                unit      = (match2.group(3) or "").strip()
                ref_str   = match2.group(4)

                test_name = re.sub(r"\s*\(.*?\)\s*$", "", test_name).strip()
                test_name = re.sub(r"\*+", "", test_name).strip()

                if len(test_name) < 3 or test_name in seen:
                    continue

                try:
                    value    = float(value_str)
                    ref_val  = float(ref_str[1:])
                    operator = ref_str[0]

                    if operator == "<":
                        is_high = value >= ref_val
                        entry   = {
                            "parameter": test_name,
                            "value":     value,
                            "unit":      unit,
                            "min":       None,
                            "max":       ref_val,
                            "status":    "HIGH" if is_high else "NORMAL"
                        }
                    else:
                        is_low = value <= ref_val
                        entry  = {
                            "parameter": test_name,
                            "value":     value,
                            "unit":      unit,
                            "min":       ref_val,
                            "max":       None,
                            "status":    "LOW" if is_low else "NORMAL"
                        }

                    seen.add(test_name)
                    if entry["status"] != "NORMAL":
                        abnormal.append(entry)
                    else:
                        normal.append(entry)

                except (ValueError, TypeError):
                    continue

    return abnormal, normal


# ── Urgency calculator ────────────────────────────────────────────
def calculate_urgency(abnormal_values):
    if not abnormal_values:
        return {
            "level":  "normal",
            "color":  "🟢",
            "text":   "All Reports Normal",
            "reason": "All values within normal range"
        }

    critical_keywords = [
        "hemoglobin", "platelet", "creatinine", "glucose",
        "sugar", "potassium", "sodium", "troponin",
        "bilirubin", "alt", "sgpt", "ast", "sgot", "uric acid"
    ]
    moderate_keywords = [
        "tsh", "hba1c", "cholesterol", "triglyceride",
        "rdw", "pcv", "ige", "igm", "igg"
    ]

    has_critical = any(
        any(kw in v["parameter"].lower() for kw in critical_keywords)
        for v in abnormal_values
    )
    has_moderate = any(
        any(kw in v["parameter"].lower() for kw in moderate_keywords)
        for v in abnormal_values
    )

    # Check severity — value more than 50% outside range
    for v in abnormal_values:
        try:
            if v["status"] == "HIGH" and v.get("max"):
                if (v["value"] - v["max"]) / v["max"] > 0.5:
                    has_critical = True
            elif v["status"] == "LOW" and v.get("min") and v["min"] > 0:
                if (v["min"] - v["value"]) / v["min"] > 0.3:
                    has_critical = True
        except Exception:
            pass

    abnormal_names = [v["parameter"] for v in abnormal_values[:3]]

    if has_critical:
        return {
            "level":  "urgent",
            "color":  "🔴",
            "text":   "Consult Doctor Today",
            "reason": f"Critical values: {', '.join(abnormal_names)}"
        }
    elif has_moderate or len(abnormal_values) > 3:
        return {
            "level":  "soon",
            "color":  "🟡",
            "text":   "Consult Doctor This Week",
            "reason": f"Values needing attention: {', '.join(abnormal_names)}"
        }
    else:
        return {
            "level":  "routine",
            "color":  "🟠",
            "text":   "Routine Checkup Advised",
            "reason": "Minor abnormalities detected"
        }


# ── AI symptom and disease suggestion via Anthropic API ──────────
def get_ai_analysis(abnormal_values, user_symptoms=None, mode="symptoms"):
    """
    Uses Claude API to suggest symptoms or diseases based on lab values.
    mode = 'symptoms'  → suggest what symptoms patient may experience
    mode = 'diseases'  → suggest possible conditions based on values + symptoms
    mode = 'routine'   → advisory for routine checkup with some abnormal values
    """
    if not abnormal_values:
        return None

    # Build the abnormal values summary
    values_text = "\n".join([
        f"- {v['parameter']}: {v['value']} {v['unit']} "
        f"({'HIGH' if v['status'] == 'HIGH' else 'LOW'}, "
        f"normal range: {v.get('min', '?')} - {v.get('max', '?')})"
        for v in abnormal_values
    ])

    if mode == "symptoms":
        prompt = f"""A patient has the following abnormal lab report values:

{values_text}

Based ONLY on these specific abnormal values, list the common symptoms 
a patient might experience. Be specific and honest.

Rules:
- Only mention symptoms that are medically well-established for these specific values
- Do not guess or hallucinate
- Keep it simple and easy for a non-medical person to understand
- Format as a bullet list
- Maximum 6-8 symptoms
- End with: "Note: Not all patients experience all symptoms."

Do not mention disease names here, only symptoms."""

    elif mode == "diseases":
        symptoms_text = user_symptoms if user_symptoms else "Not specified"
        prompt = f"""A patient has these abnormal lab values:

{values_text}

The patient reports experiencing these symptoms: {symptoms_text}

Based on the combination of lab values AND reported symptoms, suggest possible conditions.

Rules:
- Only suggest conditions that are strongly supported by BOTH the lab values AND symptoms
- Be honest about uncertainty — say "may indicate" not "you have"
- List 2-4 most likely conditions
- For each condition briefly explain which values/symptoms suggest it
- Always end with the disclaimer: 
  "IMPORTANT: These are possibilities only. A qualified doctor must examine you 
   and interpret these results in the context of your full medical history."
- Do not suggest rare or unlikely conditions
- Do not be alarmist"""

    else:  # routine
        prompt = f"""A patient had a routine health checkup. Their lab report shows 
these values outside normal range:

{values_text}

The patient reports no specific symptoms.

Give a brief, calm advisory:
1. Which values need monitoring
2. Simple lifestyle suggestions for each abnormal value
3. Whether a doctor visit is recommended and how urgently

Rules:
- Be reassuring but honest
- Keep language simple
- Do not diagnose
- End with disclaimer that a doctor should review these results"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )

        if response.status_code == 200:
            data    = response.json()
            content = data.get("content", [])
            for block in content:
                if block.get("type") == "text":
                    return block["text"].strip()
        else:
            print(f"AI API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"AI analysis error: {e}")
        return None


# ── Medicine schedule generator ───────────────────────────────────
def generate_medicine_schedule(drugs, entities):
    schedule = []
    timing_map = {
        'od':            ['Morning'],
        'once daily':    ['Morning'],
        'bd':            ['Morning', 'Night'],
        'twice daily':   ['Morning', 'Night'],
        'tds':           ['Morning', 'Afternoon', 'Night'],
        'three times':   ['Morning', 'Afternoon', 'Night'],
        'qid':           ['Morning', 'Afternoon', 'Evening', 'Night'],
    }

    for i, drug in enumerate(drugs):
        medicines = entities.get('medicines', [])
        if i < len(medicines):
            med = medicines[i]
            timing = med.get('timing', ['As directed by doctor'])
        else:
            freq   = entities['frequencies'][i] \
                     if i < len(entities.get('frequencies', [])) else ''
            timing = ['As directed by doctor']
            for key, times in timing_map.items():
                if key.lower() in freq.lower():
                    timing = times
                    break

        schedule.append({
            'medicine':  drug,
            'dosage':    entities['dosages'][i]
                         if i < len(entities.get('dosages', [])) else 'As prescribed',
            'frequency': entities['frequencies'][i]
                         if i < len(entities.get('frequencies', [])) else 'As directed',
            'timing':    timing,
            'duration':  entities['durations'][i]
                         if i < len(entities.get('durations', [])) else 'As directed',
            'with_food': True
        })

    return schedule


# ── Full report generator ─────────────────────────────────────────
def generate_full_report(entities, ocr_text="", report_text=""):
    print("\nGenerating patient report...")

    from src.openfda_api import get_drug_info, get_drug_interactions
    from src.rxnorm_api  import get_complete_drug_profile

    report = {
        'generated_at':    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'disclaimer':      'This report is AI-generated. Always consult your doctor.',
        'medicines':       [],
        'tests_ordered':   entities.get('tests', []),
        'symptoms':        entities.get('symptoms', []),
        'diagnoses':       entities.get('diagnoses', []),
        'report_analysis': {'abnormal': [], 'normal': []},
        'urgency':         {},
        'drug_interactions': []
    }

    # Medicine details from APIs
    drugs    = entities.get('drugs', [])
    schedule = generate_medicine_schedule(drugs, entities)
    medicines_list = entities.get('medicines', [])

    for i, drug in enumerate(drugs):
        print(f"Processing: {drug}")
        fda_info  = get_drug_info(drug)
        rxn_info  = get_complete_drug_profile(drug)
        reactions = get_drug_interactions(drug)

        med_data = medicines_list[i] if i < len(medicines_list) else {}

        medicine_entry = {
            'name':         drug,
            'form':         med_data.get('form', 'Tab'),
            'dosage':       med_data.get('dosage',    schedule[i]['dosage']
                                         if i < len(schedule) else 'As prescribed'),
            'frequency':    med_data.get('frequency', schedule[i]['frequency']
                                         if i < len(schedule) else 'As directed'),
            'timing':       med_data.get('timing',    schedule[i]['timing']
                                         if i < len(schedule) else ['As directed']),
            'duration':     med_data.get('duration',  schedule[i]['duration']
                                         if i < len(schedule) else 'As directed'),
            'with_food':    True,
            'purpose':      fda_info.get('purpose',      'Consult doctor'),
            'indications':  fda_info.get('indications',  'Consult doctor'),
            'warnings':     fda_info.get('warnings',     'Follow doctor instructions'),
            'side_effects': fda_info.get('side_effects', 'Consult pharmacist'),
            'brand_names':  fda_info.get('brand_names',  []),
            'drug_class':   rxn_info.get('drug_class',   'Unknown'),
            'alternatives': rxn_info.get('alternatives', []),
            'reactions':    reactions[:3]
        }
        report['medicines'].append(medicine_entry)
        time.sleep(0.3)

    # Analyze uploaded reports
    if report_text:
        abnormal, normal = analyze_report_values(report_text)
        report['report_analysis']['abnormal'] = abnormal
        report['report_analysis']['normal']   = normal
        report['urgency'] = calculate_urgency(abnormal)
    else:
        report['urgency'] = {
            'level':  'no_report',
            'color':  '⚪',
            'text':   'No Report Uploaded',
            'reason': 'Upload medical reports for urgency assessment'
        }

    print("Patient report generated successfully")
    return report