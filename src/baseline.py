"""
baseline.py
===========
WHAT THIS FILE DOES:
Pure LLM baseline for comparison with neuro-symbolic pipeline.
Uses ONLY Groq LLM with no knowledge graph or SPARQL rules.
This demonstrates the research hypothesis:
 
  "Neuro-symbolic AI (symbolic rules + LLM) catches violations
  that pure LLM misses due to probabilistic nature."
 
COMPARISON:
  main.py     = NEURO + SYMBOLIC (LLM + SPARQL rules)
  baseline.py = NEURO only (LLM alone)
  evaluate.py computes precision/recall for both
PSEUDO CODE:
1. Load components from TSV
2. Format components as JSON
3. Build prompt with 5 HIPAA rules explicitly stated
4. Send to Groq: "Find all violations of these rules"
5. Parse LLM response (handle messy JSON)
6. Convert to standard violation format
7. Generate report in output/baseline/ directory
8. Return violations for evaluate.py to compare
 
EXPECTED OUTCOME:
  LLM will find SOME violations (it's not useless)
  LLM will MISS violations that SPARQL catches (probabilistic nature)
  LLM may FLAG non-violations (false positives / hallucinations)
  This proves symbolic rules provide deterministic accuracy
 
FIX (v2): Corrected `if name == "main":` → `if __name__ == "__main__":`
          Also: Moved Groq client creation inside baseline_check()
          instead of at module level to avoid import-time failures.
"""
 
import os
import re
import json
import sys
import time
from dotenv import load_dotenv
load_dotenv()
 
from src.schema import load_from_tsv
from src.report import generate_report
from src.ontology import Rules
 
# ── API Key Check ─────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
 
if not GROQ_API_KEY:
    print("\nERROR: GROQ_API_KEY not found in .env file")
    print("   Baseline requires Groq API for LLM-only comparison")
    print("   Get free key from: https://console.groq.com")
    sys.exit(1)
 
try:
    from groq import Groq
except ImportError:
    print("\nERROR: groq package not installed")
    print("   Run: pip install groq")
    sys.exit(1)
 
# ── Prompt ────────────────────────────────────────────────────
BASELINE_PROMPT = """You are a HIPAA compliance auditor with expertise in healthcare software architecture.
 
Your task: Analyze the following software components and identify ALL HIPAA violations.
 
HIPAA RULES TO CHECK:
BAC-001: PHI transmitted to external service without Business Associate Contract
   → If component handles PHI AND is_external=Yes AND has_bac_contract=No → VIOLATION
 
ENC-002: PHI transmitted to external service without encryption
   → If component handles PHI AND is_external=Yes AND has_encryption=No → VIOLATION
 
EXT-003: External component receives PHI with no documented agreement
   → If component_type=External AND handles PHI AND has_bac_contract=No → VIOLATION
 
AUD-004: PHI stored in database without audit logging
   → If component_type=Database AND handles PHI AND has_audit_log=No → VIOLATION
 
LOG-005: External service receives PHI with no audit trail
   → If is_external=Yes AND handles PHI AND has_audit_log=No → VIOLATION
 
COMPONENTS TO ANALYZE:
{components_json}
 
RETURN FORMAT:
Return ONLY a valid JSON array. No markdown, no backticks, no explanation.
[
  {{
    "component": "ComponentName",
    "rule_id": "BAC-001",
    "description": "Brief description",
    "explanation": "One sentence explaining risk"
  }}
]
 
If no violations found: return []
 
CRITICAL: Return ONLY the JSON array. Nothing else.
"""
 
 
# ── Baseline Check ────────────────────────────────────────────
def baseline_check(components: list, max_retries: int = 3) -> list:
    """
    Pure LLM compliance check with no symbolic rules.
 
    Args:
        components:  List of ComponentSchema objects
        max_retries: Number of retry attempts for API calls
 
    Returns:
        list: Violation dicts in standard format
    """
    # FIX: Create Groq client inside function (not at module level)
    # Module-level client creation fails if key changes or is temporarily missing
    client = Groq(api_key=GROQ_API_KEY)
 
    print(f"\nBASELINE: Pure LLM compliance check")
    print(f"   Using: Groq llama-3.3-70b-versatile")
    print(f"   Components: {len(components)}")
 
    components_data = []
    for c in components:
        components_data.append({
            "component_name":  c.component_name,
            "component_type":  c.component_type,
            "handles_phi":     c.handles_phi,
            "is_external":     c.is_external,
            "has_bac_contract":c.has_bac_contract,
            "has_encryption":  c.has_encryption,
            "has_audit_log":   c.has_audit_log,
            "sends_data_to":   c.sends_data_to,
            "notes":           c.notes[:100] if c.notes else ""
        })
 
    components_json = json.dumps(components_data, indent=2)
    prompt = BASELINE_PROMPT.format(components_json=components_json)
 
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n   API call attempt {attempt}/{max_retries}...")
 
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000,
            )
 
            raw_response = response.choices[0].message.content
            print(f"   LLM response received ({len(raw_response)} chars)")
 
            try:
                flags = parse_llm_response(raw_response)
                print(f"   Parsed {len(flags)} violations from LLM")
                return flags
 
            except ValueError as e:
                print(f"\nWARNING: Could not parse LLM response: {e}")
                if attempt < max_retries:
                    print(f"   Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"\nERROR: Failed after {max_retries} attempts to parse response")
                    return []
 
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                print(f"\nRate limit hit. Waiting 60s...")
                time.sleep(60)
            elif attempt < max_retries:
                print(f"\nAttempt {attempt} failed: {e}. Retrying in 5s...")
                time.sleep(5)
            else:
                print(f"\nERROR: API failed after {max_retries} attempts: {e}")
                raise
 
    return []
 
 
# ── Response Parser ───────────────────────────────────────────
def parse_llm_response(raw_text: str) -> list:
    """Parse LLM response — handle markdown fences and malformed JSON."""
    text = raw_text.strip()
 
    # Strip markdown code fences
    text = re.sub(r'^```(?:json)?', '', text, flags=re.MULTILINE).strip()
    text = re.sub(r'```$', '', text).strip()
 
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # FIX: Non-greedy match to avoid consuming too much
        match = re.search(r'\[[\s\S]*?\]', text)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                raise ValueError("JSON array found but is malformed")
        else:
            raise ValueError("No JSON array found in LLM response")
 
    if not isinstance(data, list):
        raise ValueError(f"Expected list, got {type(data).__name__}")
 
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each violation must be a JSON object")
 
        # FIX: Validate non-empty required fields
        if not item.get("component"):
            raise ValueError("Missing or empty 'component' field in violation")
        if not item.get("rule_id"):
            raise ValueError("Missing or empty 'rule_id' field in violation")
 
        # Fill missing optional fields gracefully
        if "description" not in item:
            item["description"] = Rules.DESCRIPTIONS.get(
                item["rule_id"], "HIPAA violation"
            )
        if "explanation" not in item:
            item["explanation"] = item["description"]
 
    return data
 
 
# ── Main Runner ───────────────────────────────────────────────
def run_baseline(tsv_path: str = "data/Architecture_Compliance_Dataset.tsv"):
    """Run pure LLM baseline and generate report."""
    print("\n" + "=" * 60)
    print("BASELINE: PURE LLM COMPLIANCE CHECK")
    print("=" * 60)
    print("\nThis is the baseline for research comparison.")
    print("Uses ONLY Groq LLM (no knowledge graph, no SPARQL).")
    print("Expected: LLM will miss some violations SPARQL catches.")
 
    print(f"\nLoading: {tsv_path}")
    if not os.path.exists(tsv_path):
        print(f"\nERROR: File not found: {tsv_path}")
        return []
 
    components = load_from_tsv(tsv_path)
    if not components:
        print("\nERROR: No components loaded")
        return []
 
    print(f"   Loaded {len(components)} components")
 
    flags = baseline_check(components)
 
    print(f"\nGenerating baseline report...")
    flagged = {f['component'] for f in flags}
    report_path = generate_report(components, flags, output_dir="output/baseline")
 
    print("\n" + "=" * 60)
    print("BASELINE COMPLETE")
    print("=" * 60)
    print(f"Components analyzed  : {len(components)}")
    print(f"Violations by LLM    : {len(flagged)}")
    print(f"Compliant            : {len(components) - len(flagged)}")
    print(f"\nReport saved: {report_path}")
    print("\nNext: Run evaluate.py to compare with main.py")
    print("="*60 + "\n")
 
    return flags
 
 
# FIX: was `if name == "main":` — Python never executed this block
if __name__ == "__main__":
    os.makedirs("output/baseline", exist_ok=True)
 
    try:
        tsv_path = sys.argv[1] if len(sys.argv) > 1 else "data/Architecture_Compliance_Dataset.tsv"
        run_baseline(tsv_path)
        print("baseline.py complete")
 
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
