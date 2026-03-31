"""
evaluate.py
===========
WHAT THIS FILE DOES:
Compares neuro-symbolic pipeline (main.py) against the pure LLM
baseline (baseline.py) using precision, recall, and F1-score.
 
This is the core research measurement file that proves the hypothesis:
"Neuro-symbolic AI reduces false negatives in HIPAA compliance
auditing by >90% compared to pure LLM-based systems."
 
PSEUDO CODE:
1. Load ground-truth labels from the TSV dataset (Violation_Expected column)
2. Load neuro-symbolic results from main.py output JSON
3. Load baseline results from baseline.py output JSON
4. For each system:
   a. Build predicted set and ground-truth set
   b. Compute: TP, FP, FN, TN
   c. Compute: Precision, Recall, F1
5. Print side-by-side comparison table
6. Save results to output/evaluation_results.json
7. Assert improvement hypothesis is supported
 
METRICS DEFINITIONS:
Precision = TP / (TP + FP)  — of what we flagged, how much was real?
Recall    = TP / (TP + FN)  — of real violations, how many did we catch?
F1        = 2 * P * R / (P + R) — harmonic mean
False Negative Rate = FN / (TP + FN) — violations we missed (critical for HIPAA)
 
WHY RECALL MATTERS MORE THAN PRECISION HERE:
Missing a HIPAA violation (false negative) → regulatory penalty
False alarm (false positive) → extra audit work (annoying but not illegal)
So FN reduction is the primary research metric.
"""
 
import os
import sys
import json
import glob
from typing import List, Dict, Tuple, Set
 
# ── Ground Truth Loader ───────────────────────────────────────
def load_ground_truth(tsv_path: str) -> Dict[str, str]:
    """
    Loads Violation_Expected column from TSV dataset.
    Returns dict: {component_name → "Yes" | "No"}
    """
    import csv
    ground_truth = {}
 
    try:
        with open(tsv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                name = row.get("Component_Name", "").strip()
                expected = row.get("Violation_Expected", "No").strip()
                if name:
                    ground_truth[name] = expected
        print(f"  Ground truth loaded: {len(ground_truth)} components")
        print(f"  Expected violations: {sum(1 for v in ground_truth.values() if v == 'Yes')}")
        return ground_truth
    except FileNotFoundError:
        print(f"  ERROR: TSV not found at {tsv_path}")
        return {}
 
# ── JSON Report Loader ────────────────────────────────────────
def load_flagged_from_report(report_json_path: str) -> Set[str]:
    """
    Loads a report JSON and returns set of flagged component names.
    Handles the output format from report.py
    """
    try:
        with open(report_json_path, encoding='utf-8') as f:
            data = json.load(f)
 
        # Handle report.py JSON format: {"flags": [...]}
        flags = data.get("flags", [])
        flagged = {f["component"] for f in flags if isinstance(f, dict) and "component" in f}
        print(f"  Loaded {len(flagged)} flagged components from {os.path.basename(report_json_path)}")
        return flagged
 
    except FileNotFoundError:
        print(f"  ERROR: Report not found: {report_json_path}")
        return set()
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  ERROR parsing report JSON: {e}")
        return set()
 
def find_latest_report(report_dir: str) -> str:
    """Finds the most recently generated JSON report in a directory."""
    pattern = os.path.join(report_dir, "report_*.json")
    files = glob.glob(pattern)
    if not files:
        return ""
    return max(files, key=os.path.getmtime)
 
# ── Metrics Calculator ────────────────────────────────────────
def compute_metrics(
    ground_truth: Dict[str, str],
    predicted_flagged: Set[str],
    label: str = "System"
) -> Dict:
    """
    Computes precision, recall, F1 against ground truth.
 
    Args:
        ground_truth: {component_name → "Yes" | "No"}
        predicted_flagged: set of component names flagged as violations
        label: name for this system in output
 
    Returns:
        dict with all metrics
    """
    actual_positive = {name for name, v in ground_truth.items() if v == "Yes"}
    actual_negative = {name for name, v in ground_truth.items() if v == "No"}
 
    tp = len(predicted_flagged & actual_positive)   # Correctly flagged
    fp = len(predicted_flagged & actual_negative)   # Wrongly flagged
    fn = len(actual_positive - predicted_flagged)   # Missed violations ← critical
    tn = len(actual_negative - predicted_flagged)   # Correctly clear
 
    total = len(ground_truth)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fnr       = fn / (tp + fn) if (tp + fn) > 0 else 0.0  # False Negative Rate
    accuracy  = (tp + tn) / total if total > 0 else 0.0
 
    # Which violations were missed?
    missed = actual_positive - predicted_flagged
    false_alarms = predicted_flagged & actual_negative
 
    return {
        "label":         label,
        "total":         total,
        "tp":            tp,
        "fp":            fp,
        "fn":            fn,
        "tn":            tn,
        "precision":     round(precision, 4),
        "recall":        round(recall, 4),
        "f1":            round(f1, 4),
        "fnr":           round(fnr, 4),
        "accuracy":      round(accuracy, 4),
        "missed_violations":  sorted(missed),
        "false_alarms":       sorted(false_alarms),
        "flagged_count":      len(predicted_flagged),
        "actual_violations":  len(actual_positive),
    }
 
# ── Keyword Baseline ──────────────────────────────────────────
def keyword_baseline_check(ground_truth: Dict[str, str]) -> Set[str]:
    """
    Naive keyword matching baseline — flags components whose names
    contain HIPAA-risky keywords. No LLM, no SPARQL.
 
    This is the "naive approach" for the 3-way comparison:
    Keyword → Pure LLM → Neuro-Symbolic
 
    Keywords derived from common external service naming patterns.
    """
    VIOLATION_KEYWORDS = [
        "external", "sms", "email", "cdn", "analytics", "saas",
        "notification", "gateway", "third", "cloud", "storage",
        "bi tool", "messaging", "provider", "vendor"
    ]
 
    flagged = set()
    for name in ground_truth.keys():
        name_lower = name.lower()
        if any(kw in name_lower for kw in VIOLATION_KEYWORDS):
            flagged.add(name)
 
    print(f"  Keyword baseline flagged: {len(flagged)} components")
    return flagged
 
# ── Comparison Printer ────────────────────────────────────────
def print_comparison(results: List[Dict]):
    """Prints a side-by-side comparison table."""
 
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS — NEURO-SYMBOLIC vs BASELINES")
    print("=" * 70)
    print(f"\n{'Metric':<28}", end="")
    for r in results:
        print(f"{r['label']:>14}", end="")
    print()
    print("-" * (28 + 14 * len(results)))
 
    metrics_display = [
        ("Precision",         "precision",  True),
        ("Recall",            "recall",     True),
        ("F1 Score",          "f1",         True),
        ("False Negative Rate","fnr",       False),  # lower is better
        ("Accuracy",          "accuracy",   True),
        ("True Positives",    "tp",         True),
        ("False Positives",   "fp",         False),
        ("False Negatives",   "fn",         False),
        ("True Negatives",    "tn",         True),
        ("Flagged Count",     "flagged_count", None),
        ("Actual Violations", "actual_violations", None),
    ]
 
    for display_name, key, higher_better in metrics_display:
        print(f"  {display_name:<26}", end="")
        values = [r[key] for r in results]
 
        for i, (r, v) in enumerate(zip(results, values)):
            formatted = f"{v:.4f}" if isinstance(v, float) else str(v)
 
            if higher_better is None or len(results) < 2:
                print(f"{formatted:>14}", end="")
            else:
                # Highlight best value
                if higher_better:
                    best = max(values)
                    marker = " ★" if v == best and values.count(best) == 1 else ""
                else:
                    best = min(values)
                    marker = " ★" if v == best and values.count(best) == 1 else ""
                print(f"{formatted + marker:>14}", end="")
        print()
 
    print("\n★ = best in category")
 
    # FN reduction summary (core research metric)
    if len(results) >= 2:
        print("\n" + "=" * 70)
        print("RESEARCH HYPOTHESIS: FN REDUCTION")
        print("=" * 70)
 
        neuro_sym = next((r for r in results if "Neuro" in r["label"]), None)
        baselines = [r for r in results if r != neuro_sym]
 
        if neuro_sym and baselines:
            for baseline in baselines:
                baseline_fn  = baseline["fn"]
                neuro_fn     = neuro_sym["fn"]
                if baseline_fn > 0:
                    fn_reduction = (baseline_fn - neuro_fn) / baseline_fn * 100
                    print(f"\n  {baseline['label']} missed   : {baseline_fn} violations")
                    print(f"  Neuro-Symbolic missed: {neuro_fn} violations")
                    print(f"  FN Reduction         : {fn_reduction:.1f}%")
 
                    if fn_reduction >= 90:
                        print(f"  ✅ HYPOTHESIS SUPPORTED (target: >90% reduction)")
                    elif fn_reduction >= 50:
                        print(f"  ⚠️  PARTIAL SUPPORT (target: >90%, achieved: {fn_reduction:.1f}%)")
                    else:
                        print(f"  ❌ HYPOTHESIS NOT SUPPORTED — investigate rule coverage")
                elif neuro_fn == 0 and baseline_fn == 0:
                    print(f"\n  Both systems caught all violations — check ground truth coverage")
                else:
                    print(f"\n  {baseline['label']}: 0 missed, Neuro-Symbolic: {neuro_fn} missed")
 
    # Missed violations detail
    print("\n" + "=" * 70)
    print("MISSED VIOLATIONS BREAKDOWN")
    print("=" * 70)
    for r in results:
        missed = r.get("missed_violations", [])
        if missed:
            print(f"\n  {r['label']} missed ({len(missed)}):")
            for m in missed:
                print(f"    ✗ {m}")
        else:
            print(f"\n  {r['label']}: no missed violations ")
 
    # False alarms detail
    print("\n" + "=" * 70)
    print("FALSE ALARMS BREAKDOWN")
    print("=" * 70)
    for r in results:
        fa = r.get("false_alarms", [])
        if fa:
            print(f"\n  {r['label']} false alarms ({len(fa)}):")
            for f in fa:
                print(f"    ⚠️  {f}")
        else:
            print(f"\n  {r['label']}: no false alarms ")
 
# ── Save Evaluation Results ───────────────────────────────────
def save_evaluation(results: List[Dict], output_path: str = "output/evaluation_results.json"):
    """Saves full evaluation results to JSON."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "evaluation_results": results,
            "summary": {
                r["label"]: {
                    "precision": r["precision"],
                    "recall":    r["recall"],
                    "f1":        r["f1"],
                    "fnr":       r["fnr"],
                }
                for r in results
            }
        }, f, indent=2)
    print(f"\n  Evaluation saved: {output_path}")
 
# ── Main Evaluation Runner ────────────────────────────────────
def run_evaluation(
    tsv_path:         str = "data/Architecture_Compliance_Dataset.tsv",
    neuro_report_dir: str = "output/reports",
    llm_report_dir:   str = "output/baseline",
    neuro_report_json: str = None,
    llm_report_json:   str = None,
):
    """
    Full evaluation run.
 
    Args:
        tsv_path:          Path to dataset with ground truth labels
        neuro_report_dir:  Directory of neuro-symbolic reports
        llm_report_dir:    Directory of LLM baseline reports
        neuro_report_json: Explicit path to neuro-symbolic JSON (optional)
        llm_report_json:   Explicit path to LLM baseline JSON (optional)
    """
    print("\n" + "=" * 70)
    print("EVALUATE.PY — HIPAA COMPLIANCE SYSTEM EVALUATION")
    print("=" * 70)
 
    # ── Step 1: Load ground truth ──────────────────────────────
    print(f"\nStep 1: Loading ground truth from {tsv_path}")
    ground_truth = load_ground_truth(tsv_path)
    if not ground_truth:
        print("ERROR: Cannot evaluate without ground truth. Exiting.")
        return
 
    # ── Step 2: Keyword baseline (always runs, no API needed) ──
    print(f"\nStep 2: Running keyword baseline...")
    keyword_flagged = keyword_baseline_check(ground_truth)
    keyword_metrics = compute_metrics(ground_truth, keyword_flagged, "Keyword Baseline")
 
    results = [keyword_metrics]
 
    # ── Step 3: Load LLM baseline report ──────────────────────
    print(f"\nStep 3: Loading LLM baseline results...")
    llm_json = llm_report_json or find_latest_report(llm_report_dir)
    if llm_json:
        llm_flagged = load_flagged_from_report(llm_json)
        llm_metrics = compute_metrics(ground_truth, llm_flagged, "Pure LLM Baseline")
        results.append(llm_metrics)
    else:
        print(f"  WARNING: No LLM baseline report found in {llm_report_dir}")
        print(f"  Run baseline.py first, then re-run evaluate.py")
 
    # ── Step 4: Load neuro-symbolic report ────────────────────
    print(f"\nStep 4: Loading neuro-symbolic results...")
    neuro_json = neuro_report_json or find_latest_report(neuro_report_dir)
    if neuro_json:
        neuro_flagged = load_flagged_from_report(neuro_json)
        neuro_metrics = compute_metrics(ground_truth, neuro_flagged, "Neuro-Symbolic")
        results.append(neuro_metrics)
    else:
        print(f"  WARNING: No neuro-symbolic report found in {neuro_report_dir}")
        print(f"  Run main.py first, then re-run evaluate.py")
 
    # ── Step 5: Print comparison ───────────────────────────────
    print_comparison(results)
 
    # ── Step 6: Save results ───────────────────────────────────
    save_evaluation(results)
 
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    return results
 
 
# ── CLI: Direct comparison mode ───────────────────────────────
def compare_two_json_reports(report_a: str, label_a: str,
                             report_b: str, label_b: str,
                             tsv_path: str):
    """Utility to compare any two report JSON files directly."""
    ground_truth = load_ground_truth(tsv_path)
    if not ground_truth:
        return
 
    flagged_a = load_flagged_from_report(report_a)
    flagged_b = load_flagged_from_report(report_b)
 
    metrics_a = compute_metrics(ground_truth, flagged_a, label_a)
    metrics_b = compute_metrics(ground_truth, flagged_b, label_b)
 
    print_comparison([metrics_a, metrics_b])
    save_evaluation([metrics_a, metrics_b])
 
 
# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
 
    # Allow explicit report paths via CLI args
    # Usage: python src/evaluate.py [tsv] [neuro_json] [llm_json]
    tsv    = sys.argv[1] if len(sys.argv) > 1 else "data/Architecture_Compliance_Dataset.tsv"
    neuro  = sys.argv[2] if len(sys.argv) > 2 else None
    llm    = sys.argv[3] if len(sys.argv) > 3 else None
 
    run_evaluation(
        tsv_path=tsv,
        neuro_report_json=neuro,
        llm_report_json=llm,
    )
    print("\nevaluate.py complete")
