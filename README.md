# Diagnostic Test Booking & Price-Comparison Agent

**Track: AI Growth & Agentic Commerce — Razorpay AI Buildathon**

## The problem

Diagnostic lab pricing in India is fragmented and undiscoverable. The same
CBC test can cost ₹300 at one lab and ₹550 at another two streets away, and
there is no easy way for a patient to compare and book in one step. This
also means labs lose walk-in revenue to whichever competitor the patient
happens to call first.

## What this agent does

1. A patient types what they need in plain English (e.g. *"I need a CBC and
   Vitamin D test"*).
2. The agent checks every lab in its network, and shows which ones can do
   **all** the requested tests together, with total price and today's slot
   availability.
3. It recommends the best option — cheapest lab that actually has a slot
   today — and shows its full reasoning (audit trail).
4. If the cheapest lab has no slot today, it **gracefully falls back** to the
   next best option instead of failing.
5. Only after the patient explicitly confirms does it create a real
   Razorpay **test-mode** order — no money moves without explicit consent.

## Why this AI Judgment is deliberate

The agent uses an AI model (Claude) for exactly one job: understanding a
messy, free-text request from a human. Everything downstream — comparing
prices, ranking labs, handling the fallback, and deciding what to book — is
**plain, deterministic Python code**, not an AI model. This makes every money
decision fully explainable and auditable, which is safer and more trustworthy
than asking an LLM to "decide" what to book. If no AI key is configured at
all, the agent still works correctly using simple keyword matching — it
never silently fails.

## Architecture

```
Patient message
      │
      ▼
 nlu.py  ──(optional Claude API call)──►  extracts requested tests
      │
      ▼
 matcher.py  (100% deterministic)
   • checks every lab
   • ranks by price, tie-break by slot availability
   • falls back gracefully if top choice has no slot
   • produces a full audit trail
      │
      ▼
 Patient reviews & explicitly confirms
      │
      ▼
 razorpay_client.py  ──►  creates a Razorpay TEST MODE order
      │
      ▼
 Booking confirmation shown to patient
```

## Running it locally (Windows)

1. Install [Python](https://www.python.org/downloads/) (check "Add Python
   to PATH" during install).
2. Open this folder in a terminal (or VS Code's terminal) and run:
   ```
   pip install -r requirements.txt
   ```
3. (Optional) Copy `.env.example` to `.env` and add your own Razorpay test
   keys and/or Anthropic API key. The app works fine without either — it
   just uses the safe fallbacks described above.
4. Run the app:
   ```
   python app.py
   ```
5. Open **http://127.0.0.1:5000** in your browser.

## What broke during development, and how it was fixed

The initial ranking logic always picked the absolute cheapest lab, even when
that lab had zero slots available today — which would have meant recommending
a booking a patient couldn't actually use. Fixed by adding a fallback step:
if the cheapest option has no slot today, the agent automatically re-ranks
among labs that do, and clearly tells the patient why it changed its
recommendation.

## Data

All lab and pricing data (`mock_labs.json`) is synthetic/example data for
demo purposes.
