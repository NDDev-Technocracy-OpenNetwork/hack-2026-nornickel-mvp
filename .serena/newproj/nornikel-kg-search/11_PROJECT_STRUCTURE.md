# Proposed Project Structure

No scaffold code should be created until owner approval. After approval, use this minimal useful structure.

```text
.
├── pyproject.toml
├── uv.lock
├── Makefile
├── docker-compose.yml
├── .env.example
├── apps
│   └── streamlit_app
│       ├── Home.py
│       ├── pages
│       │   ├── 1_Import.py
│       │   ├── 2_Artifact_Bank.py
│       │   ├── 3_Extraction_Workbench.py
│       │   ├── 4_Ask.py
│       │   ├── 5_Graph.py
│       │   └── 6_Evaluation.py
│       └── components
│           ├── evidence_card.py
│           ├── experiment_table.py
│           ├── graph_view.py
│           └── metrics_panel.py
├── services
│   └── api
│       ├── main.py
│       ├── routes
│       │   ├── ingest.py
│       │   ├── query.py
│       │   ├── evidence.py
│       │   ├── graph.py
│       │   └── eval.py
│       └── schemas.py
├── src
│   └── nornikel_kg
│       ├── domain
│       │   ├── ids.py
│       │   ├── models.py
│       │   ├── evidence.py
│       │   ├── materials.py
│       │   ├── regimes.py
│       │   ├── measurements.py
│       │   ├── effects.py
│       │   ├── conflicts.py
│       │   ├── gaps.py
│       │   └── answer_claims.py
│       ├── ports
│       │   ├── artifact_store.py
│       │   ├── metadata_store.py
│       │   ├── parser.py
│       │   ├── vector_index.py
│       │   ├── graph_store.py
│       │   ├── embedding_model.py
│       │   ├── sparse_encoder.py
│       │   ├── llm_client.py
│       │   └── acl_policy.py
│       ├── adapters
│       │   ├── artifact_fs
│       │   ├── duckdb
│       │   │   └── migrations
│       │   │       └── 001_init.sql
│       │   ├── docling
│       │   ├── qdrant
│       │   ├── networkx
│       │   └── llm
│       ├── pipelines
│       │   ├── ingest.py
│       │   ├── build_evidence.py
│       │   ├── extract.py
│       │   ├── normalize.py
│       │   ├── index.py
│       │   ├── answer.py
│       │   ├── evaluate.py
│       │   └── security_checks.py
│       ├── services
│       │   ├── ingestion_service.py
│       │   ├── extraction_service.py
│       │   ├── indexing_service.py
│       │   ├── qa_service.py
│       │   ├── graph_service.py
│       │   └── evaluation_service.py
│       └── resources
│           ├── dictionaries
│           │   ├── materials.yml
│           │   ├── properties.yml
│           │   ├── regimes.yml
│           │   ├── units.yml
│           │   ├── equipment.yml
│           │   └── teams.yml
│           ├── prompts
│           │   ├── extract_fact.json.md
│           │   ├── answer_from_evidence.md
│           │   └── verify_claims.md
│           └── fixtures
│               ├── gold_questions.yml
│               ├── adversarial_questions.yml
│               └── expected_spans.yml
├── data
│   ├── .gitkeep
│   ├── catalog.duckdb
│   ├── artifacts
│   └── qdrant_storage
├── eval
│   ├── gold_questions.yml
│   ├── adversarial_questions.yml
│   └── expected_spans.yml
├── sample_docs
│   └── README.md
├── tests
│   ├── unit
│   └── integration
├── docs
│   ├── architecture
│   └── demo
└── .serena
    └── newproj
```

## Module Boundaries

- `domain`: stable scientific schemas and invariants.
- `ports`: dependency boundaries for stores, parsers, models, auth, graph, and retrieval.
- `adapters`: concrete MVP-lite implementations.
- `pipelines`: executable ingestion, evidence, extraction, indexing, QA, evaluation, and security flows.
- `services`: application service orchestration used by API and Streamlit.
- `apps/streamlit_app`: judge-facing workbench only.
- `services/api`: stable API contracts only; keep business logic in `src/nornikel_kg/services`.

## Adapter Rule

Every external dependency must sit behind a port:

- `ArtifactStore`: local filesystem first, S3-compatible later.
- `MetadataStore`: DuckDB first, PostgreSQL later.
- `GraphStore`: DuckDB edge tables plus NetworkX first, Neo4j later.
- `VectorStore`: Qdrant first, OpenSearch/pgvector later only if required.
- `DocumentParser`: Docling first, parser bakeoff alternatives later.
- `ModelProvider`: configurable hosted or local model.
- `EmbeddingProvider`: dense and sparse embedding providers.
- `AuthProvider`: local stub first, SSO later.

## Required Make Targets

- `make install`: install local development dependencies.
- `make test`: run unit and integration tests.
- `make ingest-fixtures`: ingest curated sample documents.
- `make eval`: run gold and adversarial evaluation.
- `make demo`: start the Streamlit workbench and required local services.

## Data Directory Rule

Do not commit internal corpora. Only commit synthetic sample data and schema fixtures.

## Artifact Directory Rule

Runtime artifact memory bank files are generated from source corpora and must not be committed unless they are synthetic fixtures. The intended shape is:

```text
data/artifacts/
└── sources/
    └── src_...
        ├── raw/
        ├── manifest.json
        ├── docling/document.md
        ├── docling/document.json
        ├── pages/
        ├── tables/
        ├── figures/
        ├── chunks/
        └── extraction/
```

## Migration Direction

Start with a modular Python application. Promote adapters only when the P0 evidence loop works and the scale trigger is real:

- DuckDB to PostgreSQL for multi-user review/audit.
- NetworkX to Neo4j for durable graph queries and Cypher.
- Streamlit to React for polished production UX.
- In-process jobs to worker queues for long ingestion.
- Local artifacts to object storage for shared deployment.
