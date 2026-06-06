# report_generator.py
# Combines OCR + NER + API data into structured patient report

import re
import json
import os
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
    Parses lab reports where each test is on one line:
    Test Name  value  unit  min - max
    Handles edge cases like inverted value/name lines (Dr Lal PathLabs format)
    """
    abnormal = []
    normal   = []
    seen     = set()

    skip_keywords = [
        "test name", "bio. ref", "results", "units", "hemogram",
        "test report", "report status", "name", "lab no", "ref by",
        "collected", "a/c status", "final", "age", "gender",
        "reported", "green park", "delhi", "lpl-vasant", "nelson",
        "l.s.c", "new delhi", "page ", "collected at", "processed at",
        "differential leucocyte", "absolute leucocyte",
        "liver & kidney", "tsh (thyroid",
        "interpretation", "reference group", "non diabetic",
        "factors that", "hemoglobin variant", "any condition",
        "normal levels", "no close correlation", "tsh levels",
        "values <0.03", "transient increase", "presence of",
        "bun-to-creatinine", "egfr category", "estimated gfr",
        "result rechecked", "please correlate", "the test depends",
        "affected target", "minimum between", "on the measured",
        "particularly when", "reported as per", "the bun-to",
        "azotemia.", "bun/creatinine ratio is about",
        "anisocytosis", "predominantly", "wbc is", "platelets are",
        "in anaemic", "trait.", "of beta", "as per the",
        "leucocyte counts", "note", "comment", "hba1c result",
        "authenticity", "scan", "important instructions",
        "test results released", "laboratory investigations",
        "report delivery", "certain tests", "test results may",
        "courts/forum", "medico legal", "computer generated",
        "the report does", "sample drawn", "if test results",
        "---", "***", "aheeeh", "bnfffn", "fnchfd",
        "hba1c in %", "*495105872*",
        "dr rajni", "dr divya", "dr gaurav", "dr rachna",
        "consultant", "pathologist", "biochemist",
        "dmc no", "dmc/r", "lalpathlabs",
        "e-mail:", "result rechecked"
    ]

    unit_keywords = [
        "mill/mm3", "thou/mm3", "thou/ul", "ml/min/1.73m2",
        "ml/min", "mm/hr", "meq/l", "iu/ml", "µiu/ml", "uiu/ml",
        "ng/ml", "pg/ml", "mg/dl", "gm/dl", "g/dl", "umol/l",
        "mmol/l", "fl", "pg", "u/l", "%"
    ]

    # Patterns
    range_pat  = re.compile(r"([\d]+\.?\d*)\s*[-–]\s*([\d]+\.?\d*)")
    lt_gt_pat  = re.compile(r"([<>])\s*([\d]+\.?\d*)")
    number_pat = re.compile(r"\b([\d]+\.?\d*)\b")

    # ── Pre-process: fix inverted lines ──────────────────────────
    # Dr Lal PathLabs sometimes puts value on line ABOVE test name
    # e.g:
    #   14.60  %
    #   Red Cell Distribution Width (RDW)  11.60 - 14.00
    raw_lines   = report_text.split("\n")
    fixed_lines = []
    i = 0
    while i < len(raw_lines):
        curr      = raw_lines[i].strip()
        next_line = raw_lines[i+1].strip() if i+1 < len(raw_lines) else ""

        # Check if current line is just a value+unit
        val_only = re.match(
            r"^([\d]+\.?\d*)\s*"
            r"(%|g/dL|mg/dL|fL|pg|U/L|thou/mm3|IU/mL|mEq/L|mill/mm3|mm/hr)?\s*$",
            curr, re.IGNORECASE
        )
        # And next line has a test name + range
        has_range_next = re.search(
            r"[\d]+\.?\d*\s*[-–]\s*[\d]+\.?\d*", next_line
        )

        if val_only and has_range_next and next_line:
            # Merge value into next line
            fixed_lines.append(next_line + "  " + curr)
            i += 2
            continue

        fixed_lines.append(curr)
        i += 1

    lines = fixed_lines

    # ── Parse each line ───────────────────────────────────────────
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        line_lower = line.lower()

        # Skip contact/phone lines
        if re.search(r"tel[:\s]|fax[:\s]|@|lalpathlabs|e-mail",
                     line_lower):
            continue

        # Skip junk lines
        if any(kw in line_lower for kw in skip_keywords):
            continue

        # Skip lines starting with dates
        if re.match(r"^\d{1,2}/\d{1,2}/\d{4}", line):
            continue

        # Skip lines with no numbers
        if not number_pat.search(line):
            continue

        # Must have a reference range to be a valid test result
        range_match = range_pat.search(line)
        lt_gt_match = lt_gt_pat.search(line)

        if not range_match and not lt_gt_match:
            continue

        # Extract reference range
        ref_min  = None
        ref_max  = None
        lt_gt_op = None
        lt_gt_val= None

        if range_match:
            ref_min = float(range_match.group(1))
            ref_max = float(range_match.group(2))
        elif lt_gt_match:
            lt_gt_op  = lt_gt_match.group(1)
            lt_gt_val = float(lt_gt_match.group(2))

        # Extract test name — text before first number
        first_num = number_pat.search(line)
        if not first_num:
            continue

        test_name = line[:first_num.start()].strip()
        test_name = re.sub(r"\s+", " ", test_name).strip()
        test_name = re.sub(r"[:\*]+", "", test_name).strip()

        # Skip bad test names
        if (len(test_name) < 2
                or test_name in seen
                or any(kw in test_name.lower() for kw in skip_keywords)
                or test_name[0].isdigit()
                or test_name.startswith("(")
                or test_name.startswith("<")
                or test_name.startswith(">")
                or test_name.startswith("|")
                or re.search(r"tel[:\s]|fax|@", test_name.lower())):
            continue

        # Extract patient value
        # Remove range from line to isolate value
        line_without_range = line
        if range_match:
            line_without_range = (line[:range_match.start()]
                                  + line[range_match.end():])
        elif lt_gt_match:
            line_without_range = (line[:lt_gt_match.start()]
                                  + line[lt_gt_match.end():])

        # Remove test name and units
        line_without_range = line_without_range.replace(test_name, "")
        for uk in unit_keywords:
            line_without_range = re.sub(
                re.escape(uk), "", line_without_range,
                flags=re.IGNORECASE
            )

        # Remaining numbers = patient value
        remaining_nums = number_pat.findall(line_without_range)
        if not remaining_nums:
            continue

        try:
            value = float(remaining_nums[0])
        except ValueError:
            continue

        # Extract unit
        unit = ""
        for uk in unit_keywords:
            if re.search(re.escape(uk), line_lower):
                unit = uk
                break

        # Determine status
        status = "NORMAL"
        if ref_min is not None and ref_max is not None:
            if value < ref_min:
                status = "LOW"
            elif value > ref_max:
                status = "HIGH"
        elif lt_gt_op and lt_gt_val is not None:
            if lt_gt_op == "<" and value >= lt_gt_val:
                status = "HIGH"
            elif lt_gt_op == ">" and value <= lt_gt_val:
                status = "LOW"

        seen.add(test_name)

        entry = {
            "parameter": test_name,
            "value":     value,
            "unit":      unit,
            "min":       ref_min if ref_min is not None
                         else (lt_gt_val if lt_gt_op == ">" else None),
            "max":       ref_max if ref_max is not None
                         else (lt_gt_val if lt_gt_op == "<" else None),
            "status":    status
        }

        if status != "NORMAL":
            abnormal.append(entry)
        else:
            normal.append(entry)

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