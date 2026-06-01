# ocr_pipeline.py
# This file takes a prescription image and extracts text from it using EasyOCR

import easyocr
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import os

# ─── Step 1: Initialize the OCR reader ───────────────────────────────────────
# This loads the EasyOCR model — first time will download ~100MB model files
# After first run it uses cached files so it's fast
def initialize_reader():
    print("Initializing EasyOCR reader...")
    reader = easyocr.Reader(['en'], gpu=False)  # gpu=False since we have no GPU
    print("Reader initialized successfully.")
    return reader


# ─── Step 2: Load and preprocess the image ───────────────────────────────────
# Preprocessing improves OCR accuracy on handwritten text
def preprocess_image(image_path):
    print(f"Loading image from: {image_path}")
    
    # Load image using PIL
    image = Image.open(image_path)
    
    # Convert to numpy array for OpenCV processing
    img_array = np.array(image)
    
    # Convert to grayscale — removes color noise
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply thresholding — makes text sharper and clearer
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise — removes small dots and noise around text
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    
    print("Image preprocessed successfully.")
    return denoised


# ─── Step 3: Extract text from image ─────────────────────────────────────────
def extract_text(reader, image):
    print("Extracting text from image...")
    
    # EasyOCR reads the image and returns list of (bounding_box, text, confidence)
    results = reader.readtext(image)
    
    return results


# ─── Step 4: Parse and clean the results ─────────────────────────────────────
def parse_results(results):
    extracted_data = []
    
    for (bbox, text, confidence) in results:
        # Only keep results with confidence above 30%
        # Low confidence = EasyOCR is not sure about that text
        if confidence > 0.30:
            extracted_data.append({
                'text': text,
                'confidence': round(confidence * 100, 2),
                'bbox': bbox
            })
    
    return extracted_data


# ─── Step 5: Display results cleanly ─────────────────────────────────────────
def display_results(extracted_data):
    print("\n" + "="*50)
    print("EXTRACTED TEXT FROM PRESCRIPTION")
    print("="*50)
    
    full_text = ""
    for item in extracted_data:
        print(f"Text: {item['text']:<30} Confidence: {item['confidence']}%")
        full_text += item['text'] + " "
    
    print("\n" + "="*50)
    print("FULL EXTRACTED TEXT:")
    print(full_text.strip())
    print("="*50)
    
    return full_text.strip()


# ─── Step 6: Save results to output file ─────────────────────────────────────
def save_results(full_text, output_path="outputs/extracted_text.txt"):
    os.makedirs("outputs", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(full_text)
    print(f"\nResults saved to {output_path}")


# ─── Main function — runs everything ─────────────────────────────────────────
def run_ocr_pipeline(image_path):
    # Step 1
    reader = initialize_reader()
    
    # Step 2
    processed_image = preprocess_image(image_path)
    
    # Step 3
    results = extract_text(reader, processed_image)
    
    # Step 4
    extracted_data = parse_results(results)
    
    # Step 5
    full_text = display_results(extracted_data)
    
    # Step 6
    save_results(full_text)
    
    return full_text


# ─── Run this file directly ───────────────────────────────────────────────────
if __name__ == "__main__":
    image_path = "data/raw/sample_prescription.jpg"
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"ERROR: No image found at {image_path}")
        print("Please add a prescription image at data/raw/sample_prescription.jpg")
    else:
        run_ocr_pipeline(image_path)