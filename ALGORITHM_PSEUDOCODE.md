# Neuro-Symbolic HIPAA Compliance Checker — Algorithm Pseudocode

## Overview

This document presents the pseudocode for the Neuro-Symbolic AI Checker for HIPAA Compliance. The system combines **Symbolic AI** (deterministic SPARQL rule engine) with **Neural AI** (Groq LLM) to validate software architectures against healthcare compliance regulations.

---

## 1. Main Pipeline Orchestrator

```
ALGORITHM: MainPipeline(source)
INPUT:
  source: Either a file path to TSV dataset OR GitHub repository URL
OUTPUT:
  List of violations with explanations and compliance report

PROCEDURE:
  1. Initialize output directory
  
  2. DETERMINE INPUT TYPE
     IF source ends with ".tsv" THEN
       LOAD_MODE ← TSV_MODE
       components ← load_from_tsv(source)
     ELSE IF source starts with "https://github.com/" THEN
       LOAD_MODE ← GITHUB_MODE
       readme_text ← fetch_readme_cached(source)
       arch_section ← extract_architecture_section(readme_text)
       system_name ← extract_repo_name(source)
       LOAD_MODE ← LLM_EXTRACTION_MODE
       components ← extract_components(arch_section, system_name)
     ELSE
       RAISE Error("Invalid source")
     END IF
  
  3. VALIDATE COMPONENTS
     FOR each component IN components DO
       component ← validate_component(component)
       Check for missing required fields (has_encryption, has_audit_log)
       IF missing critical fields THEN
         Log warning about rule coverage impact
       END IF
     END FOR
  
  4. BUILD KNOWLEDGE GRAPH (Symbolic AI)
     graph ← build_rdf_graph(components)
     Save graph to TTL file for inspection
  
  5. RUN COMPLIANCE RULES (Symbolic AI)
     violations ← run_sparql_rules(graph)
     Deduplicates violations by (component_name, rule_id)
  
  6. GENERATE EXPLANATIONS (Neural AI)
     FOR each violation IN violations DO
       explanation ← explain_with_llm(violation)
       violation.explanation ← explanation
     END FOR
  
  7. GENERATE REPORT
     report ← generate_compliance_report(components, violations)
     Save report to dated text file
  
  8. RETURN violations and report path
END PROCEDURE
```

---

## 2. Schema Validation & Normalization

```
ALGORITHM: validate_component(raw_dict)
INPUT:
  raw_dict: Raw component data from TSV or LLM
OUTPUT:
  ComponentSchema: Validated and normalized component object

PROCEDURE:
  component ← new ComponentSchema
  
  1. EXTRACT AND NORMALIZE FIELDS
     component.component_name ← raw_dict["Component_Name"] OR "UnknownComponent"
     component.system_name ← raw_dict["System"] OR "Unknown System"
     component.component_id ← raw_dict["Component_ID"] OR ""
  
  2. NORMALIZE COMPONENT TYPE
     raw_type ← raw_dict["Component_Type"]
     component.component_type ← normalize_type(raw_type)
     
     WHERE normalize_type(t) RETURNS:
       IF t IN {"service", "microservice", "worker"} THEN "Service"
       ELSE IF t IN {"api", "gateway"} THEN "API"
       ELSE IF t IN {"database", "db", "datastore"} THEN "Database"
       ELSE IF t IN {"external", "third-party", "saas"} THEN "External"
       ELSE IF t IN {"storage", "blob", "s3"} THEN "Storage"
       ELSE "Service"
  
  3. NORMALIZE YES/NO FIELDS
     component.handles_phi ← normalize_yes_no(raw_dict["Handles_PHI"])
     component.is_external ← normalize_yes_no(raw_dict["Is_External"])
     component.has_bac_contract ← normalize_yes_no(raw_dict["Has_BAC_Contract"])
     component.has_encryption ← normalize_yes_no(raw_dict["Has_Encryption"])
     component.has_audit_log ← normalize_yes_no(raw_dict["Has_AuditLog"])
     
     WHERE normalize_yes_no(v) RETURNS:
       IF v IN {"yes", "true", "1", "y"} THEN "Yes"
       ELSE IF v IN {"no", "false", "0", "n"} THEN "No"
       ELSE IF v IN {"n/a", "na", "none"} THEN "N/A"
       ELSE "Unknown"
  
  4. HANDLE EXTERNAL COMPONENT RULE
     IF component.component_type == "External" THEN
       component.is_external ← "Yes"  // Force external type → is_external=Yes
     END IF
  
  5. PARSE DATA RELATIONSHIPS
     sends_data_to_raw ← raw_dict["Sends_Data_To"] (comma-separated IDs)
     component.sends_data_to ← parse_list(sends_data_to_raw)
  
  6. EXTRACT METADATA
     component.notes ← raw_dict["Notes"] OR ""
     component.violation_expected ← raw_dict["Violation_Expected"] OR "No"
     component.extraction_status ← "Extracted"
  
  7. RETURN validated component
END PROCEDURE
```

---

## 3. RDF Knowledge Graph Construction

```
ALGORITHM: build_rdf_graph(components)
INPUT:
  components: List of validated ComponentSchema objects
OUTPUT:
  graph: RDF knowledge graph with all triples

PROCEDURE:
  graph ← new RDFGraph()
  graph.bind_namespace("hipaa", HIPAA_NAMESPACE)
  
  1. BUILD ID→NAME LOOKUP
     lookup ← {}
     FOR each comp IN components DO
       IF comp.component_id IS NOT EMPTY THEN
         lookup[comp.component_id] ← comp.component_name
       END IF
     END FOR
  
  2. FOR each component IN components DO
       component_uri ← generate_uri(component.system_name, component.component_name)
       system_uri ← generate_uri(component.system_name)
  
       3. ADD TYPE TRIPLE
          graph.add_triple(component_uri, rdf:type, get_rdf_class(component.component_type))
          
          WHERE get_rdf_class(t) RETURNS:
            IF t == "Service" THEN hipaa:Service
            ELSE IF t == "API" THEN hipaa:API
            ELSE IF t == "Database" THEN hipaa:Database
            ELSE IF t == "External" THEN hipaa:ExternalService
            ELSE IF t == "Storage" THEN hipaa:Storage
            ELSE hipaa:Component
  
       4. ADD ATTRIBUTE TRIPLES
          graph.add_triple(component_uri, hipaa:component_Name, component.component_name)
          graph.add_triple(component_uri, hipaa:component_Type, component.component_type)
          graph.add_triple(component_uri, hipaa:handles_PHI, component.handles_phi)
          graph.add_triple(component_uri, hipaa:is_External, component.is_external)
          graph.add_triple(component_uri, hipaa:has_BAC_Contract, component.has_bac_contract)
          graph.add_triple(component_uri, hipaa:has_Encryption, component.has_encryption)
          graph.add_triple(component_uri, hipaa:has_AuditLog, component.has_audit_log)
          graph.add_triple(component_uri, hipaa:belongs_To_System, system_uri)
  
       5. ADD DATA RELATIONSHIP EDGES
          FOR each data_target_id IN component.sends_data_to DO
            IF data_target_id IN lookup THEN
              target_name ← lookup[data_target_id]
              target_uri ← generate_uri(component.system_name, target_name)
              graph.add_triple(component_uri, hipaa:sends_Data_To, target_uri)
            END IF
          END FOR
    END FOR
  
  6. SAVE GRAPH TO TTL FILE
     save_as_turtle(graph, "output/graph.ttl")
  
  7. RETURN graph
END PROCEDURE
```

---

## 4. SPARQL Rule Engine (Symbolic AI)

```
ALGORITHM: run_sparql_rules(graph)
INPUT:
  graph: RDF knowledge graph
OUTPUT:
  List of violations with rule_id, component_name, and description

PROCEDURE:
  violations ← {}
  seen_violations ← set()  // Deduplication key: (component_name, rule_id)
  
  1. DEFINE SPARQL QUERIES FOR 5 HIPAA RULES
     
     RULE BAC-001: Business Associate Contract Violation
     QUERY:
       SELECT ?name WHERE {
         ?c hipaa:handles_PHI "Yes" .
         ?c hipaa:is_External "Yes" .
         ?c hipaa:has_BAC_Contract "No" .
         ?c hipaa:component_Name ?name .
       }
     DESCRIPTION: "PHI transmitted to external service without a Business Associate Contract"
     
     RULE ENC-002: Encryption Violation
     QUERY:
       SELECT ?name WHERE {
         ?c hipaa:handles_PHI "Yes" .
         ?c hipaa:is_External "Yes" .
         ?c hipaa:has_Encryption "No" .
         ?c hipaa:component_Name ?name .
       }
     DESCRIPTION: "PHI transmitted to external service without encryption"
     
     RULE EXT-003: External Component BAC Violation
     QUERY:
       SELECT ?name WHERE {
         ?c a hipaa:ExternalService .
         ?c hipaa:handles_PHI "Yes" .
         ?c hipaa:has_BAC_Contract "No" .
         ?c hipaa:component_Name ?name .
       }
     DESCRIPTION: "External component receives PHI with no documented agreement"
     
     RULE AUD-004: Database Audit Log Violation
     QUERY:
       SELECT ?name WHERE {
         ?c a hipaa:Database .
         ?c hipaa:handles_PHI "Yes" .
         ?c hipaa:has_AuditLog "No" .
         ?c hipaa:component_Name ?name .
       }
     DESCRIPTION: "PHI stored in database without audit logging enabled"
     
     RULE LOG-005: External Service Audit Violation
     QUERY:
       SELECT ?name WHERE {
         ?c hipaa:is_External "Yes" .
         ?c hipaa:handles_PHI "Yes" .
         ?c hipaa:has_AuditLog "No" .
         ?c hipaa:component_Name ?name .
       }
     DESCRIPTION: "External service receives PHI with no audit trail"
     
     RULE BAC-001-SENDER: Internal sender pushing PHI to external without BAC
     QUERY:
       SELECT ?name WHERE {
         ?sender hipaa:handles_PHI "Yes" .
         ?sender hipaa:is_External "No" .
         ?sender hipaa:sends_Data_To ?receiver .
         ?receiver hipaa:is_External "Yes" .
         ?receiver hipaa:has_BAC_Contract "No" .
         ?sender hipaa:component_Name ?name .
       }
     DESCRIPTION: "Internal service transmits PHI to external with no Business Associate Contract"
     
     RULE ENC-002-SENDER: Internal sender transmitting PHI without encryption
     QUERY:
       SELECT ?name WHERE {
         ?sender hipaa:handles_PHI "Yes" .
         ?sender hipaa:is_External "No" .
         ?sender hipaa:has_Encryption "No" .
         ?sender hipaa:sends_Data_To ?receiver .
         ?receiver hipaa:is_External "Yes" .
         ?sender hipaa:component_Name ?name .
       }
     DESCRIPTION: "Internal service transmits PHI without encryption to external"
     
     RULE LOG-005-SENDER: Internal sender pushing PHI to unaudited external
     QUERY:
       SELECT ?name WHERE {
         ?sender hipaa:handles_PHI "Yes" .
         ?sender hipaa:is_External "No" .
         ?sender hipaa:sends_Data_To ?receiver .
         ?receiver hipaa:is_External "Yes" .
         ?receiver hipaa:has_AuditLog "No" .
         ?sender hipaa:component_Name ?name .
       }
     DESCRIPTION: "Internal service transmits PHI to external with no audit trail"
  
  2. FOR each (rule_id, sparql_query) IN RULES DO
       results ← graph.query(sparql_query)
       
       FOR each result_row IN results DO
         component_name ← result_row["name"]
         dedup_key ← (component_name, rule_id)
         
         IF dedup_key NOT IN seen_violations THEN
           seen_violations.add(dedup_key)
           
           violation ← {
             "component": component_name,
             "rule_id": rule_id,
             "description": RULE_DESCRIPTIONS[rule_id],
             "explanation": ""  // Will be filled by LLM
           }
           
           violations.append(violation)
         END IF
       END FOR
     END FOR
  
  3. LOG SUMMARY
     unique_components ← count unique components in violations
     LOG(violations.count, "violations found")
     LOG(unique_components, "unique components flagged")
  
  4. RETURN violations list
END PROCEDURE
```

---

## 5. LLM-Based Explanation Generation (Neural AI)

```
ALGORITHM: explain_violations(violations)
INPUT:
  violations: List of violation objects from rule engine
OUTPUT:
  violations: Same list with "explanation" field populated

PROCEDURE:
  FOR each violation IN violations DO
    component_name ← violation.component
    rule_id ← violation.rule_id
    rule_description ← violation.description
    
    1. CONSTRUCT LLM PROMPT
       prompt ← format_string("""
         A software architecture compliance checker found the following HIPAA 
         violation:
         
         Component: {component_name}
         Rule Violated: {rule_id}
         Rule Description: {rule_description}
         
         Explain in plain English (1-2 sentences) why this is a HIPAA violation 
         and what the business impact would be.
       """)
    
    2. CALL GROQ LLM
       response ← groq_client.query(
         model="mixtral-8x7b-32768",
         prompt=prompt,
         max_tokens=150
       )
    
    3. EXTRACT AND ASSIGN EXPLANATION
       explanation_text ← response.content.strip()
       violation.explanation ← explanation_text
    
    4. ERROR HANDLING
       TRY
         explanation ← groq_client.query(prompt)
       CATCH RateLimitError THEN
         Log warning, use default description
         violation.explanation ← violation.description
       CATCH APIError THEN
         Log warning, use default description
         violation.explanation ← violation.description
       END TRY
  END FOR
  
  5. RETURN violations with explanations populated
END PROCEDURE
```

---

## 6. Compliance Report Generation

```
ALGORITHM: generate_compliance_report(components, violations)
INPUT:
  components: List of all analyzed components
  violations: List of violations with explanations
OUTPUT:
  report_path: File path to generated compliance report

PROCEDURE:
  timestamp ← current_timestamp()
  report_filename ← format("report_{timestamp}.txt")
  report_path ← "output/reports/" + report_filename
  
  flagged_components ← set of component names in violations
  compliant_components ← components NOT IN flagged_components
  
  1. START REPORT GENERATION
     report_content ← ""
     
  2. ADD HEADER SECTION
     report_content += format("""
     ╔════════════════════════════════════════════════════════════╗
     ║    HIPAA COMPLIANCE ANALYSIS REPORT                        ║
     ║    Generated: {timestamp}                                   ║
     ╚════════════════════════════════════════════════════════════╝
     """)
  
  3. ADD SUMMARY STATISTICS
     total_components ← components.length
     violations_count ← violations.length
     compliance_rate ← (total_components - flagged_components.length) / total_components
     
     report_content += format("""
     SUMMARY
     ────────────────────────────────────────────────────────────
     Total Components Analyzed  : {total_components}
     Violations Detected        : {violations_count}
     Unique Flagged Components  : {flagged_components.length}
     Compliant Components       : {compliant_components.length}
     Compliance Rate            : {compliance_rate * 100}%
     """)
  
  4. ADD VIOLATIONS SECTION
     FOR each violation IN violations DO
       report_content += format("""
       
       ❌ VIOLATION: {violation.rule_id}
       Component: {violation.component}
       Rule: {violation.description}
       Explanation: {violation.explanation}
       """)
     END FOR
  
  5. ADD COMPLIANT COMPONENTS SECTION
     report_content += """
     ✅ COMPLIANT COMPONENTS
     ────────────────────────────────────────────────────────────
     """
     FOR each comp IN compliant_components DO
       report_content += format("{comp.component_name}\n")
     END FOR
  
  6. SAVE REPORT TO FILE
     file ← open(report_path, "write")
     file.write(report_content)
     file.close()
  
  7. ALSO SAVE METADATA AS JSON
     metadata ← {
       "timestamp": timestamp,
       "total_components": total_components,
       "violations_found": violations_count,
       "compliance_rate": compliance_rate,
       "violations": violations
     }
     save_to_json(metadata, report_path.replace(".txt", ".json"))
  
  8. RETURN report path
END PROCEDURE
```

---

## 7. GitHub Integration (Optional)

```
ALGORITHM: extract_components(architecture_text, system_name)
INPUT:
  architecture_text: Raw text from GitHub README
  system_name: Name of the system (from repo name)
OUTPUT:
  List of ComponentSchema objects

PROCEDURE:
  1. CONSTRUCT EXTRACTION PROMPT
     prompt ← format("""
     Analyze the following architecture description and extract all software 
     components. For each component, provide:
     - Name
     - Type (Service, API, Database, External, Storage)
     - Does it handle PHI (Yes/No/Unknown)
     - Is it external (Yes/No)
     - Does it have a BAC (Business Associate Contract) (Yes/No/N/A)
     - Does it have encryption (Yes/No/Unknown)
     - Does it have audit logging (Yes/No/Unknown)
     - What components does it send data to
     
     Architecture:
     {architecture_text}
     
     Format as JSON array with these keys:
     component_name, component_type, handles_phi, is_external, 
     has_bac_contract, has_encryption, has_audit_log, sends_data_to
     """)
  
  2. CALL GROQ LLM
     response ← groq_client.query(
       model="mixtral-8x7b-32768",
       prompt=prompt,
       max_tokens=2000
     )
  
  3. PARSE JSON RESPONSE
     components_json ← extract_json(response.content)
  
  4. CONVERT TO SCHEMA OBJECTS
     components ← []
     FOR each raw_comp IN components_json DO
       comp ← validate_component(raw_comp)
       comp.system_name ← system_name
       components.append(comp)
     END FOR
  
  5. ERROR HANDLING
     TRY
       response ← groq_client.query(prompt)
     CATCH JSONParseError THEN
       Log error, request retry
     CATCH APIError THEN
       Log error, return empty list
     END TRY
  
  6. RETURN list of components
END PROCEDURE
```

---

## 8. Data Flow Diagram (Pseudocode Perspective)

```
INPUT SOURCES
  ↓
  ├─→ [TSV File] → load_from_tsv()
  └─→ [GitHub URL] → fetch_readme() → extract_architecture_section() → extract_components()
  ↓
  [Validated Components]
  ↓
  build_rdf_graph()  (Ontology: Classes, Properties, URIs)
  ↓
  [RDF Knowledge Graph]
  ↓
  run_sparql_rules() (5 Symbolic AI Rules + 3 Traversal Rules)
  ↓
  [Violations List: {component, rule_id, description}]
  ↓
  explain_violations() (Neural AI: Groq LLM)
  ↓
  [Violations with Explanations]
  ↓
  generate_report()
  ↓
  [Compliance Report + JSON Metadata]
```

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Single Ontology (ontology.py)** | Central source of truth for all RDF URIs and properties prevents inconsistencies |
| **Schema-based validation** | Ensures data consistency through pipeline stages |
| **SPARQL for rules** | Deterministic, auditable, reproducible rule evaluation (not LLM-based) |
| **LLM for explanations only** | Decouples symbolic detection from neural explanation generation |
| **Sender-side traversal rules** | Captures internal services pushing PHI to external receivers (not just receivers) |
| **Deduplication by (component, rule_id)** | Same component can violate multiple rules (correct); same component + rule = one entry |

---

## 10. Error Handling Strategy

```
PROCEDURE: graceful_degradation()

SCENARIO 1: Missing required fields in dataset
  → Log warning about rule coverage
  → Continue with best-effort checking
  → Note in report which rules are limited

SCENARIO 2: LLM API failure during explanation
  → Catch exception
  → Use default rule description as fallback
  → Continue report generation

SCENARIO 3: SPARQL query error
  → Log error with property name mismatch info
  → Skip that rule
  → Continue with remaining rules

SCENARIO 4: GitHub API rate limit
  → Cache README responses (fetch_readme_cached)
  → Allow offline development on cached data

SCENARIO 5: Malformed component data
  → Validate during schema normalization
  → Assign safe defaults (Unknown, No, N/A)
  → Continue processing

END PROCEDURE
```

---

## References for Implementation

- **RDF/SPARQL**: W3C RDF and SPARQL specifications; rdflib Python library
- **HIPAA Rules**: 45 CFR §164.308-318 (Security Rule, Privacy Rule)
- **LLM API**: Groq Cloud API for fast inference
- **Graph Database**: In-memory RDF graph using rdflib (suitable for ≤1000 components)

---

**End of Pseudocode Document**
