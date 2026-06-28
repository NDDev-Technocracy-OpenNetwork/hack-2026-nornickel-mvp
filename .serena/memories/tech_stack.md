# Tech Stack

- P0 stack: Streamlit workbench, FastAPI/application services, Docling parser, local artifact store, DuckDB metadata/evidence ledger, Qdrant vector index, NetworkX graph materializer.
- DuckDB is P0 system of record for source registry, artifacts, evidence spans, facts, graph node/edge tables, answer claims, evaluations, ACL/security checks, and gap analytics.
- Qdrant is candidate retrieval only; never authoritative for facts or provenance.
- NetworkX materializes per-query `MultiDiGraph` neighborhoods from DuckDB graph node/edge tables; Neo4j is P1 adapter only.
- P1 migrations: DuckDB -> PostgreSQL, NetworkX -> Neo4j, Streamlit -> React, in-process jobs -> queue workers, local artifacts -> S3-compatible storage.
- Source-backed architecture docs: `.serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md` and `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`.