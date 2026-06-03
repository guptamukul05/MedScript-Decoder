# main_pipeline.py
# Connects OCR + NER + APIs into one single pipeline

import os
import json
from src.ocr_pipeline     import run_ocr_pipeline
from src.ner_pipeline     import load_ner_model, extract_entities
from src.report_generator import generate_full_report

def run_full_pipeline(prescription_image_path=None,
                      report_text=None,
                      prescription_text=None):
    
    print("\n" + "="*60)
    print("MEDSCRIPT DECODER — FULL PIPELINE")
    print("="*60)
    
    ocr_text = ""
    entities = {
        'drugs': [], 'dosages': [], 'frequencies': [],
        'durations': [], 'symptoms': [], 'diagnoses': [], 'tests': []
    }
    
    # ── Step 1: OCR if image provided ────────────────────────────
    if prescription_image_path and os.path.exists(prescription_image_path):
        print("\n[1/3] Running OCR on prescription image...")
        ocr_text = run_ocr_pipeline(prescription_image_path)
    elif prescription_text:
        print("\n[1/3] Using provided prescription text...")
        ocr_text = prescription_text
    else:
        print("\n[1/3] No prescription provided — skipping OCR")
    
    # ── Step 2: NER if text available ────────────────────────────
    if ocr_text:
        print("\n[2/3] Running NER on prescription text...")
        ner     = load_ner_model()
        entities = extract_entities(ner, ocr_text)
    else:
        print("\n[2/3] No prescription text — skipping NER")
    
    # ── Step 3: Generate report ───────────────────────────────────
    print("\n[3/3] Generating patient report...")
    report = generate_full_report(
        entities,
        ocr_text=ocr_text,
        report_text=report_text or ""
    )
    
    # Save final report
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/final_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n✅ Pipeline complete")
    print(f"✅ Report saved to outputs/final_report.json")
    return report


if __name__ == "__main__":
    # Test with prescription text only
    test_prescription = """
    Patient: fever and throat pain since 3 days
    Tab Paracetamol 500mg twice daily for 5 days
    Tab Amoxicillin 250mg TDS for 7 days
    Advised CBC blood test
    Follow up after 1 week
    """
    
    test_report = """
    Hemoglobin: 11.2 g/dL
    Blood Sugar Fasting: 126 mg/dL
    TSH: 6.8 mIU/L
    Creatinine: 0.9 mg/dL
    """
    
    report = run_full_pipeline(
        prescription_text=test_prescription,
        report_text=test_report
    )
    
    # Print summary
    print("\n" + "="*60)
    print("FINAL REPORT SUMMARY")
    print("="*60)
    print(f"Medicines  : {[m['name'] for m in report['medicines']]}")
    print(f"Tests      : {report['tests_ordered']}")
    print(f"Symptoms   : {report['symptoms']}")
    print(f"Urgency    : {report['urgency']['color']} {report['urgency']['text']}")
    
    if report['report_analysis']['abnormal']:
        print("\nAbnormal Report Values:")
        for v in report['report_analysis']['abnormal']:
            print(f"  {v['parameter']}: {v['value']} — {v['status']}")