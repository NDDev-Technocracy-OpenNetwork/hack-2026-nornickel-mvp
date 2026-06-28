# Nornikel Materials KG Search

Private planning repository for the Nornikel hackathon MVP.

The product direction is an evidence-first materials research workbench:

- artifact memory bank for source documents;
- exact `EvidenceSpan` provenance;
- hybrid retrieval over Markdown chunks, tables, claims, and entity summaries;
- typed material-regime-property graph paths;
- grounded answers with experiment tables, evidence, conflicts, and gaps.

Planning documents live in `.serena/newproj/nornikel-kg-search/`.

Current implementation recommendation:

- build MVP-lite first with Streamlit, FastAPI, DuckDB, Qdrant, NetworkX, Docling, and local artifacts;
- keep PostgreSQL, Neo4j, React, queues, and object storage as P1 adapters;
- do not scaffold application code until the owner approves the P0 build plan.
