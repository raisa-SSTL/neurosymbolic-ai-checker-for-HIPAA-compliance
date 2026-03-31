"""
explainer.py
============
WHAT THIS FILE DOES:
Takes the list of flagged violations and sends them to Groq
to get plain-English explanations for each one.
This is the "Neural" part of the neuro-symbolic system.

PSEUDO CODE:
1. Take list of violation dicts as input
2. If no Groq key available — use default descriptions as fallback
3. Format all violations into one prompt (batch = fewer API calls)
4. Send to Groq: "explain each violation in one sentence"
5. Parse response as JSON array of explanation strings
6. Attach each explanation back to its violation dict
7. Return updated violation list with explanations filled in

NOTE: If Groq API not available yet this file still works —
      it just uses the rule description as the explanation.
"""

import os
import re
import json
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Explainer ─────────────────────────────────────────────────
def explain_violations(flags: list) -> list:
    """
    Adds plain-English explanations to each violation.
    Falls back to default descriptions if Groq unavailable.
    """
    if not flags:
        return []

    # ── Fallback if no API key ────────────────────────────────
    if not GROQ_API_KEY:
        print("  GROQ_API_KEY not set — using default descriptions")
        for flag in flags:
            flag["explanation"] = flag["description"]
        return flags

    # ── Build batch prompt ────────────────────────────────────
    violations_text = "\n".join([
        f"{i+1}. Component: {f['component']} | Rule: {f['rule_id']} | Issue: {f['description']}"
        for i, f in enumerate(flags)
    ])

    prompt = f"""
You are a HIPAA compliance expert.

For each violation below write exactly ONE sentence explaining:
- What the risk is
- Which specific HIPAA safeguard is being violated
- What could happen if not fixed

Return a JSON array of strings only. One string per violation.
No other text, no markdown, no backticks.

Violations:
{violations_text}
"""

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        print(f"  Sending {len(flags)} violations to Groq for explanation...")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
        )

        raw = response.choices[0].message.content
        raw = re.sub(r"```json|```", "", raw).strip()
        explanations = json.loads(raw)

        for i, flag in enumerate(flags):
            if i < len(explanations):
                flag["explanation"] = explanations[i]
            else:
                flag["explanation"] = flag["description"]

        print(f"  Explanations received for {len(flags)} violations")

    except json.JSONDecodeError:
        print("  Could not parse Groq explanations — using defaults")
        for flag in flags:
            flag["explanation"] = flag["description"]

    except Exception as e:
        print(f"  Groq explainer error: {e} — using defaults")
        for flag in flags:
            flag["explanation"] = flag["description"]

    return flags

# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    test_flags = [
        {
            "component":   "ExternalSMSGateway",
            "rule_id":     "BAC-001",
            "description": "PHI transmitted to external service without a Business Associate Contract",
            "explanation": ""
        },
        {
            "component":   "ExternalAnalyticsSaaS",
            "rule_id":     "ENC-002",
            "description": "PHI transmitted to external service without encryption",
            "explanation": ""
        }
    ]

    result = explain_violations(test_flags)
    print("\n  Explanations:")
    for f in result:
        print(f"  {f['component']}: {f['explanation']}")
print("\nexplainer.py working")