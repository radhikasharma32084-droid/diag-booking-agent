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

# Known tests the agent understands. Keys must match mock_labs.json test keys.
KNOWN_TESTS = {
    "cbc": ["cbc", "complete blood count", "blood count"],
    "vitamin_d": ["vitamin d", "vit d", "vitamin-d"],
    "thyroid": ["thyroid", "t3", "t4", "tsh"],
    "lipid": ["lipid", "cholesterol"],
    "blood_sugar": ["sugar", "glucose", "diabetes test", "blood sugar"],
}


def _keyword_fallback(message: str):
    message = message.lower()
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
        prompt = (
            f"The user wants to book diagnostic lab tests. Known test codes: "
            f"{known_list}. From this message, return ONLY a JSON array of the "
            f"matching test codes, nothing else. Message: \"{message}\""
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
