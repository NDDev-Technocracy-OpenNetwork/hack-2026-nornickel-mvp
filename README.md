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

- build the MVP as a server-first React + FastAPI product, backed by DuckDB, Qdrant, NetworkX, Docling, and local artifacts;
- keep PostgreSQL, Neo4j, queues, and object storage as P1 adapters;
- treat DuckDB as the P0 system of record and Qdrant as retrieval only;
- require every final answer sentence to cite exact `EvidenceSpan` IDs;
- use `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md` as the scaffold contract;
- use `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md` for implementation decisions;
- scaffold/application implementation is now approved and should proceed in logical branches from `main`.
