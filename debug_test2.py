import sys
import os
sys.path.append(".")
import fitz
import easyocr

pdf_path = "data/raw/test2.pdf"

doc  = fitz.open(pdf_path)
page = doc[0]
mat  = fitz.Matrix(2.5, 2.5)
pix  = page.get_pixmap(matrix=mat)
os.makedirs("outputs", exist_ok=True)
img_path = "outputs/test_page.png"
pix.save(img_path)
doc.close()

reader  = easyocr.Reader(['en'], gpu=False)
results = reader.readtext(img_path)

# Group text blocks by Y position into rows
# Blocks within 20px of each other are on the same row
rows = {}
for bbox, text, conf in results:
    if conf < 0.3:
        continue
    y = int(bbox[0][1])  # top-left y coordinate

    # Find existing row within 25px
    matched_row = None
    for row_y in rows:
        if abs(row_y - y) < 25:
            matched_row = row_y
            break

    if matched_row is None:
        rows[y] = []
        matched_row = y

    rows[matched_row].append({
        "text": text,
        "x":    bbox[0][0]  # left x for sorting within row
    })

# Sort rows by Y, then items within each row by X
full_text = ""
print("RECONSTRUCTED ROWS:")
print("="*60)
for row_y in sorted(rows.keys()):
    row_items = sorted(rows[row_y], key=lambda r: r["x"])
    row_text  = "  ".join([item["text"] for item in row_items])
    print(f"[y={row_y:4}] {row_text}")
    full_text += row_text + "\n"

print("="*60)

# Save
with open("outputs/extracted_text.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

# Test medicine extraction
from src.ner_pipeline import extract_medicine_blocks, clean_prescription_text
cleaned = clean_prescription_text(full_text)
meds    = extract_medicine_blocks(cleaned)
print(f"\nMedicines found: {len(meds)}")
for m in meds:
    print(f"  {m['name']} | {m['dosage']} | {m['frequency']} | {m['duration']}")