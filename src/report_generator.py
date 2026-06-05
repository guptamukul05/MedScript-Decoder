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
    Handles lab reports where value, unit and range are on separate lines.
    This is the standard PyMuPDF extraction format for columnar PDFs.
    """
    abnormal = []
    normal   = []
    lines    = [l.strip() for l in report_text.split("\n")]
    seen     = set()

    skip_keywords = [
        "test name", "bio. ref", "reference", "page", "note",
        "comment", "interpretation", "collected", "processed",
        "name", "age", "gender", "lab no", "ref by", "reported",
        "important", "dr lal", "tel", "fax", "email", "www",
        "factors", "measurement", "end of report", "authenticity",
        "scan", "qr code", "dr rajni", "dr divya", "dr gaurav",
        "consultant", "pathologist", "biochemist", "laboratory",
        "test conducted", "sample", "kindly", "court", "medico",
        "computer generated", "signature", "report status",
        "collected at", "processed at", "results", "units",
        "hemogram", "liver", "kidney", "function test",
        "differential", "leucocyte", "absolute", "immunoglobulin",
        "thyroid", "hba1c", "interpretation", "reference group",
        "non diabetic", "prediabetes", "diagnosing", "therapeutic",
        "factors that", "measurement", "hbsc", "hbss"
    ]

    # Units we recognize
    unit_patterns = re.compile(
        r"^(g/dL|%|thou/mm3|mill/mm3|fL|pg|mm/hr|mg/dL|U/L|"
        r"mEq/L|IU/mL|µIU/mL|uIU/mL|ng/mL|pg/mL|umol/L|mmol/L|"
        r"thou/uL|gm/dL|mL/min.*?)$",
        re.IGNORECASE
    )

    # Reference range patterns
    range_pattern    = re.compile(r"^([\d]+\.?\d*)\s*[-–]\s*([\d]+\.?\d*)$")
    lt_gt_pattern    = re.compile(r"^([<>])\s*([\d]+\.?\d*)$")
    range_with_space = re.compile(r"^\s*([\d]+\.?\d*)\s*-\s*([\d]+\.?\d*)\s*$")

    # Pure number pattern
    number_pattern = re.compile(r"^[\d]+\.?\d*$")

    i = 0
    while i < len(lines):
        line = lines[i]

        if not line or len(line) < 2:
            i += 1
            continue

        line_lower = line.lower()
        if any(kw in line_lower for kw in skip_keywords):
            i += 1
            continue

        # Check if this looks like a test name
        # Test names are text lines that are not numbers, units or ranges
        is_number   = number_pattern.match(line)
        is_unit     = unit_patterns.match(line)
        is_range    = range_pattern.match(line) or range_with_space.match(line)
        is_lt_gt    = lt_gt_pattern.match(line)
        is_in_parens = line.startswith("(") and line.endswith(")")

        if (not is_number and not is_unit and not is_range
                and not is_lt_gt and not is_in_parens
                and len(line) > 3
                and not line[0].isdigit()):

            # This could be a test name — look ahead for value/unit/range
            test_name = line

            # Remove method in parentheses from next line
            j = i + 1
            if j < len(lines) and lines[j].startswith("("):
                j += 1  # Skip method description line

            # Now look ahead up to 6 lines for value, unit, range
            value    = None
            unit     = ""
            ref_min  = None
            ref_max  = None
            ref_str  = None
            operator = None

            lookahead_lines = lines[j:j+6]

            for la_line in lookahead_lines:
                la_line = la_line.strip()
                if not la_line:
                    continue

                # Check for reference range first (e.g. "13.00 - 17.00")
                r_match = range_pattern.match(la_line) or \
                          range_with_space.match(la_line)
                if r_match and ref_min is None:
                    ref_min = float(r_match.group(1))
                    ref_max = float(r_match.group(2))
                    continue

                # Check for < or > range (e.g. "<2.00" or ">59")
                lg_match = lt_gt_pattern.match(la_line)
                if lg_match and ref_min is None and ref_max is None:
                    operator = lg_match.group(1)
                    ref_str  = float(lg_match.group(2))
                    continue

                # Check for unit
                u_match = unit_patterns.match(la_line)
                if u_match and not unit:
                    unit = la_line
                    continue

                # Check for value (pure number)
                n_match = number_pattern.match(la_line)
                if n_match and value is None:
                    try:
                        value = float(la_line)
                    except ValueError:
                        pass
                    continue

                # If we hit another test name, stop
                if (not la_line[0].isdigit()
                        and not la_line.startswith("(")
                        and not unit_patterns.match(la_line)
                        and not range_pattern.match(la_line)
                        and len(la_line) > 3):
                    break

            # Process if we found a value
            if value is not None:
                # Clean test name
                test_name = re.sub(r"\s+", " ", test_name).strip()
                test_name = re.sub(r"\*+", "", test_name).strip()

                if test_name in seen or len(test_name) < 3:
                    i += 1
                    continue

                seen.add(test_name)

                entry = {
                    "parameter": test_name,
                    "value":     value,
                    "unit":      unit,
                    "min":       ref_min,
                    "max":       ref_max,
                    "status":    "NORMAL"
                }

                if ref_min is not None and ref_max is not None:
                    if value < ref_min:
                        entry["status"] = "LOW"
                    elif value > ref_max:
                        entry["status"] = "HIGH"

                elif operator and ref_str is not None:
                    entry["max"] = ref_str if operator == "<" else None
                    entry["min"] = ref_str if operator == ">" else None
                    if operator == "<" and value >= ref_str:
                        entry["status"] = "HIGH"
                    elif operator == ">" and value <= ref_str:
                        entry["status"] = "LOW"

                if entry["status"] != "NORMAL":
                    abnormal.append(entry)
                else:
                    normal.append(entry)

        i += 1

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
    Uses Groq free API (Llama 3) to analyze lab values.
    mode = 'symptoms'  → suggest symptoms patient may experience
    mode = 'diseases'  → suggest possible conditions
    mode = 'routine'   → advisory for routine checkup
    """
    if not abnormal_values:
        return None

    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY", "")

    if not api_key:
        return "AI analysis unavailable — Groq API key not configured."

    # Build values summary
    values_text = "\n".join([
        f"- {v['parameter']}: {v['value']} {v['unit']} "
        f"({'HIGH' if v['status'] == 'HIGH' else 'LOW'}, "
        f"normal: {v.get('min','?')} - {v.get('max','?')})"
        for v in abnormal_values
    ])

    if mode == "symptoms":
        prompt = f"""A patient has these abnormal lab report values:

{values_text}

Based ONLY on these specific abnormal values, list the common symptoms 
a patient might experience. Be specific and medically accurate.

Rules:
- Only mention symptoms that are medically well-established for these values
- Do not guess or make up symptoms
- Keep language simple for a non-medical person
- Format as a bullet list with brief explanation for each
- Maximum 6-8 symptoms
- End with exactly this line: "Note: Not all patients experience all symptoms."
- Do NOT mention disease names here, only symptoms"""

    elif mode == "diseases":
        symptoms_text = user_symptoms if user_symptoms else "Not specified"
        prompt = f"""A patient has these abnormal lab values:

{values_text}

The patient reports experiencing: {symptoms_text}

Based on the combination of lab values AND reported symptoms,
suggest possible medical conditions.

Rules:
- Only suggest conditions strongly supported by BOTH lab values AND symptoms
- Say "may indicate" or "could suggest" — never say "you have"
- List 2-4 most likely conditions maximum
- For each condition briefly explain which values and symptoms suggest it
- Do not suggest rare or unlikely conditions
- Do not be alarmist
- End with exactly this disclaimer:
  "IMPORTANT: These are possibilities only. A qualified doctor must
   examine you and interpret results in context of your full medical history.
   Do not self-diagnose or self-medicate." """

    else:  # routine
        prompt = f"""A patient had a routine health checkup.
These values are outside normal range:

{values_text}

The patient has no specific symptoms — this was a routine checkup.

Give a brief, calm, helpful advisory:
1. Which values need monitoring and why
2. Simple lifestyle suggestions for each abnormal value
3. Whether a doctor visit is recommended and how urgently

Rules:
- Be reassuring but honest
- Keep language simple and friendly
- Do not diagnose anything
- Do not be alarmist
- End with: "Please share these results with your doctor at your next visit." """

    try:
        from groq import Groq

        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role":    "system",
                    "content": "You are a helpful medical information assistant. "
                               "You provide clear, accurate, honest medical information "
                               "based on lab values. You never diagnose — you only "
                               "inform and suggest consulting a doctor."
                },
                {
                    "role":    "user",
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq API error: {e}")
        return "AI analysis temporarily unavailable. Please consult your doctor directly."

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