# ner_pipeline.py
# Loads PubMedBERT and extracts medical entities from prescription text

import json
import os
import re
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# ─── Load label info ──────────────────────────────────────────────
def load_label_info():
    with open("results/metrics/final_summary.json", "r") as f:
        summary = json.load(f)
    print(f"✅ Best model: {summary['best_model']} — F1: {summary['best_f1']}")
    return summary

# ─── Load PubMedBERT NER model ────────────────────────────────────
def load_ner_model():
    print("Loading PubMedBERT NER model...")
    model_name = "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model     = AutoModelForTokenClassification.from_pretrained(model_name)
    
    ner_pipeline = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=-1  # CPU
    )
    print("✅ NER model loaded")
    return ner_pipeline

# ─── Extract entities from text ──────────────────────────────────
def extract_entities(ner_pipeline, text):
    print(f"\nExtracting entities from text...")
    print(f"Input text: {text}\n")
    
    results = ner_pipeline(text)
    
    entities = {
        'drugs':      [],
        'dosages':    [],
        'frequencies':[],
        'durations':  [],
        'symptoms':   [],
        'diagnoses':  [],
        'tests':      [],
        'raw':        results
    }
    
    # Pattern matching for common prescription patterns
    # Drug dosage patterns like 500mg, 250mg, 10ml
    dosage_pattern    = re.compile(r'\b\d+\s*(?:mg|ml|mcg|g|iu|units?)\b', re.IGNORECASE)
    # Frequency patterns like twice daily, TDS, OD, BD
    frequency_pattern = re.compile(
        r'\b(?:once|twice|thrice|1|2|3)\s*(?:daily|a day|times?(?:\s*a\s*day)?)'
        r'|\b(?:OD|BD|TDS|QID|SOS|PRN|HS|AC|PC)\b', re.IGNORECASE
    )
    # Duration patterns like 5 days, 2 weeks, 1 month
    duration_pattern  = re.compile(
        r'\b\d+\s*(?:day|days|week|weeks|month|months)\b', re.IGNORECASE
    )
    # Test patterns
    test_pattern      = re.compile(
        r'\b(?:CBC|MRI|CT|X-?ray|ECG|EEG|blood\s+test|urine\s+test'
        r'|HbA1c|thyroid|lipid\s+profile|LFT|KFT|RFT|USG|sonography)\b',
        re.IGNORECASE
    )
    # Symptom patterns
    symptom_pattern   = re.compile(
        r'\b(?:fever|pain|cough|cold|headache|vomiting|nausea|diarrhea'
        r'|fatigue|weakness|swelling|infection|inflammation|bleeding)\b',
        re.IGNORECASE
    )

    # Extract using patterns
    entities['dosages']     = list(set(dosage_pattern.findall(text)))
    entities['frequencies'] = list(set(frequency_pattern.findall(text)))
    entities['durations']   = list(set(duration_pattern.findall(text)))
    entities['tests']       = list(set(test_pattern.findall(text)))
    entities['symptoms']    = list(set(symptom_pattern.findall(text)))

    # Extract drug names from NER model results
    for entity in results:
        label = entity.get('entity_group', entity.get('entity', ''))
        word  = entity.get('word', '').strip()
        score = entity.get('score', 0)

        if score > 0.7:
            if any(x in label.upper() for x in ['CHEM', 'DRUG', 'B-C', 'I-C']):
                if word not in entities['drugs']:
                    entities['drugs'].append(word)
            elif any(x in label.upper() for x in ['DIS', 'DISEASE', 'B-D', 'I-D']):
                if word not in entities['diagnoses']:
                    entities['diagnoses'].append(word)

    print("✅ Entities extracted:")
    for key, values in entities.items():
        if key != 'raw' and values:
            print(f"   {key:<12}: {values}")

    return entities


# ─── Run test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test with a sample prescription text
    sample_text = """
    Patient has fever and headache.
    Tab Paracetamol 500mg twice daily for 5 days.
    Tab Amoxicillin 250mg TDS for 7 days.
    Syp Benadryl 10ml BD for 3 days.
    Advised CBC and blood test.
    Follow up after 1 week.
    """

    summary     = load_label_info()
    ner         = load_ner_model()
    entities    = extract_entities(ner, sample_text)

    # Save output
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/ner_output.json", "w") as f:
        json.dump({k: v for k, v in entities.items() if k != 'raw'}, f, indent=2)
    print("\n✅ NER output saved to outputs/ner_output.json")