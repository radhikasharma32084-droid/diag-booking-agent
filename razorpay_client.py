"""
razorpay_client.py — Creates a Razorpay TEST MODE order.

This is the only place in the whole project that touches money, and it only
runs after the patient has explicitly confirmed the lab and price shown to
them ("bounded and gated", as Razorpay's own bar requires).

You need your OWN free Razorpay test API keys for this to work:
  1. Sign up at https://dashboard.razorpay.com/signup (free)
  2. Make sure you're in "Test Mode" (toggle top-left of the dashboard)
  3. Go to Settings -> API Keys -> Generate Test Key
  4. Put them in a .env file (see .env.example) as:
       RAZORPAY_KEY_ID=rzp_test_xxxxx
       RAZORPAY_KEY_SECRET=xxxxx

If no keys are set, this returns a clearly-labeled MOCK order instead of
crashing, so you can still demo the full flow before you've set up keys.
"""

import os
import uuid


def create_order(amount_rupees: int, receipt_note: str):
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        return {
            "mode": "MOCK (no Razorpay test keys set)",
            "order_id": f"mock_order_{uuid.uuid4().hex[:8]}",
            "amount": amount_rupees,
            "status": "created",
        }

    import razorpay

    client = razorpay.Client(auth=(key_id, key_secret))
    order = client.order.create(
        {
            "amount": amount_rupees * 100,  # Razorpay uses paise
            "currency": "INR",
            "receipt": receipt_note,
            "payment_capture": 1,
        }
    )
    return {
        "mode": "TEST MODE (real Razorpay test order)",
        "order_id": order["id"],
        "amount": amount_rupees,
        "status": order["status"],
    }
