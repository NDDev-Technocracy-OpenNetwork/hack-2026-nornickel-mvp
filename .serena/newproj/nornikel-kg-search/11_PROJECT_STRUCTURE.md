# Proposed Project Structure

No scaffold code should be created until owner approval. After approval, use this minimal useful structure.

```text
.
├── apps
│   ├── api
│   │   ├── pyproject.toml
│   │   ├── src/nornikel_kg_api
│   │   │   ├── main.py
│   │   │   ├── modules
│   │   │   │   ├── sources
│   │   │   │   ├── ingestion
│   │   │   │   ├── entities
│   │   │   │   ├── graph
│   │   │   │   ├── retrieval
│   │   │   │   ├── qa
│   │   │   │   ├── gaps
│   │   │   │   └── review
│   │   │   └── shared
│   │   └── tests
│   └── workbench
│       ├── pyproject.toml
│       └── src/nornikel_kg_workbench
│           ├── app.py
│           ├── pages
│           └── components
├── packages
│   ├── domain
│   ├── ingestion
│   ├── retrieval
│   ├── graph
│   ├── qa
│   ├── evals
│   └── schemas
├── infra
│   ├── docker-compose.mvp.yml
│   ├── docker-compose.full.yml
│   └── qdrant
├── data
│   ├── README.md
│   └── sample
├── artifacts
│   └── README.md
├── docs
│   ├── architecture
│   └── demo
└── .serena
    └── newproj
```

## Module Boundaries

- `sources`: source registry and source spans.
- `ingestion`: parse, chunk, extract, resolve, index jobs.
- `entities`: canonical entity lookup and pages.
- `graph`: GraphStore port plus NetworkX and Neo4j adapters.
- `retrieval`: vector/hybrid search and reranking.
- `qa`: query planning, evidence assembly, answer generation.
- `gaps`: missing data and conflict analysis.
- `review`: human validation workflow.
- `shared`: settings, auth, logging, errors, persistence interfaces.

## Adapter Rule

Every external dependency must sit behind a port:

- `ArtifactStore`: local filesystem first, S3-compatible later.
- `MetadataStore`: DuckDB first, PostgreSQL later.
- `GraphStore`: NetworkX first, Neo4j later.
- `VectorStore`: Qdrant first, OpenSearch/pgvector later only if required.
- `ModelProvider`: configurable hosted or local model.
- `EmbeddingProvider`: dense and sparse embedding providers.
- `AuthProvider`: local stub first, SSO later.

## Data Directory Rule

Do not commit internal corpora. Only commit synthetic sample data and schema fixtures.

## Artifact Directory Rule

Runtime artifact memory bank files are generated from source corpora and must not be committed unless they are synthetic fixtures. The intended shape is:

```text
artifacts/
└── sources/
    └── src_...
        ├── original/
        ├── markdown/document.md
        ├── structured/document.json
        ├── tables/
        ├── images/
        └── manifest.json
```

## Migration Direction

Start modular monolith. Extract workers or services only when runtime pressure proves it necessary.
