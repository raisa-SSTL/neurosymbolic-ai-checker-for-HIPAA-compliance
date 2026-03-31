"""
schema.py
=========
WHAT THIS FILE DOES:
Defines the exact structure of a component as it moves through
the pipeline. Validates and cleans data at every stage.

PSEUDO CODE:
1. Define ComponentSchema dataclass with all fields and safe defaults
2. normalize_yes_no() — converts "yes/YES/true/1" all to "Yes"
3. normalize_component_type() — converts "microservice" to "Service" etc
4. validate_component() — takes raw dict, returns clean ComponentSchema
5. validate_batch() — validates a list of raw dicts
6. load_from_tsv() — reads the TSV dataset file
7. save_to_json() / load_from_json() — handoff format between phases
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json, csv, os

# ── Valid Values ──────────────────────────────────────────────
VALID_COMPONENT_TYPES = {"Service", "API", "Database", "External", "Storage"}
VALID_YES_NO          = {"Yes", "No", "Unknown", "N/A"}
VALID_YES_NO_ONLY     = {"Yes", "No", "Unknown"}
VALID_BAC_VALUES      = {"Yes", "No", "N/A"}

# ── Core Data Class ───────────────────────────────────────────
@dataclass
class ComponentSchema:
    component_name:     str
    system_name:        str   = "Unknown System"
    component_id:       str   = ""
    component_type:     str   = "Service"
    handles_phi:        str   = "Unknown"
    is_external:        str   = "No"
    has_bac_contract:   str   = "N/A"
    has_encryption:     str   = "Unknown"
    has_audit_log:      str   = "Unknown"
    sends_data_to:      List[str] = field(default_factory=list)
    notes:              str   = ""
    violation_expected: str   = "No"
    extraction_status:  str   = "Extracted"

    def to_dict(self):
        return asdict(self)
    def is_violation_candidate(self):
        return self.handles_phi == "Yes" and self.is_external == "Yes"

# ── Normalizers ───────────────────────────────────────────────
def normalize_yes_no(value: str, allowed: set = None) -> str:
    if allowed is None:
        allowed = VALID_YES_NO
    if not isinstance(value, str):
        return "Unknown"
    v = value.strip().lower()
    if v in {"yes", "true", "1", "y"}:       result = "Yes"
    elif v in {"no", "false", "0", "n"}:     result = "No"
    elif v in {"n/a", "na", "none"}:         result = "N/A"
    else:                                     result = "Unknown"
    return result if result in allowed else "Unknown"

def normalize_component_type(value: str) -> str:
    if not isinstance(value, str):
        return "Service"
    v = value.strip().lower()
    if v in {"service", "microservice", "worker", "processor"}:  return "Service"
    elif v in {"api", "rest api", "graphql", "gateway"}:         return "API"
    elif v in {"database", "db", "datastore", "nosql"}:          return "Database"
    elif v in {"external", "third-party", "saas"}:               return "External"
    elif v in {"storage", "blob", "s3", "object storage"}:       return "Storage"
    elif v in {"framework", "persistence", "security",
               "integration", "observability", "compliance",
               "performance", "background", "ops", "dev ux"}:    return "Service"
    else:                                                          return "Service"

# ── Validator ─────────────────────────────────────────────────
def validate_component(raw: dict, index: int = 0) -> Optional[ComponentSchema]:
    if not isinstance(raw, dict):
        return None

    name = str(raw.get("component_name", raw.get("Component_Name", ""))).strip()
    if not name:
        name = f"UnknownComponent_{index}"

    component_type = normalize_component_type(
        raw.get("component_type", raw.get("Component_Type", "Service"))
    )
    handles_phi = normalize_yes_no(
        raw.get("handles_phi", raw.get("Handles_PHI", "Unknown")),
        VALID_YES_NO_ONLY
    )
    is_external = normalize_yes_no(
        raw.get("is_external", raw.get("Is_External", "No")),
        VALID_YES_NO_ONLY
    )
    if component_type == "External":
        is_external = "Yes"

    has_bac = normalize_yes_no(
        raw.get("has_bac_contract", raw.get("Has_BAC_Contract", "N/A")),
        VALID_BAC_VALUES
    )
    if is_external == "No":
        has_bac = "N/A"

    raw_sends = raw.get("sends_data_to", raw.get("Sends_Data_To", []))
    if isinstance(raw_sends, str):
        sends = [s.strip() for s in raw_sends.split(",") if s.strip()]
    elif isinstance(raw_sends, list):
        sends = [str(s).strip() for s in raw_sends if s]
    else:
        sends = []

    violation_expected = normalize_yes_no(
        str(raw.get("violation_expected", raw.get("Violation_Expected", "No"))),
        {"Yes", "No", "Unknown"}
    )

    return ComponentSchema(
        component_name     = name,
        system_name        = str(raw.get("system_name", raw.get("System", "Unknown System"))).strip(),
        component_id       = str(raw.get("component_id", raw.get("Component_ID", ""))).strip(),
        component_type     = component_type,
        handles_phi        = handles_phi,
        is_external        = is_external,
        has_bac_contract   = has_bac,
        has_encryption     = normalize_yes_no(raw.get("has_encryption", raw.get("Has_Encryption", "Unknown")), VALID_YES_NO_ONLY),
        has_audit_log      = normalize_yes_no(raw.get("has_audit_log", raw.get("Has_AuditLog", "Unknown")), VALID_YES_NO_ONLY),
        sends_data_to      = sends,
        notes              = str(raw.get("notes", raw.get("Notes", ""))).strip()[:300],
        violation_expected = violation_expected if violation_expected != "Unknown" else "No",
        extraction_status  = str(raw.get("extraction_status", raw.get("Extraction_Status", "Extracted"))).strip(),
    )

def validate_batch(raw_list: list) -> List[ComponentSchema]:
    if not isinstance(raw_list, list):
        return []
    results = []
    skipped = 0
    for i, raw in enumerate(raw_list):
        v = validate_component(raw, index=i)
        if v:
            results.append(v)
        else:
            skipped += 1
    if skipped:
        print(f"  Skipped {skipped} invalid rows")
    print(f"  Validated {len(results)} components")
    return results

# ── TSV Loader ────────────────────────────────────────────────
def load_from_tsv(filepath: str) -> List[ComponentSchema]:
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
        print(f"  Loaded {len(rows)} rows from {filepath}")
        return validate_batch(rows)
    except FileNotFoundError:
        print(f"  ERROR: File not found: {filepath}")
        return []
# ── JSON Save/Load ────────────────────────────────────────────
def save_to_json(components: List[ComponentSchema], output_path: str):
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in components], f, indent=2)
    print(f"  Saved {len(components)} components to {output_path}")

def load_from_json(filepath: str) -> List[ComponentSchema]:
    try:
        with open(filepath, encoding="utf-8") as f:
            raw_list = json.load(f)
        return validate_batch(raw_list)
    except FileNotFoundError:
        print(f"  ERROR: File not found: {filepath}")
        return []

# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    test = {
        "component_name": "EmailService",
        "system_name": "Telemedicine Platform",
        "component_type": "Service",
        "handles_phi": "Yes",
        "is_external": "No",
        "sends_data_to": ["ExternalSMSGateway"],
    }
    result = validate_component(test)
    print(f"Name: {result.component_name}")
    print(f"PHI: {result.handles_phi}, External: {result.is_external}, BAC: {result.has_bac_contract}")
    print(f"Violation candidate: {result.is_violation_candidate()}")
    print("\n✅ schema.py loaded successfully, RAISA DID IT AGAIN!")
