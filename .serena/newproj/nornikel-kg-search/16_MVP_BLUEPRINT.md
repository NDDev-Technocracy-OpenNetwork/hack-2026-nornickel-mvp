# MVP Blueprint

## Goal

Build the smallest working product that proves the hackathon value:

> A researcher asks what was done for a material under a process regime and what happened to a property. The system returns an experiment table, exact evidence spans, graph path, conflicts or gaps, and a grounded answer.

## Non-Negotiable Product Contract

The MVP is working only if it can complete this loop:

```text
Upload/import source files
-> create artifact memory bank
-> generate EvidenceSpan IDs
-> extract material/regime/property/measurement facts
-> materialize graph path
-> index searchable evidence
-> answer a question with cited experiment table
-> show missing data/gap
```

## MVP-Lite Architecture

```text
Streamlit Workbench
        |
FastAPI / Application Services
        |
Domain Ports
        |
+------------------+-----------------+------------------+----------------+
| ArtifactStore    | MetadataStore   | GraphStore       | VectorStore    |
| local filesystem | DuckDB          | NetworkX         | Qdrant         |
+------------------+-----------------+------------------+----------------+
        |
Docling artifacts + extraction pipeline + QA/evaluation
```

## Why This Is The Right MVP Shape

- It is buildable quickly: one Python stack plus Qdrant.
- It is modular: domain code depends on ports, not vendor clients.
- It is scalable later: DuckDB to PostgreSQL, NetworkX to Neo4j, Streamlit to React.
- It is demo-friendly: Streamlit gives upload, tables, filters, charts, and graph previews fast.
- It keeps the core trust feature: every claim maps to an `EvidenceSpan`.

## P0 Modules

### `domain`

Owns schemas and invariants:

- Material;
- Experiment;
- ProcessingRegime;
- Property;
- PropertyMeasurement;
- EvidenceSpan;
- Document;
- Claim;
- Gap.

Rules:

- measurements require units;
- final-answer claims require `EvidenceSpan`;
- graph path uses the canonical relationship names;
- model output is candidate data until validated.

### `ingestion`

Owns source processing:

- source registration;
- Docling conversion;
- artifact manifest;
- table/image extraction;
- chunking;
- parser quality report;
- quarantine.

### `extraction`

Owns candidate facts:

- dictionary matching;
- regex/rule extraction for units, temperatures, durations, compositions, and values;
- structured table extraction;
- LLM JSON extraction on small chunks;
- schema validation;
- confidence scoring.

### `retrieval`

Owns evidence search:

- dense embeddings;
- sparse embeddings;
- Qdrant payload filters;
- hybrid retrieval;
- reranking by exact slot match and evidence quality.

### `graph`

Owns typed paths:

- build NetworkX graph from validated facts;
- return path and neighborhood JSON;
- keep Neo4j adapter contract ready.

### `qa`

Owns answer assembly:

- parse question into slots;
- canonicalize material/regime/property;
- retrieve evidence;
- expand graph path;
- assemble experiment table;
- detect gaps;
- generate grounded answer.

### `evals`

Owns proof:

- gold questions;
- expected evidence spans;
- Recall@10;
- citation coverage;
- unsupported claim count;
- ACL leak checks.

## P0 Screens

### Ingestion

- upload/import files;
- show parser status;
- show extracted artifacts;
- show quarantined sources.

### Ask

- query input;
- filters for material, regime, property, source type, validation status;
- answer summary;
- experiment table;
- evidence cards;
- graph path;
- gaps.

### Evidence

- source document;
- page/row/image reference;
- Markdown snippet;
- structured metadata;
- validation status.

### Evaluation

- run demo questions;
- show Recall@10, citation coverage, unsupported claim count.

## Build Order

1. Domain schemas and ports.
2. Local artifact memory bank.
3. DuckDB metadata store.
4. Docling parser adapter.
5. EvidenceSpan generation.
6. Dictionary/rule/table extraction.
7. Qdrant index and hybrid retrieval.
8. NetworkX graph adapter.
9. QA answer assembler.
10. Streamlit workbench.
11. Evaluation report.

## Deferral List

Do not build before P0 works:

- React frontend;
- Neo4j persistence;
- PostgreSQL;
- worker queues;
- full human review workflow;
- MatSciBERT/ChemDataExtractor integration;
- community/global GraphRAG summaries;
- complex ontology expansion.

## Success Criteria

- Demo corpus imports from a clean checkout.
- At least 10 demo questions run end to end.
- 100% final answer claims cite `EvidenceSpan`.
- At least 80% Recall@10 on demo QA evidence.
- Zero inaccessible evidence in answer context.
- Gap output appears for at least one material-regime-property combination.

## Scale Path

When the demo works:

- promote DuckDB to PostgreSQL for multi-user review and audit;
- promote NetworkX to Neo4j for persistent graph queries and Cypher;
- promote Streamlit to React for polished UX;
- promote in-process jobs to queue workers;
- promote local artifacts to S3-compatible object storage;
- add domain NLP and review workflow.
