import sys
import re
sys.path.append(".")
from src.ocr_pipeline import extract_from_pdf
from src.report_generator import analyze_report_values

# Re-extract with new method
text, ptype = extract_from_pdf("data/raw/download.pdf")

# Save for inspection
with open("outputs/extracted_text.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("FIRST 2000 CHARS:")
print("="*50)
print(text[:2000])
print("="*50)

abnormal, normal = analyze_report_values(text)
print(f"\nAbnormal: {len(abnormal)}")
for v in abnormal:
    print(f"  {v['parameter']}: {v['value']} {v['unit']} — {v['status']}")

print(f"\nNormal: {len(normal)}")
for v in normal:
    print(f"  {v['parameter']}: {v['value']} {v['unit']} — {v['status']}")
    
lines = report_text.split("\n")
for i, line in enumerate(lines):
    if "rdw" in line.lower() or "distribution width" in line.lower():
        print(f"[{i}] '{line}'")
    if "ige" in line.lower() or "immunoglobulin" in line.lower():
        print(f"[{i}] '{line}'")
    if "tel" in line.lower() and "49" in line:
        print(f"TEL LINE [{i}] '{line}'")