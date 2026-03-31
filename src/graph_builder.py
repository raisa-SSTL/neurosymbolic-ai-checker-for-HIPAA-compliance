"""
graph_builder.py
================
WHAT THIS FILE DOES:
Takes the validated component list and builds an RDF knowledge graph.
Each component becomes a node. Each attribute becomes a triple.
Data flows become relationships between nodes.
 
PSEUDO CODE:
1. Create an empty RDF graph
2. Bind the HIPAA namespace (so output is readable)
3. Build a lookup index: component_id → component_name
4. For each component:
   a. Create a unique URI for it (using component_name)
   b. Add its type (Service, Database, External etc)
   c. Add all its attributes as triples
      (URI → handles_PHI → "Yes")
      (URI → is_External → "Yes")
      (URI → has_BAC_Contract → "No")
   d. For each item in sends_data_to:
      Resolve ID → name via lookup index
      Add a relationship triple
      (EmailService → sends_data_to → SMSGateway)
4. Save graph to .ttl file (Turtle format)
5. Return the graph for rule_engine to use
 
FIX (v2): Dataset Sends_Data_To column uses component IDs (TP-02, AB-03)
not component names. This caused all graph edges to point to ghost URIs.
Now resolves IDs to names before building edges via a pre-built lookup map.
"""
 
import os
from rdflib import Graph, Literal, RDF, XSD
 
from src.ontology import (
    HIPAA, Classes, Properties,
    COMPONENT_TYPE_MAP, DEFAULT_COMPONENT_CLASS,
    get_component_uri, get_system_uri
)
from src.schema import ComponentSchema, load_from_tsv, load_from_json
# ── Build ID → Name Lookup ────────────────────────────────────
def build_id_name_lookup(components: list) -> dict:
    """
    FIX: Builds a lookup dict from component_id to component_name.
    Used to resolve IDs in sends_data_to to actual component names.
 
    Example:
        {"TP-02": "API Gateway", "TP-03": "Auth Service", ...}
 
    Without this fix, sends_data_to = ["TP-02"] would create an edge
    to URI hipaa:TelemedicinePlatform_TP-02 which doesn't exist.
    The actual node URI is hipaa:TelemedicinePlatform_APIGateway.
    """
    lookup = {}
    for comp in components:
        if isinstance(comp, ComponentSchema) and comp.component_id:
            lookup[comp.component_id.strip()] = comp.component_name
    return lookup
 
# ── Build Graph ───────────────────────────────────────────────
def build_graph(components: list) -> Graph:
    """
    Converts a list of ComponentSchema objects into an RDF graph.
    Returns the graph object.
    """
    g = Graph()
    g.bind("hipaa", HIPAA)
 
    # FIX: Build ID→Name lookup before iterating
    id_to_name = build_id_name_lookup(components)
 
    for comp in components:
        if not isinstance(comp, ComponentSchema):
            continue
 
        uri     = get_component_uri(comp.system_name, comp.component_name)
        sys_uri = get_system_uri(comp.system_name)
 
        # ── Type ───────────────────────────────────────────────
        rdf_class = COMPONENT_TYPE_MAP.get(comp.component_type, DEFAULT_COMPONENT_CLASS)
        g.add((uri, RDF.type, rdf_class))
 
        # ── Attributes ─────────────────────────────────────────
        g.add((uri, Properties.component_name,    Literal(comp.component_name)))
        g.add((uri, Properties.component_type,    Literal(comp.component_type)))
        g.add((uri, Properties.handles_PHI,       Literal(comp.handles_phi)))
        g.add((uri, Properties.is_external,       Literal(comp.is_external)))
        g.add((uri, Properties.has_BAC_contract,  Literal(comp.has_bac_contract)))
        g.add((uri, Properties.has_encryption,    Literal(comp.has_encryption)))
        g.add((uri, Properties.has_audit_log,     Literal(comp.has_audit_log)))
        g.add((uri, Properties.belongs_to_system, sys_uri))
 
        # ── Data Flow Relationships ────────────────────────────
        # FIX: Resolve component IDs to names before building edge URIs
        for target_raw in comp.sends_data_to:
            if not target_raw:
                continue
            # Resolve ID → Name (e.g., "TP-02" → "API Gateway")
            target_name = id_to_name.get(target_raw.strip(), target_raw.strip())
            target_uri  = get_component_uri(comp.system_name, target_name)
            g.add((uri, Properties.sends_data_to, target_uri))
 
    resolved_edges = sum(1 for _, p, _ in g if p == Properties.sends_data_to)
    print(f"  Graph built: {len(g)} triples from {len(components)} components")
    print(f"  Data flow edges resolved: {resolved_edges}")
    return g
 
# ── Save Graph ────────────────────────────────────────────────
def save_graph(g: Graph, path: str = "output/graph.ttl"):
    """Saves graph to Turtle format file."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    g.serialize(destination=path, format="turtle")
    print(f"  Graph saved to {path}")
 
# ── Load Graph ────────────────────────────────────────────────
def load_graph(path: str = "output/graph.ttl") -> Graph:
    """Loads graph from Turtle format file."""
    g = Graph()
    g.bind("hipaa", HIPAA)
    g.parse(path, format="turtle")
    print(f"  Graph loaded: {len(g)} triples from {path}")
    return g
 
# ── Smoke Test ────────────────────────────────────────────────
if __name__ == "__main__":
    tsv_path = "data/Architecture_Compliance_Dataset.tsv"
 
    if not os.path.exists(tsv_path):
        print(f"  TSV not found at {tsv_path}")
        print("  Export from Google Sheets: File → Download → TSV")
        print("  Then place it in the data/ folder")
    else:
        components = load_from_tsv(tsv_path)
        if components:
            g = build_graph(components)
            save_graph(g)
 
            print(f"\n  Verifying edge resolution...")
            unresolved = [
                str(o) for _, p, o in g
                if p == Properties.sends_data_to
                and "-" in str(o).split("#")[-1]  # Still looks like an ID
            ]
            if unresolved:
                print(f"  WARNING: {len(unresolved)} edges may still be unresolved IDs:")
                for u in unresolved[:5]:
                    print(f"    {u}")
            else:
                print("  All edges resolved to component names ")
 
            print(f"\n  Sample triples:")
            count = 0
            for s, p, o in g:
                print(f"  {s.split('#')[-1]} → {p.split('#')[-1]} → {o}")
                count += 1
                if count >= 8:
                    break
 
            print("\n graph_builder.py v2 working — ID→Name resolution active")
