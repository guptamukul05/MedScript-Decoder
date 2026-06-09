# ocr_pipeline.py
# Handles typed PDFs perfectly, handwritten with correction step

import os
import re
import cv2
import numpy as np
from PIL import Image


# ── Extract text from PDF ─────────────────────────────────────────
def extract_from_pdf(pdf_path):
    try:
        import fitz

        doc  = fitz.open(pdf_path)
        text = ""

        # First try digital text extraction
        for page in doc:
            text += page.get_text()

        doc.close()

        # If we got meaningful text — digital PDF
        if text.strip() and len(text.strip()) > 100:
            print(f"Digital PDF — extracted {len(text)} characters")
            # Use span-based extraction for better column handling
            doc        = fitz.open(pdf_path)
            final_text = ""

            for page_num in range(len(doc)):
                page   = doc[page_num]
                blocks = page.get_text("dict")["blocks"]

                spans = []
                for block in blocks:
                    if block.get("type") == 0:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                spans.append({
                                    "text": span["text"].strip(),
                                    "x":    span["bbox"][0],
                                    "y":    span["bbox"][1],
                                })

                spans.sort(key=lambda s: (round(s["y"] / 5) * 5, s["x"]))

                line_groups = {}
                for span in spans:
                    y_key = round(span["y"] / 5) * 5
                    if y_key not in line_groups:
                        line_groups[y_key] = []
                    line_groups[y_key].append(span)

                page_text = ""
                for y_key in sorted(line_groups.keys()):
                    line_spans = sorted(
                        line_groups[y_key], key=lambda s: s["x"]
                    )
                    line_text = "  ".join(
                        s["text"] for s in line_spans if s["text"]
                    )
                    if line_text.strip():
                        page_text += line_text + "\n"

                final_text += page_text

            doc.close()
            return final_text.strip(), "typed"

        # No text layer — scanned PDF
        print("Scanned PDF detected — using OCR on images...")
        doc        = fitz.open(pdf_path)
        all_text   = ""

        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page as image at high resolution
            mat = fitz.Matrix(2.5, 2.5)  # 2.5x zoom for clarity
            pix = page.get_pixmap(matrix=mat)

            # Save temp image
            temp_img = f"outputs/temp_page_{page_num}.png"
            os.makedirs("outputs", exist_ok=True)
            pix.save(temp_img)

            # Run EasyOCR on the image
            results   = reader.readtext(temp_img)
            page_text = "\n".join([
                r[1] for r in results if r[2] > 0.3
            ])
            all_text += page_text + "\n"

            # Clean up temp file
            try:
                os.remove(temp_img)
            except Exception:
                pass

        doc.close()
        print(f"Scanned PDF OCR — extracted {len(all_text)} characters")
        return all_text.strip(), "handwritten"

    except ImportError:
        print("PyMuPDF not installed. Run: pip install pymupdf")
        return "", "unknown"
    except Exception as e:
        print(f"PDF error: {e}")
        import traceback
        traceback.print_exc()
        return "", "unknown"
# ── Preprocess image for OCR ──────────────────────────────────────
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        img = np.array(Image.open(image_path).convert("RGB"))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    if w < 1200:
        scale = 1200 / w
        img   = cv2.resize(img, None, fx=scale, fy=scale,
                           interpolation=cv2.INTER_CUBIC)

    gray     = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    thresh   = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    processed_path = image_path.rsplit(".", 1)[0] + "_processed.png"
    cv2.imwrite(processed_path, thresh)
    return processed_path


# ── OCR image with EasyOCR ────────────────────────────────────────
def ocr_image(image_path):
    try:
        import easyocr
        reader  = easyocr.Reader(["en"], gpu=False)

        # Try original first
        r1      = reader.readtext(image_path)
        text1   = "\n".join([item[1] for item in r1 if item[2] > 0.3])

        # Try preprocessed
        try:
            proc   = preprocess_image(image_path)
            r2     = reader.readtext(proc)
            text2  = "\n".join([item[1] for item in r2 if item[2] > 0.3])
        except Exception:
            text2  = ""

        text = text1 if len(text1) >= len(text2) else text2
        print(f"OCR extracted {len(text)} characters")
        return text, "handwritten"

    except Exception as e:
        print(f"OCR error: {e}")
        return "", "handwritten"


# ── Main pipeline ─────────────────────────────────────────────────
def run_ocr_pipeline(file_path):
    ext  = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text, pres_type = extract_from_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        text, pres_type = ocr_image(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        return "", "unknown"

    # Save extracted text
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)

    return text, pres_type