# neurosymbolic-ai-checker-for-HIPAA-compliance

Automated HIPAA compliance validation for software architectures using Knowledge Graphs and Neuro-Symbolic AI. [1]

#### What It Does [2]
This system takes a GitHub repository URL as input, analyzes its software architecture, builds a semantic knowledge graph, and detects HIPAA violations using a combination of rule-based reasoning (SPARQL) and AI explanation (Groq LLM). [2]

**Input:** A GitHub repository URL [2]
**Output:** A compliance report flagging which components violate HIPAA rules and why [2]

#### Pipeline Overview [2]
GitHub URL ↓ 
README Scraper — Fetches and extracts architecture info ↓ 
Groq LLM Extractor — Identifies components, PHI handling, external services ↓ 
Knowledge Graph — Converts structured data into RDF graph (rdflib) ↓ 
SPARQL Rule Engine — Runs 5 HIPAA rules against the graph ↓ 
Groq Explainer — Generates plain-English reasons for each violation ↓ 
Compliance Report — Per-component ✅ / ❌ output with explanations [2]

#### Tech Stack [3]
| Component | Tool | Cost |
| :--- | :--- | :--- |
| Component extraction | Groq API (llama-3.1-70b-versatile) | Free |
| Knowledge graph | rdflib (Python) | Free |
| Rule engine | SPARQL queries | Free |
| Violation explanation | Groq API | Free |
| Data scraping | GitHub API + requests | Free | [3]

#### Project Structure [3]
```text
hipaa-compliance-checker/
├── data/
│   └── Architecture_Compliance_Dataset.tsv ← Synthetic dataset
├── src/
│   ├── ontology.py ← RDF classes, properties, rule IDs
│   ├── schema.py ← Shared data structure and validator
│   ├── scraper.py ← GitHub README fetcher
│   ├── extractor.py ← Groq component extractor
│   ├── graph_builder.py ← RDF knowledge graph builder
│   ├── rule_engine.py ← SPARQL HIPAA rule engine
│   ├── explainer.py ← Groq violation explainer
│   ├── report.py ← Compliance report generator
│   └── main.py ← Full pipeline entry point
├── output/
│   └── reports/ ← Generated compliance reports
├── .env ← API keys — NEVER PUSH THIS
├── .gitignore
├── requirements.txt
└── README.md
``` [3]

#### Setup [4]
##### 1. Clone the Repository
```bash
git clone https://github.com/rezaJOY/hipaa-compliance-checker
cd hipaa-compliance-checker
``` [4]

##### 2. Create a Virtual Environment
```bash
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Activate on Mac/Linux:
source venv/bin/activate
``` [4]

##### 3. Install Dependencies
```bash
pip install -r requirements.txt
``` [4]

##### 4. Set Up API Keys
Create a `.env` file in the project root:
```text
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_token_here
Get your Groq API key at: https://console.groq.com
Get your GitHub token at: GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → check repo scope
Usage
Run on a GitHub Repository
python src/main.py https://github.com/owner/repo
``` [5]

##### Run on Synthetic Dataset
```bash
python src/main.py
``` [5]

##### Example Output [5]
```text
============================================================
HIPAA COMPLIANCE VALIDATION REPORT
Generated: 2024-01-01 12:00
============================================================
✅ Compliant AuthService
✅ Compliant PatientRecordsDB
✅ Compliant ConsultationService
❌ VIOLATION ExternalSMSGateway
❌ VIOLATION ExternalAnalyticsSaaS
✅ Compliant PrescriptionService
============================================================
VIOLATION DETAILS
============================================================
Component : ExternalSMSGateway
Rule : BAC-001
Reason : This component transmits PHI to an external service without a Business Associate Contract, violating HIPAA's required safeguards for third-party data sharing.

Component : ExternalAnalyticsSaaS
Rule : ENC-002
Reason : PHI is being sent to an external analytics platform without encryption, violating HIPAA's Technical Safeguard requirements.

Summary: 2 violation(s) in 6 components
``` [5]

#### HIPAA Rules Implemented [6]
| Rule ID | Description |
| :--- | :--- |
| BAC-001 | PHI transmitted to external service without a Business Associate Contract |
| ENC-002 | PHI transmitted to external service without encryption |
| EXT-003 | External component receives PHI with no documented agreement |
| AUD-004 | PHI stored in database without audit logging enabled |
| LOG-005 | External service receives PHI with no audit trail | [6]

#### Dataset [6]
The synthetic dataset (`data/Architecture_Compliance_Dataset.tsv`) contains: [6]
* **3 healthcare systems** — Telemedicine Platform, Appointment Booking System, Lab Results Portal [6]
* **35 components** total across all systems [6]
* **8 injected HIPAA violations** for evaluation [6]
* Fields: System, Component ID, Component Name, Component Type, Sends Data To, Handles PHI, Is External, Has BAC Contract, Notes, Violation Expected, Extraction Status [6]

#### Evaluation [7]
| Metric | Target |
| :--- | :--- |
| Precision | > 0.80 |
| Recall | > 0.75 |
| F1 Score | > 0.77 | [7]

#### Research Context [7]
This project demonstrates a **neuro-symbolic AI** approach to compliance validation: [7]
* **Symbolic component** — SPARQL rules provide explainable, auditable decisions [7]
* **Neural component** — Groq LLM extracts unstructured architecture info and explains violations in plain English [7]

The combination makes the system both accurate and explainable — every violation comes with a specific reason traceable to a HIPAA safeguard. [7]

#### Requirements [8]
```text
rdflib>=6.3.2
requests>=2.31.0
beautifulsoup4>=4.12.2
groq>=0.4.2
pandas>=2.1.0
python-dotenv>=1.0.0
``` [8]
