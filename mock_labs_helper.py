DISPLAY_NAMES = {
    "cbc": "Complete Blood Count (CBC)",
    "vitamin_d": "Vitamin D Test",
    "thyroid": "Thyroid Profile",
    "lipid": "Lipid Profile",
    "blood_sugar": "Fasting Blood Sugar",
}


def test_display_name(test_key: str) -> str:
    return DISPLAY_NAMES.get(test_key, test_key)
