"""
main.py
=======
WHAT THIS FILE DOES:
Orchestrates the complete neuro-symbolic HIPAA compliance pipeline.
This is the main entry point for the system.
 
NEURO-SYMBOLIC ARCHITECTURE:
  NEURO (LLM):    extractor.py + explainer.py use Groq to understand docs
  SYMBOLIC (Logic): rule_engine.py uses SPARQL for deterministic checking
  Together: accuracy + explainability
 
PSEUDO CODE:
1. Parse command line arguments
2. Determine input type (TSV or GitHub URL)
3. Load components:
   a. If TSV    → schema.py load_from_tsv()
   b. If GitHub → scraper.py + extractor.py pipeline
4. Build knowledge graph → graph_builder.py
5. Run SPARQL rules      → rule_engine.py (finds violations)
6. Add explanations      → explainer.py (makes violations understandable)
7. Generate report       → report.py (human-readable output)
8. Return results for    → evaluate.py comparison
 
USAGE:
  python src/main.py                                    # default TSV
  python src/main.py data/my_dataset.tsv               # custom TSV
  python src/main.py https://github.com/owner/repo     # live GitHub repo
 
FIX (v2): Corrected __main__ guard from `if name == "main":` 
          to `if __name__ == "__main__":`. File would silently never
          execute as a script with the original typo.
"""
 
import sys
import os
from src.schema import load_from_tsv, save_to_json, load_from_json
from src.scraper import fetch_readme_cached, extract_architecture_section
from src.extractor import extract_components
from src.graph_builder import build_graph, save_graph
from src.rule_engine import run_rules
from src.explainer import explain_violations
from src.report import generate_report
 
 
def run_pipeline(source: str, system_name: str = None):
    """
    Full neuro-symbolic pipeline from source to report.
 
    Args:
        source:      Either path to TSV file or GitHub URL
        system_name: Optional name for GitHub-based systems
 
    Returns:
        list: Violation flags for evaluation
    """
    print("\n" + "=" * 60)
    print("HIPAA COMPLIANCE CHECKER — NEURO-SYMBOLIC PIPELINE")
    print("=" * 60)
 
    components = None
 
    # ── Input: TSV Dataset ────────────────────────────────────
    if source.lower().endswith('.tsv'):
        print(f"\nMODE: TSV Dataset")
        print(f"   Loading: {source}")
 
        if not os.path.exists(source):
            print(f"\nERROR: File not found: {source}")
            print("   Please check the file path and try again.")

            return []
 
        components = load_from_tsv(source)
 
        if not components:
            print("\nERROR: No valid components found in dataset")
            print("   Check that TSV has correct column headers")
            return []
 
        print(f"   Loaded {len(components)} components from dataset")
 
    # ── Input: GitHub URL ─────────────────────────────────────
    elif source.startswith('https://github.com/') or source.startswith('http://github.com/'):
        print(f"\nMODE: GitHub Repository Analysis")
        print(f"   Fetching: {source}")
 
        try:
            readme_text = fetch_readme_cached(source)
            print(f"   README fetched ({len(readme_text)} chars)")
 
            arch_section = extract_architecture_section(readme_text)
            print(f"   Architecture section extracted ({len(arch_section)} chars)")
 
            if not system_name:
                system_name = source.rstrip('/').split('/')[-1]
 
            print(f"\nNEURO: Extracting components using Groq LLM...")
            components = extract_components(arch_section, system_name)
 
            if not components:
                print("\nERROR: LLM extraction returned no components")
                print("   Check GROQ_API_KEY in .env or try TSV mode")
                return []
 
            output_json = "output/extracted_components.json"
            save_to_json(components, output_json)
            print(f"   Extracted components saved: {output_json}")
 
        except FileNotFoundError as e:
            print(f"\nERROR: {e}")
            return []
        except ConnectionError as e:
            print(f"\nERROR: {e}")
            return []
        except Exception as e:
            print(f"\nUNEXPECTED ERROR: {e}")
            raise
 
    # ── Unknown input ─────────────────────────────────────────
    else:
        print(f"\nERROR: Invalid source: {source}")
        print("   Source must be:")
        print("   - Path to .tsv file, OR")
        print("   - GitHub URL starting with https://github.com/")
        return []
 
    # ── Validate dataset quality ──────────────────────────────
    print(f"\nVALIDATING: Dataset quality...")
 
    sample = components[0]
    missing_cols = []
    warnings = []
 
    if sample.has_encryption == "Unknown":
        missing_cols.append("Has_Encryption")
        warnings.append("Rule ENC-002 (encryption check) may not detect violations")
 
    if sample.has_audit_log == "Unknown":
        missing_cols.append("Has_AuditLog")
        warnings.append("Rules AUD-004 and LOG-005 (audit checks) may not detect violations")
 
    if missing_cols:
        print(f"\nWARNING: Dataset missing columns: {', '.join(missing_cols)}")
        for w in warnings:
            print(f"   - {w}")
        print("   Recommendation: Add these columns to dataset for full rule coverage")
    else:
        print("   All required columns present")
 
    # ── Build knowledge graph ─────────────────────────────────
    print(f"\nSYMBOLIC: Building RDF knowledge graph...")
 
    try:
        graph = build_graph(components)
        graph_path = "output/graph.ttl"
        save_graph(graph, graph_path)
        print(f"   Knowledge graph saved: {graph_path}")
    except Exception as e:
        print(f"\nERROR building knowledge graph: {e}")
        raise
 
    # ── Run SPARQL compliance rules ───────────────────────────
    print(f"\nSYMBOLIC: Running 5 HIPAA compliance rules...")
 
    try:
        flags = run_rules(graph)
    except Exception as e:
        print(f"\nERROR running SPARQL rules: {e}")
        print("   Check that property names in ontology.py match rule_engine.py")
        raise
 
    if len(flags) == 0:
        print("\nWARNING: No violations detected")
        print("   This is unexpected on synthetic dataset")
        print("   Possible causes:")
        print("   1. Dataset Violation_Expected column has no 'Yes' values")
        print("   2. Missing columns (Has_Encryption, Has_AuditLog)")
        print("   3. SPARQL property names don't match ontology.py")
 
    # ── Generate plain English explanations ──────────────────
    print(f"\nNEURO: Generating plain English explanations...")
 
    try:
        flags = explain_violations(flags)
    except Exception as e:
        print(f"\nWARNING: Explainer failed: {e}")
        print("   Continuing with default rule descriptions")
        for flag in flags:
            if not flag.get("explanation"):
                flag["explanation"] = flag.get("description", "HIPAA violation detected")
 
    # ── Generate compliance report ────────────────────────────
    print(f"\nGENERATING: Compliance report...")
 
    try:
        report_path = generate_report(components, flags)
    except Exception as e:
        print(f"\nERROR generating report: {e}")
        raise
 
    flagged_components = {f['component'] for f in flags}
 
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total components analyzed  : {len(components)}")
    print(f"Violations detected        : {len(flagged_components)}")
    print(f"Compliant components       : {len(components) - len(flagged_components)}")
    print(f"\nReport saved: {report_path}")
    print(f"\nNext step: run evaluate.py to compare against baselines")
    print("=" * 60 + "\n")
 
    return flags
 
 
def run_on_dataset(tsv_path: str = "data/Architecture_Compliance_Dataset.tsv"):
    """
    Convenience function for running on the default synthetic dataset.
 
    Args:
        tsv_path: Path to TSV dataset file
    Returns:
        list: Violation flags
    """
    print(f"\nRunning on synthetic dataset: {tsv_path}")
 
    components = load_from_tsv(tsv_path)
 
    if not components:
        print(f"\nERROR: Could not load dataset from {tsv_path}")
        print("\n   Did you:")
        print("   1. Export the Google Sheet as TSV?")
        print("      (File → Download → Tab Separated Values)")
        print("   2. Save it as 'Architecture_Compliance_Dataset.tsv'?")
        print("   3. Place it in the data/ folder?")
        return []
 
    graph   = build_graph(components)
    flags   = run_rules(graph)
    flags   = explain_violations(flags)
    generate_report(components, flags)
 
    return flags
 
 
# FIX: was `if name == "main":` — Python never executed this block
if __name__ == "__main__":
    os.makedirs("output/reports", exist_ok=True)
 
    try:
        if len(sys.argv) > 1:
            source = sys.argv[1]
 
            if source in ['--help', '-h', 'help']:
                print(__doc__)
                sys.exit(0)
 
            system_name = sys.argv[2] if len(sys.argv) > 2 else None
            run_pipeline(source, system_name)
        else:
            run_on_dataset()
 
        print("main.py execution complete")
 
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
