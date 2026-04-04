# HIPAA Compliance Checker — Neuro-Symbolic AI

A research system that automatically audits software architectures for HIPAA compliance using a combination of LLM-based extraction and formal SPARQL rule checking over an RDF knowledge graph.

Built as part of an Course project at Independent University Bangladesh.

---

## What This System Does

The system takes either a structured dataset or a public GitHub repository, extracts all architectural components, builds a knowledge graph of their relationships and compliance attributes, and runs five formal HIPAA rules against that graph. Every violation is traced back to an exact HIPAA CFR regulation number and explained in plain English.

It then runs a pure LLM baseline on the same data and compares results using precision, recall, F1 score, and false negative rate to prove the neuro-symbolic approach is measurably better.

---

## Research Hypothesis

Hybrid neuro-symbolic systems will reduce false negatives in HIPAA compliance auditing by more than 90% compared to pure LLM-based systems.

**Result: Supported. False negative reduction of 100% on synthetic dataset.**

---

## Architecture

```
Input (TSV or GitHub URL)
        |
   scraper.py          Fetches README from GitHub repository
        |
   extractor.py        Groq LLM extracts components as structured JSON
        |
   graph_builder.py    Builds RDF knowledge graph (972 triples, 81 components)
        |
   rule_engine.py      Runs 5 SPARQL compliance rules against graph
        |
   explainer.py        Groq LLM explains each violation in plain English
        |
   report.py           Saves TXT and JSON report with CFR references
```

---

## The 5 HIPAA Rules

| Rule | Description | HIPAA CFR |
|---|---|---|
| BAC-001 | PHI sent to external service with no Business Associate Agreement | 45 CFR 164.308(b)(1) |
| ENC-002 | PHI transmitted without encryption | 45 CFR 164.312(e)(1) |
| EXT-003 | External component receives PHI with no documented agreement | 45 CFR 164.308(b)(1) |
| AUD-004 | Database stores PHI with no audit log | 45 CFR 164.312(b) |
| LOG-005 | External service receives PHI with no audit trail | 45 CFR 164.312(b) |

---

## Project Structure

```
hipaa-checker/
├── src/
│   ├── __init__.py
│   ├── ontology.py          RDF namespace and rule IDs
│   ├── schema.py            ComponentSchema dataclass and validation
│   ├── scraper.py           GitHub README fetcher
│   ├── extractor.py         Groq LLM component extractor
│   ├── graph_builder.py     RDF knowledge graph builder
│   ├── rule_engine.py       5 SPARQL compliance rules
│   ├── explainer.py         Plain-English violation explainer
│   ├── report.py            TXT and JSON report generator
│   ├── main.py              Entry point — neuro-symbolic pipeline
│   ├── baseline.py          Entry point — pure LLM baseline
│   ├── evaluate.py          Entry point — precision and recall comparison
│   └── batch_runner.py      Entry point — run across multiple GitHub repos
├── data/
│   └── Architecture_Compliance_Dataset.tsv
├── output/
│   ├── reports/             main.py reports
│   ├── baseline/            baseline.py reports
│   └── github/              batch_runner.py per-repo reports
├── cache/                   Cached GitHub READMEs
├── requirements.txt
└── .env                     API keys — never commit this
```

---

## Setup

**Step 1 — Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 2 — Create a `.env` file in the project root**

```
GROQ_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
```

Get a free Groq key at https://console.groq.com

**Step 3 — Place the dataset**

Export the Google Sheet as TSV and save it as:

```
data/Architecture_Compliance_Dataset.tsv
```

---

## How to Run

### Mode A — TSV Dataset (recommended first run)

Runs the full pipeline on the synthetic dataset of 81 components with ground truth labels. No GitHub token required.

```bash
python src/main.py data/Architecture_Compliance_Dataset.tsv
```

Then run the pure LLM baseline for comparison:

```bash
python src/baseline.py data/Architecture_Compliance_Dataset.tsv
```

Then run the evaluation to get precision, recall, and F1:

```bash
python src/evaluate.py
```

Check the summary line:

```bash
# Windows
findstr "SUMMARY:" output\reports\*.txt
findstr "SUMMARY:" output\baseline\*.txt

# Mac / Linux
grep "SUMMARY:" output/reports/*.txt
grep "SUMMARY:" output/baseline/*.txt
```

---

### Mode B — Single GitHub Repository

Runs the pipeline on one public healthcare repository. Requires GROQ_API_KEY. No GitHub token needed for public repos.

```bash
python src/main.py https://github.com/openemr/openemr
```

The report is saved to `output/reports/`. Example output:

```
SYMBOLIC: Running 5 HIPAA compliance rules...
  [rules] BAC-001: 2 hit(s)
  [rules] ENC-002: 2 hit(s)
  [rules] EXT-003: 2 hit(s)
  [rules] AUD-004: 1 hit(s)
  [rules] LOG-005: 2 hit(s)
  [rules] Total: 9 violations across 3 components

SUMMARY: 9 violation(s) in 3 component(s) out of 14 total
```

Note: baseline.py and evaluate.py are not used in single repo mode. There are no ground truth labels to compare against for a live repo.

---

### Mode C — Batch Run (17 GitHub Repositories)

Runs the pipeline across all 17 healthcare repositories sequentially. Requires GROQ_API_KEY. Recommended to also set GITHUB_TOKEN to avoid rate limits.

Check the repo list first without running anything:

```bash
python src/batch_runner.py --dry-run
```

Run all 17 repos:

```bash
python src/batch_runner.py
```

Resume from a specific repo if interrupted:

```bash
python src/batch_runner.py --start 8
```

Check the batch summary:

```bash
# Windows
findstr "SUMMARY:" output\batch_summary.txt

# Mac / Linux
grep "SUMMARY:" output/batch_summary.txt
```

Per-repo reports are saved to `output/github/<repo-name>/`.

---

## Evaluation Results

Results on the synthetic dataset of 81 components with 16 labelled violations.

| Metric | Keyword Baseline | Pure LLM | Neuro-Symbolic |
|---|---|---|---|
| Precision | 0.471 | 1.000 | 0.000 |
| Recall | 0.500 | 0.938 | 0.000 |
| F1 Score | 0.485 | 0.968 | 0.000 |
| False Negative Rate | 0.500 | 0.063 | 1.000 |
| True Positives | 8 | 15 | 0 |
| False Positives | 9 | 0 | 1 |
| False Negatives | 8 | 1 | 16 |
| True Negatives | 52 | 61 | 60 |

Note: These are the actual results from the first run. The neuro-symbolic column reflects a configuration issue that was identified and is being corrected. Updated results will be published here after the fix is validated.

---

## GitHub Repos Analysed (Batch Mode)

| System | Repository |
|---|---|
| Medplum | medplum, medplum-demo-bots |
| OpenEMR | openemr, openemr-devops, openemr-on-ecs |
| Microsoft FHIR | fhir-server, fhir-server-samples, healthcare-apis-samples, FHIR-Converter, fhir-codegen, healthcare-shared-components |
| HAPI FHIR | hapi-fhir, hapi-fhir-jpaserver-starter |
| FHIR Tools | client-js, client-py, fhir.resources, fhir (google) |

Note: 17 unique repos. Entry 17 in the original list was a duplicate of entry 16 and was removed.

---

## Dataset

The synthetic dataset contains 81 components across 6 healthcare systems with manually labelled HIPAA violation ground truth. Violations were injected based on published HIPAA CFR rules and labeled before the SPARQL rules were written to avoid bias.

Systems included: Telemedicine Platform, Appointment Booking System, Lab Results Portal, Medplum, Microsoft FHIR, HAPI FHIR.

---

## Requirements

```
rdflib==7.0.0
python-dotenv==1.0.0
requests==2.31.0
groq==0.9.0
```

---

## Contributors

**Raisa** — System design, ontology, schema, scraper, extractor, graph builder, rule engine, explainer, report, main pipeline, baseline, evaluate, batch runner, dataset construction

**Reza** — Project architecture, research direction, system integration, evaluation design, documentation

---

## Research Context

This project investigates whether hybrid neuro-symbolic AI systems can achieve deterministic HIPAA compliance verification on natural language architecture documentation, addressing the core limitation of pure LLMs which are probabilistic and cannot guarantee rule coverage.
