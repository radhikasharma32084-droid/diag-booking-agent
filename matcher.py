"""
matcher.py — The bounded, explainable decision engine.

Given a list of requested test keys, this module:
  1. Finds every lab that can fulfil ALL requested tests.
  2. Ranks eligible labs by total price (cheapest first), using today's
     slot availability as a tie-breaker.
  3. Falls back gracefully to the next-best lab if the top choice has no
     slots today ("one failure handled gracefully" requirement).
  4. Returns a full audit trail explaining exactly why each lab was
     included, excluded, or chosen.

No AI is used here on purpose — ranking a known list of numbers doesn't need
a language model, it needs correct arithmetic. That's the "AI Judgment"
principle: use AI for the fuzzy part (nlu.py), use plain code for the exact part.
"""

import json
import os

LABS_PATH = os.path.join(os.path.dirname(__file__), "mock_labs.json")


def load_labs():
    with open(LABS_PATH) as f:
        return json.load(f)


def find_best_lab(requested_tests):
    labs = load_labs()
    audit = []
    eligible = []

    for lab in labs:
        missing = [t for t in requested_tests if t not in lab["tests"]]
        if missing:
            audit.append(
                f"❌ {lab['name']}: excluded — doesn't offer {', '.join(missing)}."
            )
            continue

        total_price = sum(lab["tests"][t]["price"] for t in requested_tests)
        has_slot_today = len(lab.get("slots_today", [])) > 0
        eligible.append(
            {
                "lab": lab,
                "total_price": total_price,
                "has_slot_today": has_slot_today,
            }
        )
        slot_note = (
            f"slots today: {', '.join(lab['slots_today'])}"
            if has_slot_today
            else "no slots today"
        )
        audit.append(
            f"✅ {lab['name']}: can do all requested tests — total ₹{total_price}, {slot_note}."
        )

    if not eligible:
        return {
            "success": False,
            "audit_trail": audit,
            "message": "No lab currently offers all the requested tests together.",
        }

    # Rank: cheapest first; among equal price, prefer one with a slot today.
    eligible.sort(key=lambda x: (x["total_price"], not x["has_slot_today"]))

    chosen = eligible[0]
    fallback_used = False

    if not chosen["has_slot_today"] and len(eligible) > 1:
        # Graceful fallback: cheapest has no slot today -> try next best that does.
        with_slot = [e for e in eligible if e["has_slot_today"]]
        if with_slot:
            audit.append(
                f"⚠️ Cheapest option ({chosen['lab']['name']}) has no slots today — "
                f"falling back to next best lab with an available slot."
            )
            chosen = with_slot[0]
            fallback_used = True

    result = {
        "success": True,
        "chosen_lab": chosen["lab"],
        "total_price": chosen["total_price"],
        "fallback_used": fallback_used,
        "audit_trail": audit,
    }
    return result
