# openfda_api.py
# Fetches drug information from OpenFDA API — completely free, no key needed

import requests
import json
import time

BASE_URL = "https://api.fda.gov/drug"

# ─── Get drug label information ───────────────────────────────────
def get_drug_info(drug_name):
    print(f"\nFetching OpenFDA data for: {drug_name}")
    
    url    = f"{BASE_URL}/label.json"
    params = {
        "search": f"openfda.generic_name:{drug_name}",
        "limit":  1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data    = response.json()
            results = data.get('results', [])
            
            if results:
                result = results[0]
                info = {
                    'drug_name':    drug_name,
                    'purpose':      get_field(result, 'purpose'),
                    'indications':  get_field(result, 'indications_and_usage'),
                    'warnings':     get_field(result, 'warnings'),
                    'dosage':       get_field(result, 'dosage_and_administration'),
                    'side_effects': get_field(result, 'adverse_reactions'),
                    'brand_names':  result.get('openfda', {}).get('brand_name', []),
                    'source':       'OpenFDA'
                }
                print(f"✅ Found OpenFDA data for {drug_name}")
                return info
            else:
                print(f"⚠️  No OpenFDA data found for {drug_name}")
                return get_fallback_info(drug_name)
                
        else:
            print(f"⚠️  OpenFDA API error {response.status_code} for {drug_name}")
            return get_fallback_info(drug_name)
            
    except requests.exceptions.Timeout:
        print(f"⚠️  OpenFDA timeout for {drug_name}")
        return get_fallback_info(drug_name)
    except Exception as e:
        print(f"⚠️  OpenFDA error for {drug_name}: {e}")
        return get_fallback_info(drug_name)

# ─── Get drug interaction warnings ───────────────────────────────
def get_drug_interactions(drug_name):
    print(f"Checking interactions for: {drug_name}")
    
    url    = f"{BASE_URL}/event.json"
    params = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "count":  "patient.reaction.reactionmeddrapt.exact",
        "limit":  5
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data    = response.json()
            results = data.get('results', [])
            reactions = [r['term'] for r in results[:5]]
            print(f"✅ Found {len(reactions)} reactions for {drug_name}")
            return reactions
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  Interaction check error: {e}")
        return []

# ─── Helper to safely get field ──────────────────────────────────
def get_field(result, field):
    value = result.get(field, [])
    if isinstance(value, list) and value:
        # Clean up text — remove HTML tags and extra spaces
        text = value[0]
        text = text.replace('<br>', ' ').replace('<br/>', ' ')
        text = ' '.join(text.split())
        return text[:300] + "..." if len(text) > 300 else text
    return "Information not available"

# ─── Fallback info for common Indian medicines ────────────────────
def get_fallback_info(drug_name):
    # Common medicines not always in OpenFDA (Indian brands)
    fallback_db = {
        'paracetamol': {
            'purpose':      'Fever reducer and pain reliever',
            'indications':  'Used for fever, headache, body pain, toothache',
            'warnings':     'Avoid alcohol. Do not exceed 4g per day.',
            'side_effects': 'Rare at normal doses. Liver damage if overdosed.',
            'brand_names':  ['Crocin', 'Dolo', 'Calpol', 'Panadol']
        },
        'amoxicillin': {
            'purpose':      'Antibiotic for bacterial infections',
            'indications':  'Treats ear, nose, throat, skin, urinary tract infections',
            'warnings':     'Complete full course. Tell doctor if allergic to penicillin.',
            'side_effects': 'Nausea, diarrhea, rash',
            'brand_names':  ['Mox', 'Novamox', 'Amoxil']
        },
        'metformin': {
            'purpose':      'Controls blood sugar in Type 2 Diabetes',
            'indications':  'Type 2 Diabetes management',
            'warnings':     'Take with food. Monitor kidney function regularly.',
            'side_effects': 'Nausea, stomach upset, diarrhea initially',
            'brand_names':  ['Glycomet', 'Glucophage', 'Obimet']
        },
        'azithromycin': {
            'purpose':      'Antibiotic for bacterial infections',
            'indications':  'Respiratory infections, skin infections, STIs',
            'warnings':     'Tell doctor about heart conditions before taking.',
            'side_effects': 'Nausea, stomach pain, diarrhea',
            'brand_names':  ['Zithromax', 'Azee', 'Azithral']
        },
        'cetirizine': {
            'purpose':      'Antihistamine for allergies',
            'indications':  'Allergic rhinitis, urticaria, hay fever',
            'warnings':     'May cause drowsiness. Avoid driving.',
            'side_effects': 'Drowsiness, dry mouth, headache',
            'brand_names':  ['Zyrtec', 'Cetzine', 'Alerid']
        }
    }
    
    key  = drug_name.lower().strip()
    info = fallback_db.get(key, {
        'purpose':      'Please consult your doctor for details',
        'indications':  'Information not available in database',
        'warnings':     'Always follow your doctor\'s instructions',
        'side_effects': 'Consult doctor or pharmacist',
        'brand_names':  []
    })
    
    info['drug_name'] = drug_name
    info['source']    = 'Local Database'
    return info


# ─── Run test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    test_drugs = ['paracetamol', 'amoxicillin', 'metformin']
    
    all_drug_info = {}
    for drug in test_drugs:
        info = get_drug_info(drug)
        all_drug_info[drug] = info
        time.sleep(0.5)  # Be polite to the API
    
    print("\n" + "="*50)
    print("DRUG INFORMATION SUMMARY")
    print("="*50)
    for drug, info in all_drug_info.items():
        print(f"\n{drug.upper()}")
        print(f"  Purpose    : {info.get('purpose', 'N/A')[:80]}")
        print(f"  Warnings   : {info.get('warnings', 'N/A')[:80]}")
        print(f"  Brand names: {info.get('brand_names', [])}")
    
    # Save output
    import os
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/drug_info.json", "w") as f:
        json.dump(all_drug_info, f, indent=2)
    print("\n✅ Drug info saved to outputs/drug_info.json")