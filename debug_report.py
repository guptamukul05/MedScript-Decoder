import sys
sys.path.append(".")
from src.report_generator import analyze_report_values

# Read the actual extracted report text
with open("outputs/extracted_text.txt", encoding="utf-8") as f:
    text = f.read()

print("EXTRACTED TEXT (first 1000 chars):")
print("="*50)
print(text[:1000])
print("="*50)

abnormal, normal = analyze_report_values(text)
print(f"\nAbnormal values found: {len(abnormal)}")
for v in abnormal:
    print(f"  {v['parameter']}: {v['value']} {v['unit']} — {v['status']}")

print(f"\nNormal values found: {len(normal)}")
for v in normal:
    print(f"  {v['parameter']}: {v['value']} {v['unit']} — {v['status']}")