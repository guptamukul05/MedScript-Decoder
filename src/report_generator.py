# report_generator.py
# Combines OCR + NER + API data into a structured patient report

import json
import os
import time
from datetime import datetime
from src.openfda_api import get_drug_info, get_drug_interactions
from src.rxnorm_api  import get_complete_drug_profile

# ─── Normal ranges for report analysis ───────────────────────────
NORMAL_RANGES = {
    'hemoglobin':        {'min': 12.0,  'max': 17.0,  'unit': 'g/dL'},
    'blood_sugar':       {'min': 70.0,  'max': 100.0, 'unit': 'mg/dL'},
    'hba1c':             {'min': 4.0,   'max': 5.7,   'unit': '%'},
    'tsh':               {'min': 0.4,   'max': 4.0,   'unit': 'mIU/L'},
    'creatinine':        {'min': 0.6,   'max': 1.2,   'unit': 'mg/dL'},
    'platelet_count':    {'min': 150.0, 'max': 400.0, 'unit': 'thousand/uL'},
    'wbc':               {'min': 4.0,   'max': 11.0,  'unit': 'thousand/uL'},
    'cholesterol':       {'min': 0.0,   'max': 200.0, 'unit': 'mg/dL'},
    'triglycerides':     {'min': 0.0,   'max': 150.0, 'unit': 'mg/dL'},
    'sgpt':              {'min': 7.0,   'max': 56.0,  'unit': 'U/L'},
    'sgot':              {'min': 10.0,  'max': 40.0,  'unit': 'U/L'},
    'uric_acid':         {'min': 2.4,   'max': 7.0,   'unit': 'mg/dL'},
    'vitamin_d':         {'min': 20.0,  'max': 100.0, 'unit': 'ng/mL'},
    'vitamin_b12':       {'min': 200.0, 'max': 900.0, 'unit': 'pg/mL'},
}

# ─── Urgency level calculator ─────────────────────────────────────
def calculate_urgency(abnormal_values):
    if not abnormal_values:
        return {
            'level':  'normal',
            'color':  '🟢',
            'text':   'All Reports Normal',
            'reason': 'All values within normal range'
        }
    
    critical_params = ['hemoglobin', 'blood_sugar', 'creatinine', 'platelet_count']
    moderate_params = ['tsh', 'hba1c', 'cholesterol']
    
    has_critical = any(v['parameter'] in critical_params 
                       for v in abnormal_values)
    has_moderate = any(v['parameter'] in moderate_params 
                       for v in abnormal_values)
    
    if has_critical:
        return {
            'level':  'urgent',
            'color':  '🔴',
            'text':   'Consult Doctor Today',
            'reason': f"Critical value detected: "
                      f"{[v['parameter'] for v in abnormal_values if v['parameter'] in critical_params]}"
        }
    elif has_moderate:
        return {
            'level':  'soon',
            'color':  '🟡',
            'text':   'Consult Doctor This Week',
            'reason': f"Abnormal values need attention"
        }
    else:
        return {
            'level':  'routine',
            'color':  '🟠',
            'text':   'Routine Checkup Advised',
            'reason': 'Minor abnormalities detected'
        }

# ─── Analyze report values ────────────────────────────────────────
def analyze_report_values(report_text):
    import re
    
    abnormal  = []
    normal    = []
    
    # Extract numbers with parameter names
    patterns = {
        'hemoglobin':     r'(?:hemoglobin|hb|hgb)[:\s]+(\d+\.?\d*)',
        'blood_sugar':    r'(?:blood\s*sugar|glucose|fbs|rbs)[:\s]+(\d+\.?\d*)',
        'hba1c':          r'(?:hba1c|glycated)[:\s]+(\d+\.?\d*)',
        'tsh':            r'(?:tsh|thyroid)[:\s]+(\d+\.?\d*)',
        'creatinine':     r'(?:creatinine|creat)[:\s]+(\d+\.?\d*)',
        'platelet_count': r'(?:platelet|plt)[:\s]+(\d+\.?\d*)',
        'cholesterol':    r'(?:cholesterol|chol)[:\s]+(\d+\.?\d*)',
        'sgpt':           r'(?:sgpt|alt)[:\s]+(\d+\.?\d*)',
        'sgot':           r'(?:sgot|ast)[:\s]+(\d+\.?\d*)',
        'vitamin_d':      r'(?:vitamin\s*d|vit\s*d)[:\s]+(\d+\.?\d*)',
        'vitamin_b12':    r'(?:vitamin\s*b12|vit\s*b12)[:\s]+(\d+\.?\d*)',
    }
    
    text_lower = report_text.lower()
    
    for param, pattern in patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            value  = float(match.group(1))
            ranges = NORMAL_RANGES.get(param, {})
            
            if ranges:
                is_low  = value < ranges['min']
                is_high = value > ranges['max']
                
                entry = {
                    'parameter': param,
                    'value':     value,
                    'unit':      ranges['unit'],
                    'min':       ranges['min'],
                    'max':       ranges['max'],
                    'status':    'HIGH' if is_high else 'LOW' if is_low else 'NORMAL'
                }
                
                if is_low or is_high:
                    abnormal.append(entry)
                else:
                    normal.append(entry)
    
    return abnormal, normal

# ─── Generate medicine schedule ───────────────────────────────────
def generate_medicine_schedule(drugs, entities):
    schedule = []
    
    timing_map = {
        'od':          ['Morning'],
        'once daily':  ['Morning'],
        'bd':          ['Morning', 'Night'],
        'twice daily': ['Morning', 'Night'],
        'tds':         ['Morning', 'Afternoon', 'Night'],
        'three times': ['Morning', 'Afternoon', 'Night'],
        'qid':         ['Morning', 'Afternoon', 'Evening', 'Night'],
    }
    
    for i, drug in enumerate(drugs):
        freq     = entities['frequencies'][i] if i < len(entities['frequencies']) else 'As directed'
        dose     = entities['dosages'][i]     if i < len(entities['dosages'])     else 'As prescribed'
        duration = entities['durations'][i]   if i < len(entities['durations'])   else 'As directed'
        
        # Get timing from frequency
        timing = ['As directed by doctor']
        for key, times in timing_map.items():
            if key.lower() in freq.lower():
                timing = times
                break
        
        schedule.append({
            'medicine':  drug,
            'dosage':    dose,
            'frequency': freq,
            'timing':    timing,
            'duration':  duration,
            'with_food': True
        })
    
    return schedule

# ─── Generate full patient report ────────────────────────────────
def generate_full_report(entities, ocr_text="", report_text=""):
    print("\nGenerating patient report...")
    
    report = {
        'generated_at':  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'disclaimer':    '⚠️ This report is AI-generated. Always consult your doctor.',
        'medicines':     [],
        'tests_ordered': entities.get('tests', []),
        'symptoms':      entities.get('symptoms', []),
        'diagnoses':     entities.get('diagnoses', []),
        'report_analysis': {
            'abnormal': [],
            'normal':   []
        },
        'urgency':       {},
        'drug_interactions': []
    }
    
    # Get medicine details from APIs
    drugs = entities.get('drugs', [])
    schedule = generate_medicine_schedule(drugs, entities)
    
    for i, drug in enumerate(drugs):
        print(f"\nProcessing medicine: {drug}")
        
        # Get info from both APIs
        fda_info  = get_drug_info(drug)
        rxn_info  = get_complete_drug_profile(drug)
        reactions = get_drug_interactions(drug)
        
        medicine_entry = {
            'name':         drug,
            'dosage':       schedule[i]['dosage']    if i < len(schedule) else 'As prescribed',
            'frequency':    schedule[i]['frequency'] if i < len(schedule) else 'As directed',
            'timing':       schedule[i]['timing']    if i < len(schedule) else ['As directed'],
            'duration':     schedule[i]['duration']  if i < len(schedule) else 'As directed',
            'with_food':    True,
            'purpose':      fda_info.get('purpose',      'Consult doctor'),
            'indications':  fda_info.get('indications',  'Consult doctor'),
            'warnings':     fda_info.get('warnings',     'Follow doctor instructions'),
            'side_effects': fda_info.get('side_effects', 'Consult pharmacist'),
            'brand_names':  fda_info.get('brand_names',  []),
            'drug_class':   rxn_info.get('drug_class',   'Unknown'),
            'alternatives': rxn_info.get('alternatives', []),
            'reactions':    reactions[:3]
        }
        report['medicines'].append(medicine_entry)
        time.sleep(0.3)  # Polite API delay
    
    # Analyze uploaded reports if provided
    if report_text:
        abnormal, normal = analyze_report_values(report_text)
        report['report_analysis']['abnormal'] = abnormal
        report['report_analysis']['normal']   = normal
        report['urgency'] = calculate_urgency(abnormal)
    else:
        report['urgency'] = {
            'level': 'no_report',
            'color': '⚪',
            'text':  'No Report Uploaded',
            'reason':'Upload medical reports for urgency assessment'
        }
    
    print("\n✅ Patient report generated successfully")
    return report


# ─── Run test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test entities
    test_entities = {
        'drugs':       ['paracetamol', 'amoxicillin'],
        'dosages':     ['500mg', '250mg'],
        'frequencies': ['twice daily', 'TDS'],
        'durations':   ['5 days', '7 days'],
        'symptoms':    ['fever', 'headache'],
        'diagnoses':   [],
        'tests':       ['CBC', 'blood test']
    }
    
    # Test report text
    test_report = """
    Hemoglobin: 11.2 g/dL
    Blood Sugar (Fasting): 126 mg/dL
    Platelet Count: 180 thousand/uL
    TSH: 6.8 mIU/L
    Creatinine: 0.9 mg/dL
    """
    
    report = generate_full_report(test_entities, report_text=test_report)
    
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/patient_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*50)
    print("PATIENT REPORT SUMMARY")
    print("="*50)
    print(f"Medicines found : {len(report['medicines'])}")
    print(f"Tests ordered   : {report['tests_ordered']}")
    print(f"Symptoms        : {report['symptoms']}")
    print(f"Urgency         : {report['urgency']['color']} {report['urgency']['text']}")
    
    if report['report_analysis']['abnormal']:
        print(f"\nAbnormal values:")
        for v in report['report_analysis']['abnormal']:
            print(f"  ⚠️  {v['parameter']}: {v['value']} {v['unit']} — {v['status']}")
    
    print("\n✅ Full report saved to outputs/patient_report.json")