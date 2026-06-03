# rxnorm_api.py
# Fetches drug details from RxNorm API — free, no key needed

import requests
import json

BASE_URL = "https://rxnav.nlm.nih.gov/REST"

# ─── Get RxNorm ID for a drug ─────────────────────────────────────
def get_rxcui(drug_name):
    url    = f"{BASE_URL}/rxcui.json"
    params = {"name": drug_name, "search": 1}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data  = response.json()
            rxcui = data.get('idGroup', {}).get('rxnormId', [])
            if rxcui:
                print(f"✅ RxNorm ID for {drug_name}: {rxcui[0]}")
                return rxcui[0]
    except Exception as e:
        print(f"⚠️  RxNorm ID error for {drug_name}: {e}")
    return None

# ─── Get drug class/category ──────────────────────────────────────
def get_drug_class(drug_name):
    rxcui = get_rxcui(drug_name)
    if not rxcui:
        return {"drug_class": "Unknown", "drug_name": drug_name}
    
    url = f"{BASE_URL}/rxclass/class/byRxcui.json"
    params = {"rxcui": rxcui, "relaSource": "ATC"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data    = response.json()
            classes = data.get('rxclassDrugInfoList', {}).get('rxclassDrugInfo', [])
            if classes:
                drug_class = classes[0].get('rxclassMinConceptItem', {}).get('className', 'Unknown')
                print(f"✅ Drug class for {drug_name}: {drug_class}")
                return {
                    "drug_name":  drug_name,
                    "drug_class": drug_class,
                    "rxcui":      rxcui
                }
    except Exception as e:
        print(f"⚠️  Drug class error for {drug_name}: {e}")
    
    return {"drug_name": drug_name, "drug_class": "Unknown", "rxcui": rxcui}

# ─── Get related drugs (alternatives) ────────────────────────────
def get_related_drugs(drug_name):
    rxcui = get_rxcui(drug_name)
    if not rxcui:
        return []
    
    url    = f"{BASE_URL}/related.json"
    params = {"rxcui": rxcui, "tty": "IN"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data     = response.json()
            concepts = data.get('relatedGroup', {}).get('conceptGroup', [])
            related  = []
            for group in concepts:
                for concept in group.get('conceptProperties', []):
                    related.append(concept.get('name', ''))
            return related[:3]
    except Exception as e:
        print(f"⚠️  Related drugs error: {e}")
    return []

# ─── Get complete drug profile ────────────────────────────────────
def get_complete_drug_profile(drug_name):
    print(f"\nFetching RxNorm profile for: {drug_name}")
    
    drug_class   = get_drug_class(drug_name)
    related      = get_related_drugs(drug_name)
    
    profile = {
        'drug_name':     drug_name,
        'rxcui':         drug_class.get('rxcui'),
        'drug_class':    drug_class.get('drug_class', 'Unknown'),
        'alternatives':  related,
        'source':        'RxNorm'
    }
    
    print(f"✅ RxNorm profile complete for {drug_name}")
    return profile


# ─── Run test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    test_drugs = ['paracetamol', 'amoxicillin']
    
    for drug in test_drugs:
        profile = get_complete_drug_profile(drug)
        print(f"\n{drug.upper()} Profile:")
        print(f"  Drug Class  : {profile['drug_class']}")
        print(f"  Alternatives: {profile['alternatives']}")