import sys
import re
sys.path.append(".")
from src.ocr_pipeline import extract_from_pdf
from src.report_generator import analyze_report_values

# Re-extract
text, ptype = extract_from_pdf("data/raw/download.pdf")

with open("outputs/extracted_text.txt", "w", encoding="utf-8") as f:
    f.write(text)

# Find specific lines
lines = text.split("\n")
print("RDW lines:")
for i, line in enumerate(lines):
    if "rdw" in line.lower() or "distribution width" in line.lower():
        print(f"  [{i}] '{line}'")
        if i > 0: print(f"  [{i-1}] '{lines[i-1]}'")
        if i < len(lines)-1: print(f"  [{i+1}] '{lines[i+1]}'")

print("\nIgE lines:")
for i, line in enumerate(lines):
    if "ige" in line.lower() or "immunoglobulin" in line.lower():
        print(f"  [{i}] '{line}'")
        if i < len(lines)-1: print(f"  [{i+1}] '{lines[i+1]}'")

print("\nTel lines:")
for i, line in enumerate(lines):
    if "tel" in line.lower() and any(c.isdigit() for c in line):
        print(f"  [{i}] '{line}'")

abnormal, normal = analyze_report_values(text)
print(f"\nAbnormal: {len(abnormal)}")
for v in abnormal:
    print(f"  {v['parameter']}: {v['value']} {v['unit']} — {v['status']}")