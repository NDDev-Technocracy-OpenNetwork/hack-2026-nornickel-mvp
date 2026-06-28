<!-- Memory Metadata
Last updated: 2026-06-29
Last commit: a3bf103 feat: expose QA filters in frontend workbench
Scope: apps/web/; services/api/; src/nornikel_kg/; docker-compose.yml; .github/workflows/ci.yml; .serena/newproj/nornikel-kg-search/
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

- `src/nornikel_kg/services/qa_service.py`: deterministic evidence-backed QA assembly and claim verification.
- `src/nornikel_kg/services/runtime.py`: runtime factory that seeds and loads the DuckDB ledger.
- `src/nornikel_kg/ports/ledger.py`: evidence ledger port boundary.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: DuckDB repository for seeded and uploaded evidence sources.
- `apps/web/src/`: React/Vite workbench organized by app/pages/widgets/features/entities/shared.
- `services/api/`: thin FastAPI route layer.

## Current Behavior

P0 scaffold uses React 19/Vite 8/TypeScript for the workbench, FastAPI for the API, Python 3.12 for backend/scientific code, and DuckDB as the current evidence ledger. Runtime seeds the synthetic fixture and can ingest CSV/Markdown sources through `/sources/upload`; source lifecycle now also supports
`DELETE /sources/{source_id}` and safe evidence listing at `/sources/{source_id}/evidence`.
Qdrant is present in Compose and dependency configuration but is not yet used by the QA runtime. NetworkX, Docling/OCR, and LiteLLM/OpenAI-compatible LLM/embedding calls are P1 adapter wiring paths. Neo4j, PostgreSQL, queues, and object storage remain deferred migrations.

## Contracts And Data

Current implemented port: `EvidenceLedgerPort`. It covers source listing, evidence listing,
source upload, source deletion, and evidence packet loading.
Workbench now renders user-configured filter controls that serialize typed `AskFilters` into
`/qa/ask`.

Planned ports remain: `DocumentParserPort`, `ArtifactStorePort`, `MetadataStorePort`, `VectorIndexPort`, `GraphStorePort`, `EmbeddingModelPort`, `SparseEncoderPort`, `LLMExtractorPort`, `SecurityLabelPolicyPort`, and `EvaluationStorePort`.

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
- `make ci`: backend/frontend scaffold gate.
- `make eval`: deterministic evidence packet verification.
- `docker compose config`: validates server-first Compose wiring.
- Browser validation: ignored `browser/ledger-fixed-*.png` and `browser/ledger-fixed-*.yaml`
  artifacts prove the desktop query/upload flow and mobile layout; do not commit them.
