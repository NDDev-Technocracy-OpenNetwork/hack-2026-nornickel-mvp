# Infrastructure

## MVP-Lite Deployment

Use a local-first deployment for the first working demo:

- `workbench`: Streamlit app;
- `api`: FastAPI backend, optional in early local mode but required for clean contracts;
- `duckdb`: local database file for source registry, facts, evaluations, and gap analytics;
- `qdrant`: local Docker container or embedded/local test mode where acceptable;
- `artifacts/`: local generated artifact memory bank.

P1/productization adds:

- `postgres`: app state and audit;
- `neo4j`: persistent graph database;
- `worker`: ingestion and extraction queue workers;
- `frontend`: React app;
- `minio` or S3-compatible object storage.

## Environment Configuration

Required configuration groups:

- metadata store URL/path;
- graph adapter setting;
- graph database URL and credentials when using Neo4j;
- vector database URL;
- object storage path/bucket;
- LLM provider configuration;
- embedding provider configuration;
- auth mode;
- security label defaults;
- logging level.

Secrets must live outside the repository.

## Jobs

Ingestion stages:

1. source_register;
2. parse;
3. chunk;
4. dictionary_import;
5. extract;
6. resolve_entities;
7. write_graph_path;
8. index_vectors;
9. quality_report.

Each stage must be retryable and idempotent. In MVP-lite, stages can run synchronously but must still persist job state in DuckDB so failed parsing or extraction is visible.

## Observability

Log structured events:

- request ID;
- user ID;
- source ID;
- job ID;
- extraction run ID;
- QA run ID;
- retrieval plan;
- graph query ID;
- vector query ID;
- latency;
- error class.

For MVP, structured JSON logs are enough. Later, add OpenTelemetry traces and metrics dashboards.

## Backups

MVP:

- snapshot DuckDB file;
- snapshot Qdrant collection;
- archive artifact memory bank;
- keep original source files immutable.

P1:

- export Neo4j dump after successful demo ingestion;
- snapshot PostgreSQL volume;

Production direction:

- scheduled database backups;
- object storage versioning;
- migration plan for schema changes;
- disaster recovery runbook.

## Scaling Path

- Move workers to queue-backed service.
- Promote DuckDB metadata store to PostgreSQL when concurrent writes, multi-user review, or audit requirements demand it.
- Promote NetworkX graph adapter to Neo4j when graph size, Cypher querying, or persistent graph exploration demand it.
- Split parser/extractor/indexer workloads.
- Add caching for entity pages and repeated QA queries.
- Add graph precomputed neighborhoods for high-traffic materials.
- Add offline graph analytics for central materials, missing links, and team expertise.
