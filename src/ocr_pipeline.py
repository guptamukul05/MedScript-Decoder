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
        import fitz  # PyMuPDF
        doc  = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        if text.strip() and len(text.strip()) > 50:
            print(f"PDF text extracted: {len(text)} characters")
            return text.strip(), "typed"

        # No text layer — scanned PDF, convert to image
        print("Scanned PDF detected — converting to image for OCR")
        doc       = fitz.open(pdf_path)
        page      = doc[0]
        mat       = fitz.Matrix(2.5, 2.5)
        pix       = page.get_pixmap(matrix=mat)
        img_path  = pdf_path.replace(".pdf", "_page1.png")
        pix.save(img_path)
        doc.close()
        text, _   = ocr_image(img_path)
        return text, "handwritten"

    except ImportError:
        print("PyMuPDF not installed. Run: pip install pymupdf")
        return "", "unknown"
    except Exception as e:
        print(f"PDF error: {e}")
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