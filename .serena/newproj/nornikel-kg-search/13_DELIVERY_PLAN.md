# Delivery Plan

## Hackathon Plan

## Critical Path

Do not start with a broad knowledge graph. Start with one vertical slice:

```text
sample corpus
-> artifact memory bank
-> EvidenceSpan IDs
-> material/regime/property/measurement extraction
-> canonical graph path
-> hybrid retrieval
-> answer table with citations
-> gap result
```

This path must work before graph visualization, domain NLP, or community-level GraphRAG summaries.

## MVP-Lite Delivery Principle

Use the lightest adapter that proves the product contract:

- DuckDB before PostgreSQL.
- NetworkX before Neo4j.
- Streamlit before React.
- In-process job runner before worker queues.
- Local artifact directory before object storage.

The code must still be written through ports so each adapter can be replaced without changing domain logic.

## Pre-Code Must-Fix Checklist

- Freeze ID policy for `source_id`, `artifact_id`, `span_id`, `extraction_run_id`, `fact_id`, and `claim_id`.
- Make DuckDB the P0 system of record.
- Treat table rows and cells as first-class evidence.
- Define `EffectClaim`, `ConflictGroup`, `DataGap`, and `answer_claims`.
- Create 10-20 gold questions, including success, conflict, gap, ACL, and prompt-injection cases.
- Decide LLM/embedding data boundary for internal documents.
- Enforce ACL filtering before LLM context construction.
- Make answer output a claim ledger, not a prose blob.

### Phase 0: Owner Decisions

Before scaffold:

- confirm MVP priority;
- confirm LLM policy;
- confirm corpus format;
- confirm demo dataset constraints;
- confirm whether Docker Compose is acceptable.
- pick 1-3 material families, 3-5 process regimes, and 5-10 properties for the demo slice.

### Phase 1: Foundation

Deliver:

- repository scaffold;
- local Python workspace for API, workbench, domain packages, and tests;
- Docker Compose MVP profile for Qdrant only, plus full profile for future PostgreSQL/Neo4j;
- source registry schema;
- artifact memory bank layout and manifest schema;
- minimal domain schemas;
- seed dictionaries for materials, equipment, teams, and properties.
- one synthetic or approved sample corpus that can be committed or safely mounted locally.
- gold/adversarial question fixtures and expected evidence spans.

### Phase 2: Ingestion

Deliver:

- PDF/DOCX/CSV ingest;
- Docling-based Markdown plus structured JSON conversion;
- optional GROBID path for scholarly PDFs;
- extracted table/image artifacts;
- chunking with stable source spans;
- structured extraction into candidate facts;
- entity resolution against dictionaries;
- graph path materialization through NetworkX adapter;
- vector index in Qdrant.
- quarantine queue for parse failures and low-confidence spans.

### Phase 3: Search And Graph

Deliver:

- hybrid search endpoint;
- entity lookup;
- graph path/neighborhood endpoint backed by GraphStore port;
- experiment/property comparison query;
- gap detection prototype.
- answer claim verifier with unsupported-claim blocking.

### Phase 4: QA And UI

Deliver:

- research workbench UI;
- QA answer with citations;
- evidence table;
- graph path view;
- gap board;
- timeline if the P0 answer path is already stable;
- review queue basics if extraction confidence issues are blocking demo trust.

### Phase 5: Evaluation And Demo

Deliver:

- seed demo corpus;
- 10-20 demo questions;
- retrieval/evidence report;
- demo script;
- risk list and production roadmap.

## Demo Script

1. Upload or import the corpus.
2. Show ingestion status and extracted entity counts.
3. Ask: "What has already been done for alloy X under regime Y, and what effect was observed on property Z?"
4. Open evidence table and source snippets.
5. Show graph path from alloy to experiment to regime to measurement to conclusion.
6. Show related equipment and team.
7. Show timeline of decisions.
8. Show missing or conflicting data.
9. Approve a candidate fact and show graph/search update.

## Production Roadmap

After hackathon:

- integrate corporate SSO and authorization model;
- connect live source systems;
- expand ontology and validation rules;
- build human review workflows;
- add offline graph analytics;
- add scheduled ingestion;
- add full audit and compliance controls;
- scale evaluation with curated gold datasets.

## Explicit Approval Gate

Scaffold code should start only after the owner approves:

- stack choice;
- MVP priority;
- LLM policy;
- corpus access mode;
- security posture;
- demo timeline.
