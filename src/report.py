"""
report.py
=========
WHAT THIS FILE DOES:
Takes the component list and violation flags and generates
a human-readable compliance report. Saves as both .txt and .json.
Each violation is traced back to its exact HIPAA CFR regulation
number so the output is auditable and legally referenced.
PSEUDO CODE:
Take all_components list and flags list as input
Get set of flagged component names for quick lookup
Build text report:
a. Header with timestamp
b. One line per component: Compliant or VIOLATION
c. Detailed violation section for each violation showing:
Component name
Rule ID
HIPAA CFR reference number from CFR_REFERENCES map
Plain English explanation
d. Summary line: X violations in Y components
Save .txt file for humans
Save .json file for evaluation and precision recall calculation
Return path to txt report
"""

import os
import json
import time
from datetime import datetime
from src.schema import ComponentSchema

CFR_REFERENCES = {
    "BAC-001": "45 CFR 164.308(b)(1) — Business Associate Contracts",
    "ENC-002": "45 CFR 164.312(e)(1) — Transmission Security",
    "EXT-003": "45 CFR 164.308(b)(1) — Business Associate Contracts",
    "AUD-004": "45 CFR 164.312(b) — Audit Controls",
    "LOG-005": "45 CFR 164.312(b) — Audit Controls",
}

def generate_report(
    all_components: list,
    flags: list,
    output_dir: str = "output/reports"
) -> str:
    # Fix: Validate output_dir
    if not output_dir:
        output_dir = "output/reports"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Fix: Single timestamp for consistency + uniqueness
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000}"
    
    # Fix: Validate flags structure
    flagged_names = {f.get("component", "Unknown") for f in flags if isinstance(f, dict) and "component" in f}
    
    lines = []
    lines.append("=" * 60)
    lines.append("HIPAA COMPLIANCE VALIDATION REPORT")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)
    lines.append("\nCOMPONENT STATUS")
    lines.append("-" * 60)

    for comp in all_components:
        if isinstance(comp, ComponentSchema):
            name = comp.component_name or "Unknown"  # Fix: Handle None
        elif isinstance(comp, dict):
            name = comp.get("component_name", "Unknown")
        else:
            continue
        
        status = "VIOLATION" if name in flagged_names else "Compliant"
        lines.append(f"{status:<12} {name}")

    if flags:
        lines.append("\n" + "=" * 60)
        lines.append("VIOLATION DETAILS")
        lines.append("=" * 60)
        
        for f in flags:
            if not isinstance(f, dict):
                continue
            
            # Fix: Validate all required fields
            component = f.get("component", "Unknown")
            rule_id = f.get("rule_id", "UNKNOWN")
            reason = f.get("explanation") or f.get("description") or "No description provided"
            
            lines.append(f"\nComponent : {component}")
            lines.append(f"Rule      : {rule_id}")
            lines.append(f"HIPAA Ref : {CFR_REFERENCES.get(rule_id, 'See HIPAA Security Rule')}")
            lines.append(f"Reason    : {reason}")

    lines.append("\n" + "=" * 60)
    # Fix: Correct violation count
    lines.append(f"SUMMARY: {len(flags)} violation(s) in {len(flagged_names)} component(s) out of {len(all_components)} total")
    lines.append("=" * 60)

    txt_path  = f"{output_dir}/report_{timestamp}.txt"
    json_path = f"{output_dir}/report_{timestamp}.json"

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated":  now.isoformat(),
            "total":      len(all_components),
            "violations": len(flags),
            "components_flagged": len(flagged_names),
            "flags":      flags,
        }, f, indent=2)

    print(f"\n  Report saved: {txt_path}")
    print(f"  JSON saved:   {json_path}")
    # Removed: Terminal flooding print
    
    return txt_path
