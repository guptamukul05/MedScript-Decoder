# ner_pipeline.py
# Rewrote completely for typed/digital Indian prescriptions

import re
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline


# ── Load NER model ────────────────────────────────────────────────
def load_ner_model():
    print("Loading PubMedBERT NER model...")
    model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
    tokenizer  = AutoTokenizer.from_pretrained(model_name)
    model      = AutoModelForTokenClassification.from_pretrained(model_name)
    ner        = pipeline(
        "ner", model=model, tokenizer=tokenizer,
        aggregation_strategy="simple", device=-1
    )
    print("NER model loaded")
    return ner


# ── Detect if prescription is handwritten or typed ────────────────
def detect_prescription_type(text):
    """
    Typed prescriptions have consistent patterns.
    Handwritten OCR output has more noise and inconsistency.
    """
    lines         = [l.strip() for l in text.split("\n") if l.strip()]
    avg_len       = sum(len(l) for l in lines) / max(len(lines), 1)
    has_bullets   = any(l.startswith(("•", "-", "*", "·")) for l in lines)
    has_numbers   = any(re.match(r"^\d+[).]\s", l) for l in lines)
    has_tab_cap   = sum(1 for l in lines
                        if re.match(r"^(TAB|CAP|SYP|INJ|TAB\.|CAP\.)\s",
                                    l, re.IGNORECASE))
    score = 0
    if avg_len > 20:    score += 2
    if has_bullets:     score += 2
    if has_numbers:     score += 2
    if has_tab_cap > 1: score += 3
    return "typed" if score >= 4 else "handwritten"


# ── Clean OCR/PDF text ────────────────────────────────────────────
def clean_prescription_text(text):
    # Remove website/digital prescription maker footers
    footer_patterns = [
        r"Made by Prescription Maker.*",
        r"www\..*\.com.*",
        r"digitalprescriptionmaker.*",
        r"ECG\s*/\s*NEBULISATION.*",
        r"PLEASE BRING YOUR PRESCRIPTIONS.*",
        r"Facilities For.*",
        r"FULL EYE CHECKUP.*",
        r"SPECTACLES.*",
        r"CONTACT LENS.*",
    ]
    cleaned = text
    for pat in footer_patterns:
        cleaned = re.sub(pat, "", cleaned,
                         flags=re.IGNORECASE | re.DOTALL)

    # Normalize dashes — "----" becomes single space
    cleaned = re.sub(r"-{2,}", " ", cleaned)

    # Normalize multiple spaces
    cleaned = re.sub(r" {2,}", " ", cleaned)

    return cleaned.strip()


# ── Extract doctor info ───────────────────────────────────────────
def extract_doctor_info(text):
    info = {}

    # Doctor name
    dr_match = re.search(
        r"(Dr\.?\s+[A-Z][A-Za-z\s\.]+?)(?:\n|M\.B|MBBS|MD|MS|$)",
        text
    )
    if dr_match:
        name = dr_match.group(1).strip().rstrip(".,")
        if len(name) > 4:
            info["doctor_name"] = name

    # Qualification
    qual_match = re.search(
        r"(M\.B\.B\.S\..*?|M\.D\..*?|M\.S\..*?)(?:\n|$)",
        text
    )
    if qual_match:
        info["qualification"] = qual_match.group(1).strip()

    # Registration number
    reg_match = re.search(
        r"Reg\.?\s*No\.?\s*[:\-]?\s*([A-Z]{2,5}[-\s]?\d+)",
        text, re.IGNORECASE
    )
    if reg_match:
        info["reg_number"] = reg_match.group(1).strip()

    # Phone
    phone_match = re.search(r"(\d{10}|\d{3}[-\s]\d{8}|\d{2,4}[-\s]\d{7,8})", text)
    if phone_match:
        info["phone"] = phone_match.group(1)

    # Clinic/Hospital name
    clinic_match = re.search(
        r"([A-Z][A-Za-z\s]+(?:Clinic|Hospital|Centre|Center|Medical|Enclave))",
        text
    )
    if clinic_match:
        info["clinic"] = clinic_match.group(1).strip()

    return info


# ── Extract patient info ──────────────────────────────────────────
def extract_patient_info(text):
    info = {}

    # Date
    date_match = re.search(
        r"Date[:\s]+(\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text, re.IGNORECASE
    )
    if date_match:
        info["date"] = date_match.group(1).strip()

    # Patient name — looks for ALL CAPS name on its own line
    # or after "Patient:" or "Name:"
    name_patterns = [
        r"(?:Patient|Name)\s*[:\-]\s*([A-Za-z\s]+?)(?:\n|Age|$)",
        r"^([A-Z][A-Z\s]{3,30})$",   # All caps line like VISHAL GUPTA
    ]
    for pat in name_patterns:
        match = re.search(pat, text, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Filter out doctor names and headers
            skip_words = ["DR", "TAB", "CAP", "SYP", "DATE", "REG",
                          "MBBS", "TIMINGS", "ADVICE"]
            if not any(w in name.upper() for w in skip_words):
                if 3 < len(name) < 40:
                    info["name"] = name.title()
                    break

    # Age and gender
    age_match = re.search(
        r"(?:Age|AGE)\s*[:\-]?\s*(\d{1,3})\s*(?:Yrs?|Years?)?",
        text, re.IGNORECASE
    )
    if age_match:
        info["age"] = age_match.group(1)

    gender_match = re.search(r"\b(Male|Female|M|F)\b", text, re.IGNORECASE)
    if gender_match:
        g = gender_match.group(1).upper()
        info["gender"] = "Male" if g in ["M", "MALE"] else "Female"

    # Also handle combined like "20/M" or "25/F"
    combined = re.search(r"(\d{1,3})\s*/\s*(M|F)\b", text, re.IGNORECASE)
    if combined:
        info["age"]    = combined.group(1)
        info["gender"] = "Male" if combined.group(2).upper() == "M" else "Female"

    return info


# ── Extract symptoms ──────────────────────────────────────────────
def extract_symptoms(text):
    symptoms = []

    # c/o section
    co_match = re.search(
        r"c/?o\s+(.*?)(?:\n\n|Rx|$)",
        text, re.IGNORECASE | re.DOTALL
    )
    if co_match:
        raw = co_match.group(1).strip()
        for part in re.split(r"[,/\n]", raw):
            part = part.strip()
            if part and len(part) > 2:
                symptoms.append(part.title())

    # Keyword detection
    keywords = [
        "fever", "pain", "cough", "cold", "headache", "vomiting",
        "nausea", "diarrhea", "fatigue", "weakness", "swelling",
        "infection", "inflammation", "bleeding", "hypogastrium",
        "umbilicus", "bp", "diabetes", "rhonchi", "wheeze",
        "congestion", "rhinitis", "sinusitis", "allergy",
        "acidity", "gastritis", "ulcer", "constipation"
    ]
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            title = kw.title()
            if title not in symptoms:
                symptoms.append(title)

    return symptoms


# ── Extract tests ─────────────────────────────────────────────────
def extract_tests(text):
    # Clean footer first to avoid false positives
    clean = clean_prescription_text(text)
    tests = []

    patterns = [
        r"\b(CBC|Complete Blood Count)\b",
        r"\b(Blood\s+Sugar|FBS|RBS|HbA1c)\b",
        r"\b(X[- ]?[Rr]ay|Xray)\b",
        r"\b(MRI|CT\s*[Ss]can)\b",
        r"\b(Urine\s+[TR]|Urine\s+Culture|Urine\s+Test)\b",
        r"\b(Thyroid|TSH|T3|T4)\b",
        r"\b(LFT|Liver\s+Function)\b",
        r"\b(KFT|RFT|Kidney\s+Function)\b",
        r"\b(Lipid\s+Profile)\b",
        r"\b(USG|Sonography|Ultrasound)\b",
        r"\b(Sputum|AFB|Culture)\b",
        r"\b(Blood\s+Culture)\b",
        r"\b(Chest\s+X[- ]?ray)\b",
    ]

    for pat in patterns:
        match = re.search(pat, clean, re.IGNORECASE)
        if match:
            tests.append(match.group(1).strip())

    return list(set(tests))


# ── Parse timing from natural language ───────────────────────────
def parse_timing_natural(timing_text):
    """
    Parses natural timing like:
    'After breakfast and dinner' → ['Morning', 'Night']
    'After breakfast, lunch and dinner' → ['Morning', 'Afternoon', 'Night']
    'After dinner' → ['Night']
    'twice daily' → ['Morning', 'Night']
    'three times daily' → ['Morning', 'Afternoon', 'Night']
    'once daily' → ['Morning']
    'at bedtime' → ['Night']
    '2 puffs twice daily' → ['Morning', 'Night']
    """
    t = timing_text.lower()

    # Natural meal-based timing — most common in Indian prescriptions
    has_breakfast = "breakfast" in t or "morning" in t
    has_lunch     = "lunch" in t or "afternoon" in t or "noon" in t
    has_dinner    = "dinner" in t or "night" in t or "evening" in t
    has_bedtime   = "bedtime" in t or "bed time" in t or "sleep" in t

    timing = []
    if has_breakfast: timing.append("Morning (after breakfast)")
    if has_lunch:     timing.append("Afternoon (after lunch)")
    if has_dinner:    timing.append("Night (after dinner)")
    if has_bedtime:   timing.append("At bedtime")

    if timing:
        return timing

    # Frequency-based fallback
    if re.search(r"four\s*times|qid|4\s*times", t):
        return ["Morning", "Afternoon", "Evening", "Night"]
    if re.search(r"three\s*times|tds|thrice|tid", t):
        return ["Morning", "Afternoon", "Night"]
    if re.search(r"twice|two\s*times|bd|b\.d\.", t):
        return ["Morning", "Night"]
    if re.search(r"once|one\s*time|od|o\.d\.", t):
        return ["Morning"]
    if re.search(r"bedtime|hs|h\.s\.", t):
        return ["At bedtime"]
    if re.search(r"sos|as\s*needed|if\s*needed", t):
        return ["As needed (SOS)"]

    return ["As directed by doctor"]


# ── Parse frequency from text ─────────────────────────────────────
def parse_frequency(text):
    t = text.lower()

    if re.search(r"four\s*times|qid|4\s*times\s*daily", t):
        return "Four times daily"
    if re.search(r"three\s*times|tds|thrice|tid|3\s*times", t):
        return "Three times daily (TDS)"
    if re.search(r"twice|two\s*times|bd|b\.d\.|after\s+breakfast\s+and\s+dinner"
                 r"|breakfast\s+and\s+dinner|morning\s+and\s+night", t):
        return "Twice daily (BD)"
    if re.search(r"once|one\s*time|od|o\.d\.|once\s*daily", t):
        return "Once daily (OD)"
    if re.search(r"sos|as\s*needed|if\s*needed|when\s*required", t):
        return "SOS (as needed)"
    if re.search(r"bedtime|hs|h\.s\.|at\s*night\s*only", t):
        return "Once daily at bedtime"
    if re.search(r"after\s+(breakfast|lunch|dinner|meal)", t):
        # Count how many meals mentioned
        meals = len(re.findall(
            r"(breakfast|lunch|dinner|meal)", t
        ))
        if meals >= 3:  return "Three times daily (TDS)"
        if meals == 2:  return "Twice daily (BD)"
        if meals == 1:  return "Once daily (OD)"

    return "As directed"


# ── Main medicine extraction ──────────────────────────────────────
def extract_medicine_blocks(text):
    """
    Handles both formats:

    Format 1 — Numbered:
    1) Tab Cepodem 200mg twice daily x5d

    Format 2 — Bullet point (like the PDF you uploaded):
    • TAB CEPODEM 200 ---- 15 days
    After breakfast and dinner
    """
    medicines = []
    lines     = text.split("\n")
    i         = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this line starts a medicine entry
        # Matches: "• TAB X", "1) Tab X", "Tab X", "CAP X", "SYP X"
        med_match = re.match(
            r"^(?:[•\-\*·]|\d+[).\s])?\s*"
            r"(TAB|Tab|tab|TAS|Tas|CAP|Cap|SYP|Syp|Syr|INJ|Inj|"
            r"DROPS?|Drops?|OINT|Oint|SPRAY|Spray|GEL|Gel|CREAM|Cream)\s+"
            r"([A-Za-z][A-Za-z0-9\-\/\s]+?)(?:\s+(\d+\.?\d*)\s*"
            r"(mg|ml|mcg|g|iu|units?|puffs?))?"
            r"(?:\s*[-–—]+\s*|\s+)(.*?)$",
            line, re.IGNORECASE
        )

        if not med_match:
            # Also try without form word — plain medicine name line
            # e.g. "FLOMIST NASAL SPRAY---- 15 days"
            plain_match = re.match(
                r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                r"([A-Z][A-Z0-9\s\-]+(?:SPRAY|DROPS|CREAM|GEL|OINT))"
                r"(?:\s*[-–—]+\s*|\s+)(.*?)$",
                line
            )
            if plain_match:
                form      = "Spray/Drops"
                drug_name = plain_match.group(1).strip().title()
                rest      = plain_match.group(2).strip()
                dosage    = ""

                # Look ahead for timing line
                timing_text = rest
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not re.match(
                        r"^(?:[•\-\*·]|\d+[).\s])", next_line
                    ):
                        timing_text += " " + next_line
                        i += 1

                duration  = extract_duration(timing_text + " " + rest)
                frequency = parse_frequency(timing_text)
                timing    = parse_timing_natural(timing_text)

                if len(drug_name) > 2:
                    medicines.append({
                        "form":      form,
                        "name":      drug_name,
                        "dosage":    dosage or "As directed",
                        "frequency": frequency,
                        "duration":  duration,
                        "timing":    timing,
                        "raw":       line
                    })
                i += 1
                continue
            else:
                i += 1
                continue

        form      = med_match.group(1).title()
        drug_name = med_match.group(2).strip()
        dosage_n  = med_match.group(3) or ""
        dosage_u  = med_match.group(4) or ""
        rest      = med_match.group(5).strip()

        # Clean drug name — remove trailing dashes and spaces
        drug_name = re.sub(r"[-\s]+$", "", drug_name).strip()

        # Build dosage
        dosage = (dosage_n + dosage_u) if dosage_n else ""

        # If no dosage in name line, check rest
        if not dosage:
            dose_in_rest = re.search(
                r"(\d+\.?\d*)\s*(mg|ml|mcg|g|iu|units?)",
                rest, re.IGNORECASE
            )
            if dose_in_rest:
                dosage = dose_in_rest.group(1) + dose_in_rest.group(2)

        if not dosage:
            dosage = "As prescribed"

        # Look ahead — next line is often timing info
        # e.g. "After breakfast and dinner"
        timing_text = rest
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line:
                j += 1
                continue
            # Stop if next medicine starts
            if re.match(
                r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                r"(TAB|Tab|CAP|Cap|SYP|Syp|INJ|Inj|SPRAY|[A-Z]{3,})\s+[A-Z]",
                next_line, re.IGNORECASE
            ):
                break
            # It is a continuation line (timing/instructions)
            timing_text += " " + next_line
            i = j
            j += 1
            break

        duration  = extract_duration(timing_text + " " + rest)
        frequency = parse_frequency(timing_text)
        timing    = parse_timing_natural(timing_text)

        if len(drug_name) > 1:
            medicines.append({
                "form":      form,
                "name":      drug_name,
                "dosage":    dosage,
                "frequency": frequency,
                "duration":  duration,
                "timing":    timing,
                "raw":       line + " | " + timing_text
            })

        i += 1

    return medicines


# ── Extract duration ──────────────────────────────────────────────
def extract_duration(text):
    # "15 days", "x5d", "for 7 days", "1 week", "1 month"
    patterns = [
        r"(\d+)\s*(days?|weeks?|months?)",
        r"[xX×]\s*(\d+)\s*[dD]",
        r"for\s+(\d+)\s*(days?|weeks?|months?)",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            num    = groups[0]
            unit   = groups[1] if len(groups) > 1 and groups[1] else "days"
            return f"{num} {unit}"
    return "As directed"


# ── Main extract entities function ────────────────────────────────
def extract_entities(ner_model, text):
    print("\nExtracting entities from prescription...")

    clean_text   = clean_prescription_text(text)
    pres_type    = detect_prescription_type(clean_text)
    medicines    = extract_medicine_blocks(clean_text)
    symptoms     = extract_symptoms(clean_text)
    tests        = extract_tests(clean_text)
    doctor_info  = extract_doctor_info(text)
    patient_info = extract_patient_info(text)

    # Run NER model for additional entity detection
    try:
        ner_results = ner_model(clean_text[:512])
        existing    = [m["name"].lower() for m in medicines]
        for entity in ner_results:
            label = entity.get("entity_group", "")
            word  = entity.get("word", "").strip()
            score = entity.get("score", 0)
            if (score > 0.85
                    and any(x in label.upper()
                            for x in ["CHEM", "DRUG", "B-C"])
                    and word.lower() not in existing
                    and len(word) > 3):
                medicines.append({
                    "form":      "Tab",
                    "name":      word,
                    "dosage":    "As prescribed",
                    "frequency": "As directed",
                    "duration":  "As directed",
                    "timing":    ["As directed by doctor"],
                    "raw":       word
                })
    except Exception as e:
        print(f"NER model note: {e}")

    entities = {
        "medicines":          medicines,
        "drugs":              [m["name"] for m in medicines],
        "dosages":            [m["dosage"] for m in medicines],
        "frequencies":        [m["frequency"] for m in medicines],
        "durations":          [m["duration"] for m in medicines],
        "timings":            [m["timing"] for m in medicines],
        "symptoms":           symptoms,
        "diagnoses":          [],
        "tests":              tests,
        "doctor_info":        doctor_info,
        "patient_info":       patient_info,
        "prescription_type":  pres_type
    }

    print(f"Type     : {pres_type}")
    print(f"Medicines: {len(medicines)}")
    for m in medicines:
        print(f"  {m['form']} {m['name']} {m['dosage']} "
              f"| {m['frequency']} | {m['duration']} | {m['timing']}")
    print(f"Doctor   : {doctor_info}")
    print(f"Patient  : {patient_info}")

    return entities