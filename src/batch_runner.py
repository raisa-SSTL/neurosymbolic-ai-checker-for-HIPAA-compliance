"""
batch_runner.py
===============
Runs the neuro-symbolic HIPAA compliance pipeline across all
17 healthcare GitHub repositories.

What this file does:
1. Iterates through all 17 repos in order
2. Fetches README via scraper.py (cached — no re-fetch on retry)
3. Extracts components via Groq LLM (extractor.py)
4. Builds RDF knowledge graph per repo (graph_builder.py)
5. Runs 5 SPARQL rules per repo (rule_engine.py)
6. Explains violations via Groq (explainer.py)
7. Saves per-repo report to output/github/<repo_name>/
8. Waits between repos to respect Groq rate limits
9. Prints a final aggregate summary table

Usage:
  python src/batch_runner.py               # run all 17 repos
  python src/batch_runner.py --dry-run     # print repo list only
  python src/batch_runner.py --start 5     # resume from repo #5

Output structure:
  output/
    github/
      medplum/
        report_<timestamp>.txt
        report_<timestamp>.json
        graph.ttl
        components.json
      fhir-server/
        ...
    batch_summary.json     <- aggregate across all repos
    batch_summary.txt      <- human-readable summary table
"""

import os
import sys
import json
import time
from datetime import datetime

from src.schema        import validate_batch
from src.scraper       import fetch_readme_cached, extract_architecture_section
from src.extractor     import extract_components
from src.graph_builder import build_graph, save_graph
from src.rule_engine   import run_rules
from src.explainer     import explain_violations
from src.report        import generate_report

# ── Repo List (17 unique — #17 duplicate removed, label fixed) ─
REPOS = [
    {"id":  1, "system": "Medplum",        "url": "https://github.com/medplum/medplum"},
    {"id":  2, "system": "Medplum",        "url": "https://github.com/medplum/medplum-demo-bots"},
    {"id":  3, "system": "OpenEMR",        "url": "https://github.com/openemr/openemr"},
    {"id":  4, "system": "OpenEMR",        "url": "https://github.com/openemr/openemr-devops"},
    {"id":  5, "system": "Microsoft FHIR", "url": "https://github.com/microsoft/fhir-server"},
    {"id":  6, "system": "Microsoft FHIR", "url": "https://github.com/microsoft/fhir-server-samples"},
    {"id":  7, "system": "Microsoft FHIR", "url": "https://github.com/microsoft/healthcare-apis-samples"},
    {"id":  8, "system": "Microsoft FHIR", "url": "https://github.com/microsoft/FHIR-Converter"},
    {"id":  9, "system": "Microsoft FHIR", "url": "https://github.com/microsoft/fhir-codegen"},
    {"id": 10, "system": "Microsoft FHIR", "url": "https://github.com/microsoft/healthcare-shared-components"},
    {"id": 11, "system": "HAPI FHIR",      "url": "https://github.com/hapifhir/hapi-fhir"},
    {"id": 12, "system": "HAPI FHIR",      "url": "https://github.com/hapifhir/hapi-fhir-jpaserver-starter"},
    {"id": 13, "system": "FHIR Tools",     "url": "https://github.com/smart-on-fhir/client-js"},
    {"id": 14, "system": "FHIR Tools",     "url": "https://github.com/smart-on-fhir/client-py"},
    {"id": 15, "system": "FHIR Tools",     "url": "https://github.com/nazrulworld/fhir.resources"},
    {"id": 16, "system": "FHIR Tools",     "url": "https://github.com/google/fhir"},
    # #17 removed — duplicate of #16 (same URL, mislabelled as HAPI FHIR)
    {"id": 18, "system": "OpenEMR",        "url": "https://github.com/openemr/openemr-on-ecs"},
]
# ── Groq rate limit: max ~30 req/min on free tier
# Each repo uses 2 Groq calls (extractor + explainer)
# 15 seconds between repos = safe buffer
DELAY_BETWEEN_REPOS = 15


# ── Per-repo output dir ───────────────────────────────────────
def get_repo_output_dir(url: str) -> str:
    repo_name = url.rstrip("/").split("/")[-1].lower()
    path = f"output/github/{repo_name}"
    os.makedirs(path, exist_ok=True)
    return path


# ── Single repo pipeline ──────────────────────────────────────
def run_single_repo(repo: dict) -> dict:
    """
    Runs the full pipeline on one repo.
    Returns a result dict for the summary table.
    """
    rid     = repo["id"]
    system  = repo["system"]
    url     = repo["url"]
    repo_name = url.rstrip("/").split("/")[-1]
    out_dir = get_repo_output_dir(url)

    print(f"\n{'='*60}")
    print(f"REPO #{rid:02d} — {repo_name}  [{system}]")
    print(f"{'='*60}")

    result = {
        "id":          rid,
        "system":      system,
        "repo":        repo_name,
        "url":         url,
        "status":      "pending",
        "components":  0,
        "violations":  0,
        "flagged":     [],
        "error":       "",
        "report_path": "",
    }

    # ── Step 1: Fetch README ──────────────────────────────────
    try:
        readme = fetch_readme_cached(url)
        arch   = extract_architecture_section(readme)
    except (FileNotFoundError, ConnectionError, ValueError) as e:
        result["status"] = "readme_failed"
        result["error"]  = str(e)
        print(f"  [batch] README fetch failed: {e}")
        return result

    # ── Step 2: Extract components via Groq ──────────────────

    components = extract_components(arch, system_name=f"{system} — {repo_name}")
    if not components:
        result["status"] = "extract_failed"
        result["error"]  = "LLM returned no components"
        print(f"  [batch] Extraction returned nothing")
        return result

    result["components"] = len(components)

    # Save extracted components
    comp_path = f"{out_dir}/components.json"
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in components], f, indent=2)

    # ── Step 3: Build graph ───────────────────────────────────
    graph = build_graph(components)
    save_graph(graph, f"{out_dir}/graph.ttl")

    # ── Step 4: Run SPARQL rules ──────────────────────────────
    flags = run_rules(graph)

    # ── Step 5: Explain violations ────────────────────────────
    if flags:
        flags = explain_violations(flags)
        for flag in flags:
            if not flag.get("explanation"):
                flag["explanation"] = flag.get("description", "HIPAA violation")

    # ── Step 6: Generate report ───────────────────────────────
    report_path = generate_report(components, flags, output_dir=out_dir)

    flagged_names = sorted({f["component"] for f in flags})
    result["status"]      = "complete"
    result["violations"]  = len(flagged_names)
    result["flagged"]     = flagged_names
    result["report_path"] = report_path

    print(f"  [batch] Done — {len(components)} components, {len(flagged_names)} violations")
    return result


# ── Aggregate Summary ─────────────────────────────────────────
def save_summary(results: list):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    completed  = [r for r in results if r["status"] == "complete"]
    failed     = [r for r in results if r["status"] != "complete"]
    total_comp = sum(r["components"] for r in completed)
    total_viol = sum(r["violations"] for r in completed)

    # ── TXT summary ───────────────────────────────────────────
    lines = []
    lines.append("=" * 70)
    lines.append("BATCH COMPLIANCE SUMMARY — GITHUB REPO MODE")
    lines.append(f"Generated : {now}")
    lines.append("=" * 70)
    lines.append(f"\n{'#':<4} {'System':<20} {'Repo':<38} {'Comp':>5} {'Viol':>5} {'Status'}")
    lines.append("-" * 70)

    for r in results:
        status_str = "✓" if r["status"] == "complete" else f"✗ {r['status']}"
        lines.append(
            f"{r['id']:<4} {r['system']:<20} {r['repo']:<38} "
            f"{r['components']:>5} {r['violations']:>5}  {status_str}"
        )

    lines.append("-" * 70)
    lines.append(f"{'TOTAL':<4} {'':<20} {f'{len(completed)}/{len(results)} repos':<38} "
                 f"{total_comp:>5} {total_viol:>5}")
    lines.append("=" * 70)

    if failed:
        lines.append("\nFAILED REPOS:")
        for r in failed:
            lines.append(f"  #{r['id']} {r['repo']}: {r['error']}")

    # Violations detail
    lines.append("\n" + "=" * 70)
    lines.append("VIOLATIONS BY REPO")
    lines.append("=" * 70)
    for r in results:
        if r["violations"] > 0:
            lines.append(f"\n  #{r['id']} {r['repo']} ({r['system']}):")
            for comp in r["flagged"]:
                lines.append(f"    • {comp}")

    # SUMMARY line (for findstr)
    lines.append("\n" + "=" * 70)
    lines.append(
        f"SUMMARY: {total_viol} violation(s) across "
        f"{total_comp} components in {len(completed)} repos"
    )
    lines.append("=" * 70)

    txt_path  = "output/batch_summary.txt"
    json_path = "output/batch_summary.json"

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated":   now,
            "total_repos": len(results),
            "completed":   len(completed),
            "failed":      len(failed),
            "total_components": total_comp,
            "total_violations": total_viol,
            "results":     results,
        }, f, indent=2)

    print(f"\n  [batch] Summary TXT  → {txt_path}")
    print(f"  [batch] Summary JSON → {json_path}")
    return txt_path


# ── Main Batch Runner ─────────────────────────────────────────
def run_batch(start_from: int = 1, dry_run: bool = False):
    print("\n" + "=" * 60)
    print("BATCH RUNNER — HIPAA COMPLIANCE ACROSS 17 GITHUB REPOS")
    print("=" * 60)
    print(f"  Repos to process : {len(REPOS)}")
    print(f"  Starting from    : #{start_from}")
    print(f"  Delay between    : {DELAY_BETWEEN_REPOS}s (Groq rate limit buffer)")
    print(f"  Output dir       : output/github/")
    print(f"  Mode             : {'DRY RUN — no API calls' if dry_run else 'LIVE'}")

    if dry_run:
        print("\n  Repo list:")
        for repo in REPOS:
            repo_name = repo["url"].split("/")[-1]
            print(f"    #{repo['id']:02d} {repo['system']:<20} {repo_name}")
        return []

    os.makedirs("output/github", exist_ok=True)

    repos_to_run = [r for r in REPOS if r["id"] >= start_from]
    results      = []

    for i, repo in enumerate(repos_to_run):
        result = run_single_repo(repo)
        results.append(result)
        save_summary(results)   # Save after every repo — safe resuming

        # Rate limit buffer between repos (not after last)
        if i < len(repos_to_run) - 1:
            print(f"\n  [batch] Waiting {DELAY_BETWEEN_REPOS}s before next repo...")
            time.sleep(DELAY_BETWEEN_REPOS)

    # ── Final summary ─────────────────────────────────────────
    completed = [r for r in results if r["status"] == "complete"]
    failed    = [r for r in results if r["status"] != "complete"]

    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    print(f"  Repos completed  : {len(completed)}/{len(results)}")
    print(f"  Repos failed     : {len(failed)}")
    print(f"  Total components : {sum(r['components'] for r in completed)}")
    print(f"  Total violations : {sum(r['violations'] for r in completed)}")
    if failed:
        print(f"\n  Failed repos (retry with --start N):")
        for r in failed:
            print(f"    #{r['id']} {r['repo']}: {r['error']}")
    print("\n  To check summary:")
    print("    findstr \"SUMMARY:\" output\\batch_summary.txt")
    print("=" * 60)
    return results


# ── Entry Point ───────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("output/github", exist_ok=True)

    dry_run    = "--dry-run" in sys.argv
    start_from = 1

    for arg in sys.argv[1:]:
        if arg.startswith("--start="):
            start_from = int(arg.split("=")[1])
        elif arg.startswith("--start"):
            idx = sys.argv.index(arg)
            if idx + 1 < len(sys.argv):
                try:
                    start_from = int(sys.argv[idx + 1])
                except ValueError:
                    pass

    try:
        run_batch(start_from=start_from, dry_run=dry_run)
    except KeyboardInterrupt:
        print("\n\n  Batch interrupted. Re-run with --start N to resume.")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\nFATAL: {e}")
        traceback.print_exc()
        sys.exit(1)
