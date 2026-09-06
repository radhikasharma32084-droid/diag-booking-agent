from flask import Flask, request, jsonify, render_template

from nlu import extract_requested_tests, KNOWN_TESTS
from matcher import find_best_lab
from razorpay_client import create_order

app = Flask(__name__)

LAST_PROPOSAL = {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask():
    """Step 1: patient describes what they need in plain English."""
    message = request.json.get("message", "")
    requested_tests = extract_requested_tests(message)

    if not requested_tests:
        return jsonify(
            {
                "reply": (
                    "I didn't catch a specific test in that. You can name a "
                    "test directly (e.g. \"CBC\", \"thyroid\", \"sugar test\"), "
                    "or just say \"full body checkup\" if you're not sure — "
                    "I'll pick a standard set of common tests for you."
                ),
                "done": False,
            }
        )

    result = find_best_lab(requested_tests)

    if not result["success"]:
        return jsonify(
            {
                "reply": result["message"],
                "audit_trail": result["audit_trail"],
                "done": False,
            }
        )

    lab = result["chosen_lab"]
    test_names = [KNOWN_TESTS_DISPLAY(t) for t in requested_tests]

    LAST_PROPOSAL["lab"] = lab
    LAST_PROPOSAL["requested_tests"] = requested_tests
    LAST_PROPOSAL["total_price"] = result["total_price"]

    reply = (
        f"Best match: **{lab['name']}** ({lab['area']}, ⭐{lab['rating']}) — "
        f"₹{result['total_price']} for {', '.join(test_names)}."
    )
    if result["fallback_used"]:
        reply += " (Note: cheapest lab had no slots today, so I picked the next best one.)"

    return jsonify(
        {
            "reply": reply,
            "audit_trail": result["audit_trail"],
            "awaiting_confirmation": True,
            "done": False,
            "lab_card": {
                "name": lab["name"],
                "area": lab["area"],
                "rating": lab["rating"],
                "price": result["total_price"],
                "tests": test_names,
                "fallback_used": result["fallback_used"],
            },
        }
    )


@app.route("/api/confirm", methods=["POST"])
def confirm():
    """Step 2: patient explicitly confirms -> only now does money move."""
    if not LAST_PROPOSAL:
        return jsonify({"reply": "Nothing to confirm yet — ask me for a test first."})

    lab = LAST_PROPOSAL["lab"]
    total_price = LAST_PROPOSAL["total_price"]

    order = create_order(total_price, receipt_note=f"booking_{lab['id']}")

    return jsonify(
        {
            "reply": (
                f"Booked with {lab['name']} for ₹{total_price}. "
                f"Order ID: {order['order_id']} ({order['mode']})."
            ),
            "order": order,
            "done": True,
        }
    )


def KNOWN_TESTS_DISPLAY(test_key):
    from mock_labs_helper import test_display_name

    return test_display_name(test_key)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
