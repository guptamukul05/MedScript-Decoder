import sys
sys.path.append(".")

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

from src.ner_pipeline import extract_medicine_blocks, clean_prescription_text

cleaned = clean_prescription_text(text)
result  = extract_medicine_blocks(cleaned)

print(f"Medicines found: {len(result)}")
for m in result:
    print(f"\n  Name      : {m['name']}")
    print(f"  Dosage    : {m['dosage']}")
    print(f"  Frequency : {m['frequency']}")
    print(f"  Duration  : {m['duration']}")
    print(f"  Timing    : {m['timing']}")