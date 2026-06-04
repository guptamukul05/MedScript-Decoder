import sys
sys.path.append(".")

# Simulate what the real PDF text looks like
text = """TAB CEPODEM 200 ---- 15 days
After breakfast and dinner
TAB PANTOCID 40 -- 15 days
After breakfast and dinner
TAB LORFAST AM ---- 15 days
after breakfast and dinner
CAP NATVIE 400 ---- 15 days
After dinner
FLOMIST NASAL SPRAY---- 15 days
2 puffs into each nostril twice daily"""

print("Testing fixed extraction...")
print("="*50)

# Test the fixed functions directly here
import re

def clean_prescription_text_fixed(text):
    # Remove footer patterns
    footer_patterns = [
        r"Made by Prescription Maker.*",
        r"www\..*\.com.*",
        r"digitalprescriptionmaker.*",
        r"ECG\s*/\s*NEBULISATION.*",
        r"PLEASE BRING YOUR PRESCRIPTIONS.*",
        r"Facilities For.*",
    ]
    cleaned = text
    for pat in footer_patterns:
        cleaned = re.sub(pat, "", cleaned,
                         flags=re.IGNORECASE | re.DOTALL)
    # DO NOT remove dashes here — keep them as separators
    # Just normalize multiple spaces
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()

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
    if re.search(r"twice|two\s*times|bd|b\.d\.", t):
        return ["Morning", "Night"]
    if re.search(r"once|one\s*time|od|o\.d\.", t):
        return ["Morning"]
    if re.search(r"bedtime|hs|h\.s\.", t):
        return ["At bedtime"]
    if re.search(r"sos|as\s*needed|if\s*needed", t):
        return ["As needed (SOS)"]
    return ["As directed by doctor"]

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
    if re.search(r"bedtime|hs|h\.s\.|at\s*night\s*only|after\s+dinner$", t):
        return "Once daily at bedtime"
    if re.search(r"after\s+(breakfast|lunch|dinner|meal)", t):
        meals = len(re.findall(r"(breakfast|lunch|dinner|meal)", t))
        if meals >= 3: return "Three times daily (TDS)"
        if meals == 2: return "Twice daily (BD)"
        if meals == 1: return "Once daily (OD)"
    return "As directed"

def extract_duration(text):
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

def extract_medicine_blocks_fixed(text):
    medicines = []
    lines     = [l for l in text.split("\n")]
    
    print("\nDEBUG — All lines:")
    for idx, l in enumerate(lines):
        print(f"  [{idx}] '{l}'")
    print()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        med_match = re.match(
            r"^(?:[•\-\*·]|\d+[).\s])?\s*"
            r"(TAB|Tab|tab|TAS|Tas|CAP|Cap|SYP|Syp|Syr|INJ|Inj|"
            r"DROPS?|Drops?|OINT|Oint|SPRAY|Spray|GEL|Gel|CREAM|Cream)\s+"
            r"([A-Za-z][A-Za-z0-9\-\/\s]+?)"
            r"(?:\s+(\d+\.?\d*)\s*(mg|ml|mcg|g|iu|units?|puffs?))?"
            r"(?:\s*[-–—]{1,}\s*|\s+)(.*?)$",
            line, re.IGNORECASE
        )

        plain_match = None
        if not med_match:
            plain_match = re.match(
                r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                r"([A-Z][A-Z0-9\s]+(?:SPRAY|DROPS|CREAM|GEL|OINT|NASAL))"
                r"(?:[A-Z0-9\s]*)"
                r"(?:\s*[-–—]{1,}\s*|\s+)(.*?)$",
                line
            )

        if med_match:
            print(f"  MATCH at line [{i}]: '{line}'")
            print(f"    groups: {med_match.groups()}")
            
            form      = med_match.group(1).title()
            drug_name = med_match.group(2).strip()
            dosage_n  = med_match.group(3) or ""
            dosage_u  = med_match.group(4) or ""
            rest      = med_match.group(5).strip()
            
            print(f"    drug_name='{drug_name}' dosage='{dosage_n}{dosage_u}' rest='{rest}'")
            
            # Check number at end of name
            num_match = re.search(r"^([A-Za-z][A-Za-z\-]+)\s+(\d+)\s*$", drug_name)
            if num_match:
                print(f"    Number found in name: {num_match.groups()}")
                drug_name = num_match.group(1)
                dosage    = num_match.group(2) + "mg"
            else:
                dosage = (dosage_n + dosage_u) if dosage_n else "As prescribed"
            
            # Look ahead
            timing_text = rest
            j = i + 1
            print(f"    Looking ahead from line [{j}]")
            while j < len(lines):
                next_line = lines[j].strip()
                print(f"      Checking [{j}]: '{next_line}'")
                if not next_line:
                    j += 1
                    continue
                is_next_med = re.match(
                    r"^(?:[•\-\*·]|\d+[).\s])?\s*"
                    r"(TAB|Tab|CAP|Cap|SYP|Syp|INJ|[A-Z]{3,})\s+[A-Z]",
                    next_line, re.IGNORECASE
                )
                if is_next_med:
                    print(f"      -> Next medicine found, stopping")
                    break
                print(f"      -> Using as timing: '{next_line}'")
                timing_text += " " + next_line
                i = j
                break

            print(f"    timing_text='{timing_text}'")
            
            duration  = extract_duration(timing_text + " " + rest)
            frequency = parse_frequency(timing_text)
            timing    = parse_timing_natural(timing_text)
            
            medicines.append({
                "form": form, "name": drug_name,
                "dosage": dosage, "frequency": frequency,
                "duration": duration, "timing": timing,
            })
        elif plain_match:
            print(f"  PLAIN MATCH at line [{i}]: '{line}'")
            
        i += 1
    return medicines

# Run test
cleaned  = clean_prescription_text_fixed(text)
result   = extract_medicine_blocks_fixed(cleaned)

print(f"Medicines found: {len(result)}")
for m in result:
    print(f"\n  Name      : {m['name']}")
    print(f"  Form      : {m['form']}")
    print(f"  Dosage    : {m['dosage']}")
    print(f"  Frequency : {m['frequency']}")
    print(f"  Duration  : {m['duration']}")
    print(f"  Timing    : {m['timing']}")