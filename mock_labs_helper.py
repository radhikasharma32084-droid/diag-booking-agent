DISPLAY_NAMES = {
    "cbc": "Complete Blood Count (CBC)",
    "vitamin_d": "Vitamin D Test",
    "vitamin_b12": "Vitamin B12 Test",
    "thyroid": "Thyroid Profile",
    "lipid": "Lipid Profile",
    "blood_sugar": "Fasting Blood Sugar",
    "hba1c": "HbA1c (Diabetes Average)",
    "lft": "Liver Function Test",
    "kft": "Kidney Function Test",
    "hemoglobin": "Hemoglobin Test",
    "urine_routine": "Urine Routine Test",
    "calcium": "Calcium Test",
    "uric_acid": "Uric Acid Test",
    "iron": "Iron Studies",
}


def test_display_name(test_key: str) -> str:
    return DISPLAY_NAMES.get(test_key, test_key)
    
