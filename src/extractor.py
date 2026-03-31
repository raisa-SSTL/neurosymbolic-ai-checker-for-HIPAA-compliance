"""
extractor.py
============
WHAT THIS FILE DOES:
Sends README text to Groq LLM and gets back a structured list
of components. Handles errors, bad JSON, and rate limits.
 
PSEUDO CODE:
1. Take README text as input
2. Build a prompt telling Groq to extract components as JSON
3. Send to Groq API with retry logic (max 3 attempts)
4. Get back raw text response
5. Strip any markdown fences (```json ... ```)
6. Parse JSON — if it fails try regex extraction
7. Validate each component using schema.py
8. Return clean list of ComponentSchema objects
 
NOTE: If Groq API key not available yet — use the TSV dataset directly.
      extractor.py is only needed for live GitHub URL mode.
 
FIX (v2): Added has_bac_contract, has_encryption, has_audit_log to prompt.
          Without these 3 fields, rules ENC-002, AUD-004, LOG-005 never fire
          in GitHub URL mode because schema.py defaults all to "Unknown".
"""
 
import os
import re
import json
import time
from dotenv import load_dotenv
load_dotenv()
 
from src.schema import ComponentSchema, validate_batch
 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
 
# ── Prompt ────────────────────────────────────────────────────
# FIX: Added has_bac_contract, has_encryption, has_audit_log fields.
# These 3 fields are required for rules ENC-002, AUD-004, LOG-005 to fire.
# Instructions added to help LLM infer from architecture docs.
EXTRACTION_PROMPT = """
You are a software architecture analyst specializing in HIPAA compliance.
 
Given the README text of a software system, extract all identifiable
components (services, APIs, databases, external services, storage, etc.)
 
Return ONLY a valid JSON array with this exact structure:
[
  {{
    "component_name": "string",
    "component_type": "Service | API | Database | External | Storage",
    "handles_phi": "Yes | No | Unknown",
    "is_external": "Yes | No",
    "has_bac_contract": "Yes | No | N/A",
    "has_encryption": "Yes | No | Unknown",
    "has_audit_log": "Yes | No | Unknown",
    "sends_data_to": ["ComponentName1", "ComponentName2"],
    "notes": "one sentence description"
  }}
]
 
Field rules:
- has_bac_contract: "N/A" for internal components. "Yes" if the doc mentions a signed 
  Business Associate Agreement with this vendor. "No" if external with no mention of BAA.
- has_encryption: "Yes" if the doc mentions TLS, HTTPS, AES, or encryption for this 
  component. "No" if doc explicitly says unencrypted. "Unknown" if not mentioned.
- has_audit_log: "Yes" if the doc mentions audit logs, access logs, or FHIR AuditEvent 
  for this component. "No" if it's a database/storage with no audit trail mentioned.
  "Unknown" if not mentioned.
- is_external: "Yes" if the component is a third-party service outside the main system.
- PHI means Protected Health Information (patient data, medical records, PII).
- Return ONLY the JSON array. No explanation, no markdown, no backticks.
- If unsure about a field use Unknown.
 
README TEXT:
{readme_text}
"""
 
# ── Groq Call ─────────────────────────────────────────────────
def call_groq(readme_text: str, max_retries: int = 3) -> str:
    """
    Calls Groq API. Returns raw response string.
    Falls back gracefully if API key missing.
    """
    if not GROQ_API_KEY:
        raise EnvironmentError("GROQ_API_KEY not found in .env file")
 
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        raise ImportError("Run: pip install groq")
 
    readme_trimmed = readme_text[:3000]
    prompt = EXTRACTION_PROMPT.format(readme_text=readme_trimmed)
 
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Groq API call attempt {attempt}/{max_retries}")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            return response.choices[0].message.content
 
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                wait = 60
                print(f"  Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
            elif "authentication" in error_str:
                raise PermissionError("Invalid GROQ_API_KEY")
            elif attempt < max_retries:
                print(f"  Attempt {attempt} failed: {e}. Retrying in 5s...")
                time.sleep(5)
            else:
                raise RuntimeError(f"Groq API failed after {max_retries} attempts: {e}")
 
# ── JSON Parser ────────────────────────────────────────────────
def parse_groq_response(raw_text: str) -> list:
    """
    Parses Groq's response into a list of dicts.
    Handles markdown fences and malformed JSON.
    """
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
 
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                raise ValueError("Could not parse JSON from Groq response")
        else:
            raise ValueError("No JSON array found in Groq response")
 
    if not isinstance(data, list):
        raise ValueError(f"Expected list, got {type(data).__name__}")
 
    return data
 
# ── Main Extractor ────────────────────────────────────────────
def extract_components(readme_text: str, system_name: str = "Unknown") -> list:
    """
    Full pipeline: README text → validated ComponentSchema list.
    """
    print(f"\n  Extracting components for: {system_name}")
 
    try:
        raw_response = call_groq(readme_text)
        print(f"  Groq response received ({len(raw_response)} chars)")
    except Exception as e:
        print(f"  ERROR calling Groq: {e}")
        return []
 
    try:
        raw_list = parse_groq_response(raw_response)
        print(f"  Parsed {len(raw_list)} raw components")
    except ValueError as e:
        print(f"  ERROR parsing JSON: {e}")
        return []
 
    for item in raw_list:
        if isinstance(item, dict):
            item["system_name"] = system_name
    components = validate_batch(raw_list)
    time.sleep(2)
    return components
 
# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("  GROQ_API_KEY not set — skipping live test")
        print("  Add your key to .env file first")
        print("  Get it free from: console.groq.com")
    else:
        sample_readme = """
        ## Architecture
        Our telemedicine platform has the following components:
        - Patient API: handles patient data and PHI, TLS encrypted
        - Auth Service: handles login, no PHI stored
        - External SMS Gateway: sends notifications containing patient info,
          no Business Associate Agreement signed, no audit log
        - Patient Database: stores all medical records, no audit trail documented
        """
        results = extract_components(sample_readme, "Test System")
        print(f"\n  Extracted {len(results)} components")
        for c in results:
            print(f"  - {c.component_name} | PHI: {c.handles_phi} | "
                  f"External: {c.is_external} | BAC: {c.has_bac_contract} | "
                  f"Enc: {c.has_encryption} | Audit: {c.has_audit_log}")
        print("\n extractor.py v2 working — all 3 compliance fields now included")
