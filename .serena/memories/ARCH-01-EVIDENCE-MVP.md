<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 5acab4a docs: lock implementation decisions
Scope: .serena/newproj/nornikel-kg-search/04_ADRS.md; .serena/newproj/nornikel-kg-search/05_TECH_STACK.md; .serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md; .serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md; .serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md
Area: ARCH
-->

# ARCH-01-EVIDENCE-MVP

## Purpose

Capture the P0 architecture contract for the evidence-first materials research workbench.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: implementation source of truth for scaffold decisions.
- `.serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md`: MVP loop, modules, and build order.
- `.serena/newproj/nornikel-kg-search/04_ADRS.md`: accepted decisions and deferred migrations.
- `.serena/newproj/nornikel-kg-search/05_TECH_STACK.md`: current technology choices and migration path.
- `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`: approved implementation/deployment decisions.

## Entry Points

- Future `src/nornikel_kg/services/*`: application services to be called by FastAPI and future workers.
- Future `src/nornikel_kg/ports/*`: swappable adapter contracts.
- Future `apps/web/`: React/Vite workbench.
- Future `services/api/`: thin API layer only.

## Current Behavior

P0 uses React 19/Vite 8/TypeScript for the workbench, FastAPI for the API, Python 3.12 for backend/scientific code, DuckDB as the system of record, Qdrant as candidate retrieval, NetworkX as per-query graph materialization, and LiteLLM/OpenAI-compatible external APIs for LLM/embeddings. Neo4j, PostgreSQL, queues, and object storage are P1 migrations.

## Contracts And Data

Required ports: `DocumentParserPort`, `ArtifactStorePort`, `MetadataStorePort`, `VectorIndexPort`, `GraphStorePort`, `EmbeddingModelPort`, `SparseEncoderPort`, `LLMExtractorPort`, `SecurityLabelPolicyPort`, and `EvaluationStorePort`.

Concrete P0 domain services should not be hidden behind generic RAG abstractions: `EvidenceSpanFactory`, `TableEvidenceBuilder`, `MaterialNormalizer`, `RegimeNormalizer`, `MeasurementNormalizer`, `ConflictDetector`, `GapAnalyzer`, `AnswerAssembler`, and `ClaimVerifier`.

## Invariants

- Domain logic depends on ports, not vendor clients.
- React must call FastAPI contracts and must not bypass application services.
- If DuckDB and Qdrant disagree, DuckDB wins.
- Do not add Neo4j or PostgreSQL before the documented scale triggers become real.
- Deploy target is `fa.nddev.asia` through Docker Compose on `ssh server-nddev`.

## Change Rules

Keep implementation changes aligned with `18_IMPLEMENTATION_SPEC.md` first, then update ADRs if a stack boundary changes.

## Verification

- `git diff --check`: formatting gate for planning docs.
- `rg -n "Neo4j|PostgreSQL|DuckDB|Qdrant|NetworkX" .serena/newproj/nornikel-kg-search`: inspect stack references for consistency after architecture edits.
