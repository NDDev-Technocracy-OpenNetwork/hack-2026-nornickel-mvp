<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 55e8e19 docs: integrate evidence-led mvp review
Scope: .serena/newproj/nornikel-kg-search/04_ADRS.md; .serena/newproj/nornikel-kg-search/05_TECH_STACK.md; .serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md; .serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md
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

## Entry Points

- Future `src/nornikel_kg/services/*`: application services to be called by API and Streamlit.
- Future `src/nornikel_kg/ports/*`: swappable adapter contracts.
- Future `apps/streamlit_app/`: judge-facing UI only.
- Future `services/api/`: thin API layer only.

## Current Behavior

P0 uses DuckDB as the system of record, Qdrant as candidate retrieval, NetworkX as per-query graph materialization, and Streamlit as a workbench. Neo4j, PostgreSQL, React, queues, and object storage are P1 migrations, not P0 dependencies.

## Contracts And Data

Required ports: `DocumentParserPort`, `ArtifactStorePort`, `MetadataStorePort`, `VectorIndexPort`, `GraphStorePort`, `EmbeddingModelPort`, `SparseEncoderPort`, `LLMExtractorPort`, `ACLPolicyPort`, and `EvaluationStorePort`.

Concrete P0 domain services should not be hidden behind generic RAG abstractions: `EvidenceSpanFactory`, `TableEvidenceBuilder`, `MaterialNormalizer`, `RegimeNormalizer`, `MeasurementNormalizer`, `ConflictDetector`, `GapAnalyzer`, `AnswerAssembler`, and `ClaimVerifier`.

## Invariants

- Domain logic depends on ports, not vendor clients.
- Streamlit must not perform long-running ingestion directly inside page reruns.
- If DuckDB and Qdrant disagree, DuckDB wins.
- Do not add Neo4j or PostgreSQL before the documented scale triggers become real.

## Change Rules

Keep implementation changes aligned with `18_IMPLEMENTATION_SPEC.md` first, then update ADRs if a stack boundary changes.

## Verification

- `git diff --check`: formatting gate for planning docs.
- `rg -n "Neo4j|PostgreSQL|DuckDB|Qdrant|NetworkX" .serena/newproj/nornikel-kg-search`: inspect stack references for consistency after architecture edits.

