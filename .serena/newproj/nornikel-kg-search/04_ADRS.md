# Architecture Decision Records

## ADR-001: Use Hybrid KG Plus Semantic Search

Status: Proposed

Decision: Build a hybrid system combining a canonical knowledge graph, vector/sparse retrieval, and grounded answer assembly.

Rationale:

- Target questions require both relationship traversal and text evidence retrieval.
- Graph-only systems struggle with incomplete extraction and narrative documents.
- Vector-only systems cannot reliably explain multi-hop material to regime to property to conclusion chains.

Consequences:

- More moving parts than a simple RAG app.
- Stronger demo value: answer, evidence, graph, conflicts, and gaps.
- Requires artifact memory bank discipline so generated Markdown remains traceable to structured source spans.

## ADR-002: Use Neo4j For Canonical Graph

Status: Proposed

Decision: Use Neo4j for graph storage and Cypher traversal in the MVP.

Rationale:

- Property graph fits material, experiment, regime, measurement, equipment, team, and document relationships.
- Neo4j GraphRAG tooling supports vector, full-text, hybrid, and Cypher-based retrieval patterns.
- Cypher is fast to demo and explain to stakeholders.

Consequences:

- Neo4j Community licensing must be reviewed before productization because it is GPLv3.
- Neo4j remains suitable for hackathon/demo use when deployed as a separate graph service and when license constraints are understood.

Alternatives:

- PostgreSQL plus recursive SQL: lower operational cost, weaker graph ergonomics.
- RDF triple store: strong ontology semantics, slower hackathon iteration.
- NetworkX only: useful for analytics prototypes, not a persistent multi-user graph.

## ADR-003: Use Qdrant For Hybrid Retrieval

Status: Proposed

Decision: Use Qdrant for dense plus sparse vectors and fusion-based hybrid retrieval.

Rationale:

- Hybrid retrieval is important for exact alloy names and semantic phrasing.
- Qdrant supports dense and sparse vectors, payload filters, and reciprocal-rank-fusion style hybrid queries.
- It keeps retrieval independent from the graph database.

Alternatives:

- OpenSearch: strong enterprise search option if the organization already operates it.
- pgvector: simpler stack, but less specialized for advanced hybrid retrieval and payload-heavy vector search.
- Neo4j vector only: fewer services, but mixes graph and retrieval concerns too early.

## ADR-004: Use PostgreSQL For Application State And Audit

Status: Proposed

Decision: Use PostgreSQL for source registry, jobs, review workflow, users, audit, and reproducibility metadata.

Rationale:

- These are relational workflow records, not graph facts.
- PostgreSQL is reliable, familiar, and easy to operate.

## ADR-005: Use FastAPI For Backend API

Status: Proposed

Decision: Use FastAPI for typed API services, OpenAPI docs, async endpoints, dependency injection, and background job integration.

Rationale:

- Python ecosystem is strongest for document parsing, embeddings, LLM extraction, scientific tooling, and rapid prototype work.
- FastAPI keeps contracts explicit and demoable.

## ADR-006: Keep LLM Provider Swappable

Status: Proposed

Decision: LLM extraction and answer generation must be behind provider interfaces.

Rationale:

- Internal document policy may require local/on-prem models.
- Hosted providers may be allowed only for anonymized or public data.
- Evaluation and provenance should not depend on one vendor.

## ADR-007: Provenance Is Mandatory

Status: Proposed

Decision: Every extracted fact and relationship must carry source span, extraction run, extractor type, confidence, validation status, and reviewer metadata where applicable.

Rationale:

- Scientific users need evidence and reproducibility.
- Provenance enables conflict detection, trust scoring, and audit.
