"""
ontology.py
===========
WHAT THIS FILE DOES:
Defines all RDF classes, properties, and rule IDs used across
the entire pipeline. Everyone imports from here.
NEVER hardcode class or property names in other files.

PSEUDO CODE:
1. Define a base namespace (like a unique URL prefix)
2. Define Classes — types of things (Component, Database, ExternalService)
3. Define Properties — attributes (handles_PHI, is_External, has_BAC_Contract)
4. Define Rule IDs — names for each HIPAA rule
5. Helper functions to generate unique URIs for each component
"""




from rdflib import Namespace, URIRef

# ── Base Namespace ────────────────────────────────────────────
HIPAA = Namespace("http://hipaa-checker.org/ontology#")

# ── Classes ───────────────────────────────────────────────────
class Classes:
    Component       = HIPAA["Component"]
    Service         = HIPAA["Service"]
    API             = HIPAA["API"]
    Database        = HIPAA["Database"]
    ExternalService = HIPAA["ExternalService"]
    Storage         = HIPAA["Storage"]
    System          = HIPAA["System"]
    Violation       = HIPAA["Violation"]

# ── Properties ────────────────────────────────────────────────
class Properties:
    handles_PHI       = HIPAA["handles_PHI"]
    is_external       = HIPAA["is_External"]
    has_BAC_contract  = HIPAA["has_BAC_Contract"]
    component_type    = HIPAA["component_Type"]
    component_name    = HIPAA["component_Name"]
    has_encryption    = HIPAA["has_Encryption"]
    has_audit_log     = HIPAA["has_AuditLog"]
    sends_data_to     = HIPAA["sends_Data_To"]
    belongs_to_system = HIPAA["belongs_To_System"]
    system_name       = HIPAA["system_Name"]
    violation_rule    = HIPAA["violation_Rule"]
    violation_reason  = HIPAA["violation_Reason"]
    affects_component = HIPAA["affects_Component"]

# ── Rule IDs ──────────────────────────────────────────────────
class Rules:
    BAC_001 = "BAC-001"
    ENC_002 = "ENC-002"
    EXT_003 = "EXT-003"
    AUD_004 = "AUD-004"
    LOG_005 = "LOG-005"

    DESCRIPTIONS = {
        BAC_001: "PHI transmitted to external service without a Business Associate Contract",
        ENC_002: "PHI transmitted to external service without encryption",
        EXT_003: "External component receives PHI with no documented agreement",
        AUD_004: "PHI stored in database without audit logging enabled",
        LOG_005: "External service receives PHI with no audit trail",
    }

# ── Component Type Map ────────────────────────────────────────
COMPONENT_TYPE_MAP = {
    "Service":   Classes.Service,
    "API":       Classes.API,
    "Database":  Classes.Database,
    "External":  Classes.ExternalService,
    "Storage":   Classes.Storage,
}
DEFAULT_COMPONENT_CLASS = Classes.Component

# ── Helper Functions ──────────────────────────────────────────
def get_component_uri(system_name: str, component_name: str) -> URIRef:
    safe_system    = system_name.replace(" ", "")
    safe_component = component_name.replace(" ", "")
    return HIPAA[f"{safe_system}_{safe_component}"]

def get_system_uri(system_name: str) -> URIRef:
    return HIPAA[system_name.replace(" ", "")]

# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Namespace:", str(HIPAA))
    print("Sample class:", Classes.Database)
    print("Sample property:", Properties.handles_PHI)
    print("Sample rule:", Rules.BAC_001, "→", Rules.DESCRIPTIONS[Rules.BAC_001])
    print("Sample URI:", get_component_uri("Telemedicine Platform", "EmailService"))
    print("\n✅ ontology.py loaded successfully, All thanks to RAISA.")