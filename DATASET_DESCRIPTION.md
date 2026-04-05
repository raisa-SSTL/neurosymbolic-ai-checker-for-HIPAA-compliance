# Dataset Description: Architecture Compliance Dataset

## Overview

The **Architecture Compliance Dataset** is a synthetic collection of software architecture components from six real-world healthcare systems, annotated with HIPAA compliance attributes. The dataset is designed for evaluating compliance checking algorithms on healthcare system architectures and contains both compliant and non-compliant configurations with ground-truth violation labels.

## Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Healthcare Systems** | 6 |
| **Total Components** | 83 |
| **Total Violations (Injected)** | 8 |
| **Completion Rate** | 100% |
| **Format** | Tab-Separated Values (TSV) |
| **File Size** | ~15 KB |

## System Descriptions

### 1. Telemedicine Platform (13 components)
A real-time virtual consultation system connecting patients with healthcare providers. Components include a patient mobile app, API gateway, consultation service, patient records database, and integrations with external video CDN, analytics platforms, and messaging services.

**Key Features:**
- Direct patient-to-provider communication
- Live video consultation streaming
- Electronic prescription management
- Appointment notification system

**Components:** Patient Mobile App, API Gateway, Auth Service, Consultation Service, Patient Records DB, Video Streaming Server, Internal Analytics, Prescription Service, External Video CDN, Notification Service, External Analytics SaaS, External SMS Gateway

---

### 2. Appointment Booking System (12 components)
A web-based scheduling platform for managing patient appointments across a healthcare network. Includes a booking portal, scheduling engine, appointment and user databases, reminder service, and integrations with external email and business intelligence tools.

**Key Features:**
- Patient self-service appointment scheduling
- Doctor availability matching
- Automated reminder notifications
- Administrative dashboard for staff management
- Booking analytics and reporting

**Components:** Web Booking Portal, Booking API, Scheduling Engine, Auth Service, Appointment DB, User DB, Reminder Service, Admin Dashboard API, Audit Log Storage, Analytics Processor, External Email Service, External BI Tool

---

### 3. Lab Results Portal (11 components)
A patient portal for viewing laboratory test results and diagnostic reports. The system manages lab result storage, retrieval, report generation, and secure delivery via external storage and SMS notification services.

**Key Features:**
- Secure patient access to lab reports
- Diagnostic result processing
- Report generation and archival
- External cloud storage integration
- SMS notification delivery

**Components:** Patient Portal Web, API Gateway, Lab Results Service, Auth Service, Lab Results DB, Identity Storage, Report Generator, Internal File Storage, Notification Service, External Cloud Storage, External SMS Provider

---

### 4. Medplum (13 components)
An open-source, production-grade FHIR-compliant healthcare data platform. Features a Clinical Data Repository, FHIR API, PostgreSQL backend, authentication server, bot automation, Redis caching, medical device connectivity, and web application for clinical workflows.

**Key Features:**
- FHIR-compliant data models (HL7 standard)
- SMART-on-FHIR OAuth 2.0 support
- Server-side automation via Medplum Bots
- Medical device integration via On-Premise Agent
- Managed cloud database infrastructure

**Components:** Clinical Data Repository, FHIR API, PostgreSQL Database, Auth Server, Medplum Bots, Redis Cache, On-Premise Agent, Web Application, HL7 Integration Service, FHIR Router, AWS Lambda Bot Layer, GraphiQL Interface, Backend API Server

---

### 5. Microsoft FHIR (15 components)
Microsoft's cloud-based FHIR server implementation on Azure infrastructure. Includes Azure Active Directory integration, FHIR proxy layer, RESTful API endpoints, bulk export capabilities, persistence layers with Azure Cosmos DB and SQL Server, and integrated DICOM imaging services.

**Key Features:**
- Azure cloud-native architecture
- RBAC via Azure Active Directory
- SMART on FHIR OAuth compliance
- Bulk data export/import
- Multi-database support (NoSQL and relational)
- DICOM imaging integration

**Components:** Client Application, Azure Active Directory, FHIR Proxy, RESTful API Layer, SMART on FHIR Proxy, Core Logic Layer, Bulk Export Module, Convert Data Service, Persistence Layer, Azure Cosmos DB, SQL Server, DICOM Server, Azure Blob Storage, Healthcare Workspace, Hosting Layer

---

### 6. HAPI FHIR (18 components)
The most widely deployed open-source FHIR server implementation. HAPI (HL7 FHIR API) includes REST API endpoints, resource controllers, JPA persistence layer, search indexing, FHIR validation, terminology services, authentication/authorization, binary storage, audit logging, caching, batch processing, and comprehensive monitoring.

**Key Features:**
- Battle-tested open-source FHIR server
- JPA-based ORM for relational databases
- External identity provider support (Azure AD, Okta)
- Role-based access control (RBAC)
- FHIR-native audit event logging
- Search and terminology services
- Swagger API documentation

**Components:** REST API Layer, Resource Controllers, Server Framework, JPA Persistence Layer, Relational Database, Search Engine, FHIR Validation, Terminology Service, AuthN (Identity), AuthZ (Access), Binary Storage, External Integrations, Logging/Metrics, Audit Logging, Caching Layer, Batch Scheduler, Config Management, Swagger UI

---

## Data Schema

The dataset contains 13 attributes per component:

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| **System** | String | System name | Name of the healthcare system (e.g., "Telemedicine Platform") |
| **Component_ID** | String | e.g., "TP-01" | Unique component identifier within system |
| **Component_Name** | String | e.g., "Patient Mobile App" | Human-readable component name |
| **Component_Type** | String | Service, API, Database, External, Storage, Framework, Persistence, Security, Integration, Observability, Compliance, Performance, Background, Ops, Dev UX | Type of software component |
| **Sends_Data_To** | String (comma-separated) | e.g., "TP-02,TP-04,TP-10" | List of component IDs this component transmits data to |
| **Handles_PHI** | String | Yes, No, Unknown | Whether component processes, stores, or transmits Protected Health Information |
| **Is_External** | String | Yes, No | Whether component is outside organizational control (third-party SaaS, cloud provider) |
| **Has_BAC_Contract** | String | Yes, No, N/A | Whether Business Associate Agreement exists (required for external PHI handling) |
| **Has_Encryption** | String | Yes, No, Unknown | Whether data in transit uses encryption (TLS 1.2+ or equivalent) |
| **Has_AuditLog** | String | Yes, No, Unknown | Whether component maintains audit trails for PHI access and modifications |
| **Notes** | String | Free-form text | Description of component function and PHI handling rationale |
| **Violation_Expected** | String | Yes, No | Ground truth: whether component violates a HIPAA rule |
| **Extraction_Status** | String | Completed, Pending, Failed | Data quality indicator |

---

## Violations and Ground Truth

The dataset contains **8 injected HIPAA violations** across 5 rule categories:

### Violation Summary by Rule

| Rule ID | Rule Name | Count | Affected Components |
|---------|-----------|-------|-------------------|
| **BAC-001** | Missing Business Associate Contract | 4 | TP-09, TP-11, TP-12, AB-11 |
| **ENC-002** | Missing Encryption on PHI Transfer | 5 | TP-06, TP-07, AB-10, LR-03, LR-07 |
| **EXT-003** | External Component without BAC | 2 | TP-09, TP-11 |
| **AUD-004** | Database without Audit Logging | 3 | TP-05, AB-05, LR-05 |
| **LOG-005** | External Service without Audit Trail | 5 | TP-09, TP-11, TP-12, AB-11, LR-10 |

### Examples of Violations

**Example 1 — BAC-001 Violation:**
- Component: "External Video CDN" (TP-09)
- System: Telemedicine Platform
- Attributes: Handles_PHI=Yes, Is_External=Yes, Has_BAC_Contract=No
- Violation: External component receives live video containing PHI without a Business Associate Agreement

**Example 2 — AUD-004 Violation:**
- Component: "Patient Records DB" (TP-05)
- System: Telemedicine Platform
- Attributes: Handles_PHI=Yes, Component_Type=Database, Has_AuditLog=No
- Violation: Database storing patient medical history and prescriptions lacks audit logging

**Example 3 — ENC-002 Violation:**
- Component: "Video Streaming Server" (TP-06)
- System: Telemedicine Platform
- Attributes: Handles_PHI=Yes, Is_External=No, Has_Encryption=No
- Violation: Component streams live consultation video (PHI) to external provider without encryption

---

## HIPAA Compliance Rules

The dataset is designed to evaluate systems against five HIPAA Security Rule requirements, derived from 45 CFR §164.308-318:

### BAC-001: Business Associate Contract for External Services
**Rule:** Any external component handling PHI must have a signed Business Associate Agreement (BAA).

**HIPAA Citation:** 45 CFR §164.308(b)(1) — Workforce Security; 45 CFR §164.504(e) — Business Associate Agreements

**Dataset Relevance:** Detects third-party integrations (SaaS, cloud providers, messaging services) receiving PHI without contractual safeguards.

---

### ENC-002: Encryption for Data in Transit
**Rule:** Any component transmitting PHI (internally or externally) must use encryption (TLS 1.2 or equivalent).

**HIPAA Citation:** 45 CFR §164.312(a)(2)(i) — Encryption and Decryption

**Dataset Relevance:** Detects unencrypted data flows, including internal APIs and external integrations.

---

### EXT-003: External Component PHI Handling
**Rule:** External components (third-party services, cloud providers) handling PHI must have documentation of safeguards.

**HIPAA Citation:** 45 CFR §164.308(b)(3) — Business Associate Management

**Dataset Relevance:** Complements BAC-001 by using RDF class-based detection to catch external-typed components specifically.

---

### AUD-004: Database Audit Logging
**Rule:** Any database storing PHI must maintain audit logs of access and modifications.

**HIPAA Citation:** 45 CFR §164.312(b) — Audit Controls; 45 CFR §164.308(a)(5)(ii) — Log-in Monitoring

**Dataset Relevance:** Detects data stores lacking audit trails, a critical compliance gap for healthcare databases.

---

### LOG-005: External Service Audit Trail
**Rule:** External services receiving PHI must maintain audit logs of data access and handling.

**HIPAA Citation:** 45 CFR §164.308(b)(1) — Workforce Security in Business Associate Agreements

**Dataset Relevance:** Extends audit logging requirements to third-party services and SaaS platforms.

---

## Data Characteristics

### Component Type Distribution

| Type | Count | % | Notes |
|------|-------|---|-------|
| Service | 38 | 45.8% | Internal microservices, workers, middleware |
| API | 6 | 7.2% | RESTful and FHIR API gateways |
| Database | 11 | 13.3% | Relational, NoSQL, and specialized datastores |
| External | 13 | 15.7% | Third-party SaaS, cloud providers, CDNs |
| Storage | 8 | 9.6% | Object storage, caching, file systems |
| Other (Framework, Security, Integration, etc.) | 7 | 8.4% | Cross-cutting concerns |

### PHI Handling Distribution

| Handles_PHI | Count | % |
|-------------|-------|---|
| Yes | 63 | 75.9% |
| No | 14 | 16.9% |
| Unknown | 6 | 7.2% |

### External Component Distribution

| Is_External | Count | % |
|------------|-------|---|
| Yes | 13 | 15.7% |
| No | 70 | 84.3% |

### Data Flow Complexity

- **Total Data Relationships:** 47 directed edges (sends_data_to connections)
- **Max Out-Degree:** 3 (API gateways and routers)
- **Average Out-Degree:** 0.57 (components sending data)
- **Graph Density:** 0.007 (sparse graph typical of microservice architectures)

---

## Usage and Validation

### Intended Use Cases

1. **Algorithm Development:** Benchmark HIPAA compliance checking algorithms on realistic healthcare architectures
2. **Rule Evaluation:** Validate SPARQL rules and compliance queries against ground truth
3. **Metric Calculation:** Compute precision, recall, F1-score for automated compliance systems
4. **Teaching:** Educational example of healthcare system architecture and HIPAA requirements

### Data Quality Notes

- **Completeness:** All 83 components have complete attribute values (no missing critical fields)
- **Consistency:** Component type assignments validated; external components have is_External=Yes
- **Realism:** Systems modeled after real open-source and commercial healthcare platforms (Medplum, HAPI FHIR, Microsoft Azure Health Data Services)
- **Violation Coverage:** 8 injected violations span all 5 HIPAA rules for comprehensive evaluation

### Known Limitations

1. **Synthetic Data:** Ground truth violations are manually injected; real-world violations may differ in distribution
2. **Scale:** 83 components represents small to medium-sized healthcare systems (enterprise systems may have 1000+ components)
3. **Simplifications:** 
   - Component attributes are binary or ternary (Yes/No/Unknown); real systems require continuous attributes
   - Data relationships are simplified to direct sends_data_to edges (real systems have more complex routing, intermediaries, event buses)
4. **Static Snapshot:** Dataset captures architecture at one point in time; real systems evolve continuously

---

## Citation

For research, cite the dataset as:

```
Architecture Compliance Dataset. 
Synthetic healthcare system architectures for HIPAA compliance evaluation. 
Available at: https://github.com/[user]/neurosymbolic-ai-checker-for-HIPAA-compliance
```

---

## Access and Licensing

The dataset is provided as part of the **neurosymbolic-ai-checker-for-HIPAA-compliance** project. The dataset file `Architecture_Compliance_Dataset.tsv` is included in the repository under `data/` directory.

**License:** MIT

**Format:** Tab-Separated Values (TSV) — Import into spreadsheet software, Python pandas, or any data analysis tool.

---

## Experimental Methodology

Researchers using this dataset should:

1. **Split:** Divide the dataset into training (70%) and test (30%) sets by system
2. **Evaluation Metrics:**
   - **Precision:** Of violations flagged, how many are correct?
   - **Recall:** Of true violations, how many are detected?
   - **F1-Score:** Harmonic mean of precision and recall
3. **Baseline:** Report performance of simple rule-based checkers as baseline
4. **Statistical Significance:** Use cross-validation and significance testing for multi-system evaluation

---

**End of Dataset Description**
