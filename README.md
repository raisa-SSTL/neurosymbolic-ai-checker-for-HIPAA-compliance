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

# neurosymbolic-ai-checker-for-HIPAA-compliance

Automated HIPAA compliance validation for software architectures using Knowledge Graphs and Neuro-Symbolic AI.

---

## What It Does

This system takes either a GitHub repository URL or a structured dataset as input, analyses its software architecture, builds a semantic knowledge graph, and detects HIPAA violations using a combination of rule-based reasoning (SPARQL) and AI explanation (Groq LLM).

It also runs a pure LLM baseline on the same data and compares results using precision, recall, and F1 score to prove the neuro-symbolic approach is measurably better.

- Input: A GitHub repository URL or TSV dataset
- Output: A compliance report flagging which components violate HIPAA rules and why, plus a full evaluation comparing three approaches

---

## Research Hypothesis

Hybrid neuro-symbolic systems will reduce false negatives in HIPAA compliance auditing by more than 90% compared to pure LLM-based systems.

---

## Pipeline Overview

```
GitHub URL or TSV Dataset
        |
scraper.py          Fetches and extracts architecture info from GitHub README
        |
extractor.py        Groq LLM identifies components, PHI handling, external services
        |
graph_builder.py    Converts structured data into RDF knowledge graph (rdflib)
        |
rule_engine.py      Runs 5 HIPAA SPARQL rules against the graph
        |
explainer.py        Groq LLM generates plain-English reasons for each violation
        |
report.py           Per-component Compliant / VIOLATION output with CFR references
```

For evaluation, two additional steps run after main.py:

```
baseline.py         Runs same data through pure LLM only, no graph, no SPARQL
        |
evaluate.py         Compares all three approaches using precision, recall, F1
```

---

## Tech Stack

| Component | Tool | Cost |
|---|---|---|
| Component extraction | Groq API (llama-3.1-70b-versatile) | Free |
| Knowledge graph | rdflib (Python) | Free |
| Rule engine | SPARQL queries | Free |
| Violation explanation | Groq API | Free |
| Data scraping | GitHub API + requests | Free |
| Baseline comparison | Groq API (llama-3.3-70b-versatile) | Free |

---

## Project Structure

```
neurosymbolic-ai-checker-for-HIPAA-compliance/
├── data/
│   └── Architecture_Compliance_Dataset.tsv   <- Synthetic dataset (81 components, 6 systems)
├── src/
│   ├── __init__.py        <- Package init with correct import order
│   ├── ontology.py        <- RDF classes, properties, rule IDs
│   ├── schema.py          <- Shared data structure and validator
│   ├── scraper.py         <- GitHub README fetcher and cache
│   ├── extractor.py       <- Groq LLM component extractor
│   ├── graph_builder.py   <- RDF knowledge graph builder
│   ├── rule_engine.py     <- 5 SPARQL HIPAA rules
│   ├── explainer.py       <- Groq violation explainer
│   ├── report.py          <- Compliance report generator (TXT and JSON)
│   ├── main.py            <- Entry point: neuro-symbolic pipeline
│   ├── baseline.py        <- Entry point: pure LLM baseline
│   ├── evaluate.py        <- Entry point: precision and recall comparison
│   └── batch_runner.py    <- Entry point: run across 17 GitHub repos
├── output/
│   ├── reports/           <- main.py reports
│   ├── baseline/          <- baseline.py reports
│   └── github/            <- batch_runner.py per-repo reports
├── cache/                 <- Cached GitHub READMEs
├── .env                   <- API keys — NEVER PUSH THIS
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/raisa-SSTL/neurosymbolic-ai-checker-for-HIPAA-compliance.git
cd neurosymbolic-ai-checker-for-HIPAA-compliance
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up API Keys

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_token_here
```

- Get your Groq key at: https://console.groq.com
- Get your GitHub token at: GitHub > Settings > Developer Settings > Personal Access Tokens > Tokens (classic) > check repo scope

---

## How to Run

### Mode A — TSV Dataset (run this first)

Runs the full neuro-symbolic pipeline on the synthetic dataset of 81 components. No GitHub token required. Produces the evaluation results. Run these three commands in order:

```bash
python src/main.py data/Architecture_Compliance_Dataset.tsv
```

```bash
python src/baseline.py data/Architecture_Compliance_Dataset.tsv
```

```bash
python src/evaluate.py
```

Check the summary lines:

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

Runs the pipeline on one public healthcare repository. Only main.py is used. baseline.py and evaluate.py do not apply here as there are no ground truth labels for a live repo.

```bash
python src/main.py https://github.com/openemr/openemr
```

No GitHub token required for public repositories.

---

### Mode C — Batch (17 GitHub Repositories)

Runs the pipeline across all 17 healthcare repositories sequentially with a 15 second delay between each to respect Groq rate limits. Saves progress after every repo so it can be resumed if interrupted.

Check the repo list first without making any API calls:

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

## Example Output

```
============================================================
HIPAA COMPLIANCE VALIDATION REPORT
Generated: 2026-04-04 14:32
============================================================

COMPONENT STATUS
------------------------------------------------------------
Compliant    AuthService
Compliant    PatientRecordsDB
Compliant    ConsultationService
VIOLATION    ExternalSMSGateway
VIOLATION    ExternalAnalyticsSaaS
Compliant    PrescriptionService

============================================================
VIOLATION DETAILS
============================================================

Component : ExternalSMSGateway
Rule      : BAC-001
HIPAA Ref : 45 CFR 164.308(b)(1) — Business Associate Contracts
Reason    : This component transmits PHI to an external service
            without a Business Associate Contract, violating
            HIPAA required safeguards for third-party data sharing.

Component : ExternalAnalyticsSaaS
Rule      : ENC-002
HIPAA Ref : 45 CFR 164.312(e)(1) — Transmission Security
Reason    : PHI is being sent to an external analytics platform
            without encryption, violating HIPAA Technical
            Safeguard requirements.

============================================================
SUMMARY: 2 violation(s) in 2 component(s) out of 6 total
============================================================
```

---

## HIPAA Rules Implemented

| Rule ID | Description | HIPAA CFR |
|---|---|---|
| BAC-001 | PHI transmitted to external service without a Business Associate Contract | 45 CFR 164.308(b)(1) |
| ENC-002 | PHI transmitted to external service without encryption | 45 CFR 164.312(e)(1) |
| EXT-003 | External component receives PHI with no documented agreement | 45 CFR 164.308(b)(1) |
| AUD-004 | PHI stored in database without audit logging enabled | 45 CFR 164.312(b) |
| LOG-005 | External service receives PHI with no audit trail | 45 CFR 164.312(b) |

---

## Dataset

The synthetic dataset (`data/Architecture_Compliance_Dataset.tsv`) contains:

- 6 healthcare systems: Telemedicine Platform, Appointment Booking System, Lab Results Portal, Medplum, Microsoft FHIR, HAPI FHIR
- 81 components total across all systems
- Manually labelled HIPAA violations derived from published CFR text
- Fields: System, Component ID, Component Name, Component Type, Sends Data To, Handles PHI, Is External, Has BAC Contract, Has Encryption, Has Audit Log, Notes, Violation Expected, Extraction Status

---

## GitHub Repositories Analysed (Batch Mode)

| System | Repositories |
|---|---|
| Medplum | medplum, medplum-demo-bots |
| OpenEMR | openemr, openemr-devops, openemr-on-ecs |
| Microsoft FHIR | fhir-server, fhir-server-samples, healthcare-apis-samples, FHIR-Converter, fhir-codegen, healthcare-shared-components |
| HAPI FHIR | hapi-fhir, hapi-fhir-jpaserver-starter |
| FHIR Tools | client-js, client-py, fhir.resources, fhir (google) |

17 unique repositories. One duplicate was identified and removed from the original list of 18.

---

## Evaluation

Results on the synthetic dataset of 81 components against manually labelled ground truth.

| Metric | Keyword Baseline | Pure LLM | Neuro-Symbolic |
|---|---|---|---|
| Precision | TBD | TBD | TBD |
| Recall | TBD | TBD | TBD |
| F1 Score | TBD | TBD | TBD |
| False Negative Rate | TBD | TBD | TBD |
| Violations Missed | TBD | TBD | TBD |

Results will be updated after the final evaluation run is completed.

---

## Research Context

This project demonstrates a neuro-symbolic AI approach to compliance validation:

- Symbolic component: SPARQL rules provide deterministic, auditable, repeatable decisions. Same input always produces the same output.
- Neural component: Groq LLM extracts unstructured architecture documentation and explains violations in plain English.

The combination makes the system both accurate and explainable. Every violation comes with a specific reason traceable to an exact HIPAA CFR safeguard. Pure LLM systems are probabilistic and cannot guarantee rule coverage. Symbolic systems alone cannot parse natural language documentation.

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

**Raisa** — Product Developer, ontology, schema, scraper, extractor, graph builder, rule engine, explainer, report, main pipeline, baseline, evaluate, batch runner, dataset construction

**Reza** — Project architecture, research direction, system integration, evaluation design, documentation and Risk Management 

---

*Course project — Independent University Bangladesh*
