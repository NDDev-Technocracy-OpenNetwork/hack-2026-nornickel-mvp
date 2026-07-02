<!-- Memory Metadata
Last updated: 2026-07-02
Last commit: 1bca77f Merge pull request #6 from rldyourmnd/feat/w0-alignment-and-seams
Scope: apps/web/; services/api/; src/nornikel_kg/; docker-compose.yml; .github/workflows/ci.yml; pyproject.toml; .serena/newproj/nornikel-kg-search/; README.md
Area: ARCH
-->

# ARCH-01-EVIDENCE-MVP

## Purpose

Capture the P0 architecture contract for the evidence-first materials research workbench.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: implementation source of truth for scaffold decisions.
- `.serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md`: MVP loop, modules, and build order.
- `.serena/newproj/nornikel-kg-search/04_ADRS.md`: accepted decisions and deferred migrations.
- `.serena/newproj/nornikel-kg-search/05_TECH_STACK.md`: current technology choices; the "LLM And Embeddings" defaults section was amended 2026-07-02 (commit `d5e61fa`) to open-weight-only models, withdrawing the earlier `openai/gpt-5.5-mini` / `openai/text-embedding-3-large` defaults.
- `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`: approved implementation/deployment decisions, amended 2026-07-02 to defer to `.serena/plans/01_MVP_SCOPE_AND_DECISIONS.md` on LLM/embeddings choices.

## Entry Points

- `src/nornikel_kg/services/qa_service.py`: deterministic evidence-backed QA assembly and claim verification.
- `src/nornikel_kg/services/runtime.py`: runtime factory that seeds and loads the DuckDB ledger.
- `src/nornikel_kg/ports/ledger.py`: evidence ledger port boundary.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: DuckDB repository for seeded and uploaded evidence sources; `migrate()` also seeds the graph dictionaries (see `mem:DATA-01-EVIDENCE-LEDGER`).
- `src/nornikel_kg/ports/llm.py`: `LLMPort` protocol (`generate_json(task, system_prompt, user_prompt, json_schema, trace_id, tags)` returning `LLMResult`), plus the `LLMError`/`LLMInvalidResponseError`/`LLMBudgetExceededError` hierarchy.
- `src/nornikel_kg/adapters/llm/__init__.py`: `build_llm(settings=None)` factory; returns `FakeLLM` unless `LLMSettings.llm_enabled` is true, in which case it lazily imports and returns `LiteLLMGateway`.
- `src/nornikel_kg/adapters/llm/gateway.py`: `LiteLLMGateway` — the only module in the repository allowed to `import litellm`; runs guided `json_schema` completions at `temperature=0` with a request timeout, bounded retries, a `threading.BoundedSemaphore` concurrency cap, a `TokenBudget` hard stop, and optional Langfuse success/failure callbacks when `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` are set.
- `src/nornikel_kg/adapters/llm/fake.py`: `FakeLLM` — deterministic canned/queued JSON responses for CI, tests, and the offline demo path.
- `src/nornikel_kg/adapters/llm/settings.py`: `LLMSettings` (pydantic-settings) reads the LLM/embedding/Langfuse env matrix.
- `apps/web/src/`: React/Vite workbench organized by app/pages/widgets/features/entities/shared.
- `services/api/`: thin FastAPI route layer.

## Current Behavior

P0 scaffold uses React 19/Vite 8/TypeScript for the workbench, FastAPI for the API, Python 3.12 for backend/scientific code, and DuckDB as the current evidence ledger. Runtime seeds the synthetic fixture and can ingest CSV/Markdown sources through `/sources/upload`; source lifecycle also supports `DELETE /sources/{source_id}` and safe evidence listing at `/sources/{source_id}/evidence`.

Wave W0 added an `LLMPort`/adapter seam behind `build_llm()`: `LLM_ENABLED=false` (the default, and the CI/test invariant) returns `FakeLLM` and never imports `litellm`; `tests/unit/test_llm_gateway.py::test_litellm_imported_only_inside_llm_adapter` scans `src/nornikel_kg` and fails if any file outside `adapters/llm` imports `litellm`. `pyproject.toml` adds a `[[tool.mypy.overrides]]` entry that sets `ignore_missing_imports = true` and `follow_imports = "skip"` for `litellm`/`langfuse`, since those packages are not part of the strict-mypy dependency closure otherwise. Neither `build_llm()`/`LiteLLMGateway` nor the new dictionary-loader `resolve_alias()` is called by any ingestion or QA service yet — they exist as tested, unwired seams.

Upload hardening is split across FastAPI validation and the web Nginx proxy limit so production uploads receive structured API errors instead of proxy-level body-size failures.

Qdrant is present in Compose and dependency configuration but is not yet used by the QA runtime. NetworkX, Docling/OCR, and embedding calls are P1 adapter wiring paths. Neo4j, PostgreSQL, queues, and object storage remain deferred migrations.

## Contracts And Data

Implemented ports: `EvidenceLedgerPort` (source listing, evidence listing, source upload, source deletion, evidence packet loading) and `LLMPort` (`generate_json` for `extraction`/`answer` tasks, implemented by `LiteLLMGateway` and `FakeLLM`).

Workbench now renders user-configured filter controls that serialize typed `AskFilters` into
`/qa/ask`.
Workbench also renders clickable `follow_up_queries` when QA returns no exact material match,
allowing the user to rerun a corrected query without accepting unrelated evidence.

Planned ports remain: `DocumentParserPort`, `ArtifactStorePort`, `MetadataStorePort`, `VectorIndexPort`, `GraphStorePort`, `EmbeddingModelPort`, `SparseEncoderPort`, `SecurityLabelPolicyPort`, and `EvaluationStorePort`. `LLMExtractorPort` from the original plan is superseded by the generic `LLMPort`, which already covers both the extraction and answer tasks through the `task` argument.

Concrete P0 domain services should not be hidden behind generic RAG abstractions: `EvidenceSpanFactory`, `TableEvidenceBuilder`, `MaterialNormalizer`, `RegimeNormalizer`, `MeasurementNormalizer`, `ConflictDetector`, `GapAnalyzer`, `AnswerAssembler`, and `ClaimVerifier`.

## Invariants

- Domain logic depends on ports, not vendor clients.
- React must call FastAPI contracts and must not bypass application services.
- If DuckDB and Qdrant disagree, DuckDB wins.
- Do not add Neo4j or PostgreSQL before the documented scale triggers become real.
- Only `src/nornikel_kg/adapters/llm/gateway.py` may `import litellm`; enforced by `tests/unit/test_llm_gateway.py::test_litellm_imported_only_inside_llm_adapter`.
- `README.md` documents the live stand as `https://nornikel.nddev.asia`, with `https://fa.nddev.asia` as an interim mirror; `docs/deployment/fa-nddev.md` was not updated in this wave and still describes only the `fa.nddev.asia` server-only Compose override (see `mem:TECHDEBT-01-NOW` for the resulting doc drift).

## Change Rules

Keep implementation changes aligned with `18_IMPLEMENTATION_SPEC.md` first, then update ADRs if a stack boundary changes.

## Verification

- `git diff --check`: formatting gate for planning docs.
- `make ci`: backend/frontend scaffold gate (`uv run ruff check .`, `uv run mypy`, `uv run pytest` — 53 tests pass at `1bca77f` — plus frontend typecheck/build).
- `make eval`: deterministic evidence packet verification.
- `docker compose config`: validates server-first Compose wiring.
- Browser validation: ignored `browser/ledger-fixed-*.png` and `browser/ledger-fixed-*.yaml`
  artifacts prove the desktop query/upload flow and mobile layout; do not commit them.
