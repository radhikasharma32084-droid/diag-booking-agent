"""
nlu.py — Understands what the patient typed.

Design choice (worth mentioning in your pitch):
We ONLY use the AI model for the fuzzy part of the problem — reading a human's
free-text request and figuring out which tests they mean. Everything AFTER
that (comparing labs, picking the winner, booking, paying) is 100% deterministic
Python logic, so it can be audited and explained line by line.

If no ANTHROPIC_API_KEY is set, we fall back to simple keyword matching so the
demo still works out of the box — the agent never silently fails.
"""

import os
import json
import re

# Known individual tests. Keys must match mock_labs.json test keys.
KNOWN_TESTS = {
    "cbc": ["cbc", "complete blood count", "blood count"],
    "vitamin_d": ["vitamin d", "vit d", "vitamin-d"],
    "vitamin_b12": ["vitamin b12", "vit b12", "b12"],
    "thyroid": ["thyroid", "t3", "t4", "tsh"],
    "lipid": ["lipid", "cholesterol"],
    "blood_sugar": ["fasting sugar", "fasting glucose", "fasting blood sugar", "fbs", "sugar test", "sugar", "glucose", "diabetes test"],
    "hba1c": ["hba1c", "hb a1c", "diabetes average", "a1c"],
    "lft": ["lft", "liver function", "liver test"],
    "kft": ["kft", "kidney function", "kidney test", "renal function"],
    "hemoglobin": ["hemoglobin", "haemoglobin", "hb test"],
    "urine_routine": ["urine test", "urine routine", "urinalysis"],
    "calcium": ["calcium"],
    "uric_acid": ["uric acid", "gout test"],
    "iron": ["iron test", "iron studies", "ferritin"],
}

# Bundled "checkup" packages — for patients who don't know individual test
# names and just want a general wellness screen. Each maps to a fixed set of
# individual tests, so the deterministic matcher/booking logic downstream
# never has to change — a package is just a shortcut for picking several
# known tests at once.
CHECKUP_PACKAGES = {
    "full_body": {
        "aliases": [
            "full body checkup", "full body check up", "full body", "fullbody",
            "general checkup", "general check up", "health checkup",
            "health check up", "routine checkup", "master health checkup",
            "complete checkup", "complete body checkup", "basic checkup",
            "wellness checkup", "annual checkup",
        ],
        "tests": ["cbc", "blood_sugar", "lipid", "lft", "kft", "thyroid", "hemoglobin"],
    },
    "diabetes": {
        "aliases": ["diabetes checkup", "diabetes package", "diabetic checkup", "sugar checkup"],
        "tests": ["blood_sugar", "hba1c"],
    },
}


def _keyword_fallback(message: str):
    message = message.lower()

    # Check checkup packages first — a package match takes priority over
    # individual test aliases, since "full body checkup" would otherwise
    # match nothing (no single test is literally called that).
    for package in CHECKUP_PACKAGES.values():
        if any(alias in message for alias in package["aliases"]):
            return package["tests"]

    found = []
    for test_key, aliases in KNOWN_TESTS.items():
        if any(alias in message for alias in aliases):
            found.append(test_key)
    return found


def extract_requested_tests(message: str):
    """
    Returns a list of test keys (e.g. ["cbc", "vitamin_d"]) requested in the
    patient's message.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        # Deterministic fallback — no API key configured.
        return _keyword_fallback(message)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        known_list = ", ".join(KNOWN_TESTS.keys())
        packages_note = (
            "If the user asks for a general 'full body checkup' or 'health "
            "checkup' rather than naming specific tests, return this bundle: "
            "cbc, blood_sugar, lipid, lft, kft, thyroid, hemoglobin."
        )
        prompt = (
            f"The user wants to book diagnostic lab tests. Known test codes: "
            f"{known_list}. {packages_note} From this message, return ONLY a "
            f"JSON array of the matching test codes, nothing else. "
            f"Message: \"{message}\""
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        text = re.sub(r"^```json|```$", "", text).strip()
        parsed = json.loads(text)
        valid = [t for t in parsed if t in KNOWN_TESTS]
        return valid if valid else _keyword_fallback(message)
    except Exception:
        # Any API problem -> fall back safely rather than crash the booking flow.
        return _keyword_fallback(message)
