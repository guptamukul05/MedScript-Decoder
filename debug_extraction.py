import sys
sys.path.append(".")
from src.ner_pipeline import extract_medicine_blocks, clean_prescription_text

# Read the actual extracted text from the PDF
with open("outputs/extracted_text.txt", encoding="utf-8") as f:
    text = f.read()

print("RAW EXTRACTED TEXT:")
print("="*50)
print(text)
print("="*50)

cleaned = clean_prescription_text(text)
print("\nCLEANED TEXT:")
print("="*50)
print(cleaned)
print("="*50)

result = extract_medicine_blocks(cleaned)
print(f"\nMedicines found: {len(result)}")
for m in result:
    print(f"  {m['name']} | {m['dosage']} | {m['frequency']} | {m['timing']}")