# ner_pipeline.py
# Complete rewrite for typed/digital Indian prescriptions

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


# ── Detect prescription type ──────────────────────────────────────
def detect_prescription_type(text):
    lines     = [l.strip() for l in text.split("\n") if l.strip()]
    avg_len   = sum(len(l) for l in lines) / max(len(lines), 1)
    has_tab   = sum(1 for l in lines
                    if re.match(r"^(TAB|CAP|SYP|INJ)\s", l, re.IGNORECASE))
    score     = 0
    if avg_len > 20: score += 2
    if has_tab > 1:  score += 3
    return "typed" if score >= 4 else "handwritten"


# ── Clean prescription text ───────────────────────────────────────
def clean_prescription_text(text):
    # Remove specific footer lines only — NOT with DOTALL
    # DOTALL was deleting all medicine lines after the URL
    footer_patterns = [
        r"Made by Prescription Maker[^\n]*",
        r"\[?www\.[^\s\]]+\][^\n]*",
        r"https?://[^\s\n]+",
        r"digitalprescriptionmaker[^\n]*",
        r"ECG\s*/\s*NEBULISATION[^\n]*",
        r"PLEASE BRING YOUR PRESCRIPTIONS[^\n]*",
        r"Facilities For[^\n]*",
        r"FULL EYE CHECKUP[^\n]*",
        r"SPECTACLES[^\n]*",
        r"CONTACT LENS[^\n]*",
    ]
    cleaned = text
    for pat in footer_patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # Remove multiple blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


# ── Parse timing from natural language ───────────────────────────
def parse_timing_natural(timing_text):
    t = timing_text.lower()
    has_breakfast = "breakfast" in t or "morning" in t
    has_lunch     = "lunch" in t or "afternoon" in t or "noon" in t
    has_dinner    = "dinner" in t or "night" in t or "evening" in t
    has_bedtime   = "bedtime" in t or "bed time" in t or "sleep" in t

    timing = []
    if has_breakfast: timing.append("Morning (after breakfast)")
    if has_lunch:     timing.append("Afternoon (after lunch)")
    if has_dinner:    timing.append("Night (after dinner)")
    if has_bedtime:   timing.append("At bedtime")
    if timing:        return timing

    if re.search(r"four\s*times|qid|4\s*times", t):
        return ["Morning", "Afternoon", "Evening", "Night"]
    if re.search(r"three\s*times|tds|thrice|tid", t):
        return ["Morning", "Afternoon", "Night"]
    if re.search(r"twice|two\s*times|bd|b\.d\.|2\s*puffs.*twice", t):
        return ["Morning", "Night"]
    if re.search(r"once|one\s*time|od|o\.d\.", t):
        return ["Morning"]
    if re.search(r"bedtime|hs|h\.s\.", t):
        return ["At bedtime"]
    if re.search(r"sos|as\s*needed|if\s*needed", t):
        return ["As needed (SOS)"]
    return ["As directed by doctor"]


# ── Parse frequency ───────────────────────────────────────────────
def parse_frequency(text):
    t = text.lower()
    if re.search(r"four\s*times|qid|4\s*times", t):
        return "Four times daily"
    if re.search(r"three\s*times|tds|thrice|tid|3\s*times", t):
        return "Three times daily (TDS)"
    if re.search(r"twice|two\s*times|bd|b\.d\.|"
                 r"breakfast\s+and\s+dinner|"
                 r"morning\s+and\s+night|"
                 r"2\s*puffs.*twice", t):
        return "Twice daily (BD)"
    if re.search(r"once|one\s*time|od|o\.d\.|once\s*daily", t):
        return "Once daily (OD)"
    if re.search(r"sos|as\s*needed|if\s*needed|when\s*required", t):
        return "SOS (as needed)"
    if re.search(r"bedtime|hs|h\.s\.|at\s*night\s*only", t):
        return "Once daily at bedtime"
    if re.search(r"after\s+(breakfast|lunch|dinner|meal)", t):
        meals = len(re.findall(r"(breakfast|lunch|dinner|meal)", t))
        if meals >= 3: return "Three times daily (TDS)"
        if meals == 2: return "Twice daily (BD)"
        if meals == 1: return "Once daily (OD)"
    return "As directed"


# ── Extract duration ──────────────────────────────────────────────
def extract_duration(text):
    text = re.sub(r"-{2,}", " ", text)
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


# ── Check if line is a medicine line ─────────────────────────────
def is_medicine_line(line):
    return bool(re.match(
        r"^(?:[•\-\*·]|\d+[).\s])?\s*"
        r"(TAB|Tab|tab|TAS|Tas|CAP|Cap|SYP|Syp|INJ|Inj|"
        r"DROPS?|Drops?|OINT|SPRAY|Spray|GEL|CREAM)\s+[A-Za-z]",
        line, re.IGNORECASE
    ))


# ── Check if line contains timing info ───────────────────────────
def is_timing_line(line):
    timing_words = [
        "after", "before", "breakfast", "lunch", "dinner",
        "morning", "night", "evening", "bedtime", "daily",
        "twice", "thrice", "once", "puffs", "nostril",
        "meals", "food", "empty", "stomach", "times"
    ]
    line_lower = line.lower()
    return any(w in line_lower for w in timing_words)


# ── Main medicine extraction ──────────────────────────────────────
def extract_medicine_blocks(text):
    medicines = []
    lines     = text.split("\n")
    
    # ── Handle table format prescriptions ────────────────────────
    table_medicines  = []
    in_table         = False

    for line in lines:
        line       = line.strip()
        line_lower = line.lower()

        # Detect prescription table header
        if "medication" in line_lower and (
            "dosage" in line_lower or "duration" in line_lower
        ):
            in_table = True
            continue

        if not in_table:
            continue

        # Skip date/doctor/footer lines
        if re.match(r"\d{2}/\d{2}/\d{2}", line):
            continue
        if any(kw in line_lower for kw in [
            "electronically", "page", "signed", "ddc",
            "by dr", "dr.", "investigations", "observations",
            "notes", "advised", "clinical"
        ]):
            continue
        if not line or len(line) < 3:
            continue

        # Extract medicine name — first word group before numbers/keywords
        # Remove everything after first occurrence of digit+unit or keyword
        name_match = re.match(
            r"^([A-Za-z][A-Za-z0-9\s\-\(\)\.]+?)"
            r"(?=\s+\d|\s+(?:stat|twice|once|three|after|before|"
            r"massage|apply|tab|cap|\d))",
            line, re.IGNORECASE
        )

        if not name_match:
            # Try simpler — just take first column (before double space)
            parts = re.split(r"\s{2,}", line)
            if parts and len(parts[0]) > 2:
                name_match_text = parts[0].strip()
            else:
                continue
        else:
            name_match_text = name_match.group(1).strip()

        # Clean name
        drug_name = name_match_text
        drug_name = re.sub(
            r"^\s*(?:tab|cap|syp|inj)\s+",
            "", drug_name, flags=re.IGNORECASE
        ).strip()
        drug_name = re.sub(r"\(\d+\)\s*$", "", drug_name).strip()
        drug_name = drug_name.strip("*+× .,")

        if not drug_name or len(drug_name) < 2:
            continue

        # Skip junk lines
        junk_names = [
            "stat", "after meals", "before meals", "after food",
            "with food", "gums", "gums_", "day_", "twice daily",
            "once daily", "three times", "after", "before",
            "massage", "apply", "take", "dosage", "duration",
            "instructions", "medication", "tablet", "capsule"
        ]
        if drug_name.lower().strip() in junk_names:
            continue
        if re.match(r"Dr\.?\s+", drug_name, re.IGNORECASE):
            continue
        # Skip if too short or just special characters
        if len(drug_name) < 3 or not re.search(r"[A-Za-z]{2,}", drug_name):
            continue
        # Skip continuation lines that start with lowercase
        if drug_name[0].islower():
            continue

        # Extract dosage from line
        dose_match = re.search(
            r"\d+\.?\d*\s*(?:mg|ml|mcg|g|caps?|tabs?|puffs?)",
            line, re.IGNORECASE
        )
        dosage = dose_match.group(0) if dose_match else "As prescribed"

        # Extract duration
        dur_match = re.search(
            r"\d+\s*(?:days?|weeks?|months?)",
            line, re.IGNORECASE
        )
        duration = dur_match.group(0) if dur_match else "As directed"

        # Extract frequency and timing
        frequency = parse_frequency(line)
        timing    = parse_timing_natural(line)

        # Determine form
        form = "Tab"
        if re.match(r"^cap\s+", line, re.IGNORECASE):
            form = "Cap"
        elif "massage" in line_lower or "gum" in line_lower \
                or "paint" in line_lower or "gel" in line_lower:
            form = "Topical"
        elif re.match(r"^syp\s+", line, re.IGNORECASE):
            form = "Syp"

        table_medicines.append({
            "form":      form,
            "name":      drug_name,
            "dosage":    dosage,
            "frequency": frequency,
            "duration":  duration,
            "timing":    timing,
            "raw":       line
        })

    if table_medicines:
        return table_medicines
    
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # ── Match standard TAB/CAP/SYP line ──────────────────────
        med_match = re.match(
            r"^(?:[•\-\*·]|\d+[).\s])?\s*"
            r"(TAB|Tab|tab|TAS|Tas|CAP|Cap|SYP|Syp|Syr|INJ|Inj|"
            r"DROPS?|Drops?|OINT|Oint|SPRAY|Spray|GEL|Gel|CREAM|Cream)\s+"
            r"(.+?)$",
            line, re.IGNORECASE
        )

        # ── Match plain spray/drops without form word ─────────────
        plain_match = None
        if not med_match:
            plain_match = re.match(
                r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                r"([A-Z][A-Z0-9\s]+?(?:SPRAY|DROPS|CREAM|GEL|OINT"
                r"|NASAL\s+SPRAY))\s*[-–—]*\s*(.*?)$",
                line
            )
        plain_match = None
        if not med_match:
            plain_match = re.match(
                r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                r"([A-Z][A-Z0-9\s]+?(?:SPRAY|DROPS|CREAM|GEL|OINT|NASAL\s+SPRAY))"
                r"\s*[-–—]*\s*(\d+\s*(?:days?|weeks?|months?).*)$",
                line
            )
            if not plain_match:
                plain_match = re.match(
                    r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                    r"([A-Z][A-Z0-9\s]+?(?:SPRAY|DROPS|CREAM|GEL|OINT|NASAL\s+SPRAY))"
                    r"\s*[-–—]*\s*(.*)$",
                    line
                )
        if med_match or plain_match:
            if med_match:
                form     = med_match.group(1).title()
                raw_rest = med_match.group(2).strip()
            else:
                form      = "Spray"
                drug_name = plain_match.group(1).strip().title()
                raw_rest  = plain_match.group(2).strip()

                # For plain_match, name is already extracted
                # Skip the name_dose parsing below
                duration  = extract_duration(raw_rest)
                timing_text = raw_rest

                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if is_medicine_line(next_line):
                        break
                    if is_timing_line(next_line):
                        timing_text = next_line
                        i = j
                        break
                    break

                frequency = parse_frequency(timing_text)
                timing    = parse_timing_natural(timing_text)

                if len(drug_name) > 1:
                    medicines.append({
                        "form":      form,
                        "name":      drug_name,
                        "dosage":    "As directed",
                        "frequency": frequency,
                        "duration":  duration,
                        "timing":    timing,
                        "raw":       line
                    })
                i += 1
                continue

            # ── Parse name and dosage from raw_rest ───────────────
            # raw_rest looks like: "CEPODEM 200 ---- 15 days"
            # or: "LORFAST AM ---- 15 days"
            # or: "PANTOCID 40 -- 15 days"

            # Split on dashes separator
            raw_clean = re.sub(r"-{2,}", " ||| ", raw_rest)
            parts     = raw_clean.split("|||")
            name_part = parts[0].strip()
            rest_part = parts[1].strip() if len(parts) > 1 else ""

            # Try to extract name + dosage number from name_part
            # e.g. "CEPODEM 200" → name=CEPODEM, dose=200mg
            # e.g. "LORFAST AM"  → name=LORFAST AM, dose=As prescribed
            name_dose = re.match(
                r"^([A-Za-z][A-Za-z0-9\-\/\s]+?)\s+"
                r"(\d+\.?\d*)\s*(mg|ml|mcg|g|iu|units?|puffs?)?\s*$",
                name_part
            )

            if name_dose:
                drug_name = name_dose.group(1).strip()
                dosage_n  = name_dose.group(2)
                dosage_u  = name_dose.group(3) or "mg"
                dosage    = dosage_n + dosage_u
            else:
                drug_name = name_part.strip()
                dosage    = "As prescribed"

            # Remove any trailing dashes from drug name
            drug_name = re.sub(r"[-\s]+$", "", drug_name).strip()

            # Duration from rest_part
            duration = extract_duration(rest_part) if rest_part \
                       else "As directed"

            # ── Look ahead for timing line ────────────────────────
            timing_text = rest_part
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                # Stop if next line is a new medicine
                if is_medicine_line(next_line):
                    break
                # Use if it has timing info
                if is_timing_line(next_line):
                    timing_text = next_line
                    i = j
                    break
                break

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
                    "raw":       line
                })

        i += 1

    return medicines


# ── Extract doctor info ───────────────────────────────────────────
def extract_doctor_info(text):
    info = {}

    dr_match = re.search(
        r"(Dr\.?\s+[A-Z][A-Za-z\s\.]+?)(?:\n|M\.B|MBBS|MD|MS|$)",
        text
    )
    if dr_match:
        name = dr_match.group(1).strip().rstrip(".,")
        if len(name) > 4:
            info["doctor_name"] = name

    qual_match = re.search(
        r"(M\.B\.B\.S\..*?|M\.D\..*?|M\.S\..*?)(?:\n|$)",
        text
    )
    if qual_match:
        info["qualification"] = qual_match.group(1).strip()

    reg_match = re.search(
        r"Reg\.?\s*No\.?\s*[:\-]?\s*([A-Z]{2,5}[-\s]?\d+)",
        text, re.IGNORECASE
    )
    if reg_match:
        info["reg_number"] = reg_match.group(1).strip()

    phone_match = re.search(
        r"(\d{10}|\d{3}[-\s]\d{8}|\d{2,4}[-\s]\d{7,8})",
        text
    )
    if phone_match:
        info["phone"] = phone_match.group(1)

    clinic_match = re.search(
        r"([A-Z][A-Za-z\s]+(?:Clinic|Hospital|Centre|Center|Medical))",
        text
    )
    if clinic_match:
        info["clinic"] = clinic_match.group(1).strip()

    return info


# ── Extract patient info ──────────────────────────────────────────
def extract_patient_info(text):
    info = {}

    date_match = re.search(
        r"Date[:\s]+(\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        text, re.IGNORECASE
    )
    if date_match:
        info["date"] = date_match.group(1).strip()

    # Patient name — ALL CAPS line or after Patient/Name label
    name_patterns = [
        r"(?:Patient|Name)\s*[:\-]\s*([A-Za-z\s]+?)(?:\n|Age|$)",
        r"^([A-Z][A-Z\s]{3,30})$",
    ]
    for pat in name_patterns:
        match = re.search(pat, text, re.MULTILINE)
        if match:
            name = match.group(1).strip()
            skip = ["DR", "TAB", "CAP", "SYP", "DATE", "REG",
                    "MBBS", "TIMINGS", "ADVICE", "MADE", "WWW"]
            if not any(w in name.upper() for w in skip):
                if 3 < len(name) < 40:
                    info["name"] = name.title()
                    break

    age_match = re.search(
        r"(?:Age|AGE)\s*[:\-]?\s*(\d{1,3})\s*(?:Yrs?|Years?)?",
        text, re.IGNORECASE
    )
    if age_match:
        info["age"] = age_match.group(1)

    gender_match = re.search(r"\b(Male|Female)\b", text, re.IGNORECASE)
    if gender_match:
        info["gender"] = gender_match.group(1).title()

    combined = re.search(r"(\d{1,3})\s*/\s*(M|F)\b", text, re.IGNORECASE)
    if combined:
        info["age"]    = combined.group(1)
        info["gender"] = ("Male" if combined.group(2).upper() == "M"
                          else "Female")

    return info


# ── Extract symptoms ──────────────────────────────────────────────
def extract_symptoms(text):
    symptoms = []

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
        r"\b(Chest\s+X[- ]?ray)\b",
    ]

    for pat in patterns:
        match = re.search(pat, clean, re.IGNORECASE)
        if match:
            tests.append(match.group(1).strip())

    return list(set(tests))


# ── Main extract_entities ─────────────────────────────────────────
def extract_entities(ner_model, text):
    print("\nExtracting entities from prescription...")

    clean_text   = clean_prescription_text(text)
    pres_type    = detect_prescription_type(clean_text)
    medicines    = extract_medicine_blocks(clean_text)
    symptoms     = extract_symptoms(clean_text)
    tests        = extract_tests(clean_text)
    doctor_info  = extract_doctor_info(text)
    patient_info = extract_patient_info(text)

    # NER model for additional detection
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
        "medicines":         medicines,
        "drugs":             [m["name"] for m in medicines],
        "dosages":           [m["dosage"] for m in medicines],
        "frequencies":       [m["frequency"] for m in medicines],
        "durations":         [m["duration"] for m in medicines],
        "timings":           [m["timing"] for m in medicines],
        "symptoms":          symptoms,
        "diagnoses":         [],
        "tests":             tests,
        "doctor_info":       doctor_info,
        "patient_info":      patient_info,
        "prescription_type": pres_type
    }

    print(f"Type     : {pres_type}")
    print(f"Medicines: {len(medicines)}")
    for m in medicines:
        print(f"  {m['form']} {m['name']} {m['dosage']} "
              f"| {m['frequency']} | {m['duration']} | {m['timing']}")
    print(f"Doctor   : {doctor_info}")
    print(f"Patient  : {patient_info}")

    return entities