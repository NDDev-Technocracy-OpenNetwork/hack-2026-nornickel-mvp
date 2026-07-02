<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: ece33d3 docs(plans): record completed dataeyes discovery and configured dev model
Scope: README.md; apps/web/; services/api/; src/nornikel_kg/; eval/; sample_docs/; tests/; docker-compose.yml; .github/workflows/ci.yml; .env.example; pyproject.toml; .serena/plans/; .serena/reviews/; docs/deployment/
Area: CORE
-->

# CORE-01-INDEX

## Purpose

Index the durable project knowledge for the Nornikel Materials KG Search hackathon MVP.

## Source Of Truth

- `README.md`: repository overview, quick start, demo scenario, and implemented W0-W5 scope.
- `AGENTS.md`: Codex-native project instructions and plugin/tooling policy.
- `.claude/CLAUDE.md`: Claude Code project memory and operational commands.
- `apps/web/`: React/Vite analysis workbench.
- `services/api/`: FastAPI route layer.
- `src/nornikel_kg/`: backend domain, ports, adapters, and application services.
- `eval/`: legacy YAML gold/adversarial fixtures (`eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml`); these files are no longer read by any code path (see `mem:TEST-01-EVALUATION-GATES`).
- `sample_docs/synthetic/`: original P0 fixture. `sample_docs/synthetic_v2/`: W5 17-source synthetic corpus with `manifest.json`.
- `tests/`: unit and integration tests.
- `docs/deployment/nornikel-nddev.md`: primary live-stand deployment contract (W5).
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: primary scaffold contract for P0 implementation.
- `.serena/plans/00_PLAN_INDEX.md`: 2026-07-02 MVP implementation plan package (waves W0-W5), now fully implemented per this memory set.
- `.serena/reviews/`: tracked plan critical review and research evidence register.

## Entry Points

- `mem:ARCH-01-EVIDENCE-MVP`: architecture, module boundaries, ports/adapters, and stack decisions.
- `mem:DATA-01-EVIDENCE-LEDGER`: evidence IDs, DuckDB ledger, graph/entity schema, and answer claims.
- `mem:SEC-01-ACL-AND-PROMPT-INJECTION`: source-label filtering, prompt-injection, and internal-document safety invariants.
- `mem:TEST-01-EVALUATION-GATES`: required checks, metrics, and acceptance gates.
- `mem:DOCS-01-PLANNING-SOURCE`: planning-doc ownership and current implementation status.
- `mem:RELEASE-01-VALIDATION`: validation, CI, Compose, and deployment checks.
- `mem:TECHDEBT-01-NOW`: verified current gaps and migration triggers.

## Current Behavior

Waves W0-W5 (merge commits `1bca77f` PR#6, `d27bf88` PR#7, `824e19a` PR#8, `b117459` PR#9,
`f9b0830` PR#10, `f4bf404` PR#11) closed the ingest/extraction/retrieval/frontend/corpus
gaps that were open at W0. The system now:

- Parses PDF/DOCX with Docling (`src/nornikel_kg/adapters/docling/parser.py`, text layer only,
  `do_ocr=False`) and fetches URLs with trafilatura
  (`src/nornikel_kg/adapters/trafilatura/fetcher.py`); parser/no-text-layer failures quarantine
  the source instead of returning 500 (`src/nornikel_kg/services/ingestion_service.py`).
- Extracts entities/relations via dictionary alias-scan (always), optional GLiNER zero-shot NER
  (`GLINER_ENABLED`, default `true`), and optional LLM guided-JSON extraction with an
  `extraction_claims` audit trail (`src/nornikel_kg/services/extraction_service.py`), resolved
  through `EntityResolutionService` (`src/nornikel_kg/services/entity_resolution.py`) and
  materialized on demand as a NetworkX `MultiDiGraph`
  (`src/nornikel_kg/services/graph_service.py`).
- Retrieves via Qdrant hybrid dense+sparse search with RRF fusion
  (`src/nornikel_kg/adapters/qdrant_index/index.py`, USER-bge-m3 dense +
  fastembed/Qdrant-bm25 sparse in `src/nornikel_kg/adapters/embeddings/local.py`), gated by
  `EMBEDDING_BACKEND=off|local|fake` and always rejoined/rechecked against DuckDB
  (`src/nornikel_kg/services/retrieval_service.py`).
- Synthesizes answers with an LLM composer that only cites `span_id`s from the evidence
  packet, with one regeneration and a deterministic fallback
  (`src/nornikel_kg/services/answer_composer.py`); every `/qa/ask` call is recorded to
  `answer_runs` and replayable via `GET /qa/runs/{run_id}`.
- Detects conflicts (`contradictory_direction`, `method_mismatch`, `numeric_disagreement > 15%`
  under the same method) and computes a material x regime x property coverage/gap matrix
  (`src/nornikel_kg/domain/analysis.py`, `GET /gaps/analyze`).
- Ships a synthetic corpus v2 of 17 committed sources (4 CSV, 6 RU DOCX, 3 RU MD, 2 EN PDF,
  1 image-only quarantine PDF, 1 HTML) under `sample_docs/synthetic_v2/` with a matching
  `manifest.json`, generated deterministically by `scripts/generate_synthetic_docs.py`.

`uv run pytest` passes **90 tests, 3 skipped** at `ece33d3` (skips are `docling`/`trafilatura`
`importorskip` guards in `tests/integration/test_synthetic_v2_corpus.py` when those optional
`ingest` extras are not installed); `uv run ruff check .` and `uv run mypy` report no issues.
Merge commits `edfa173` (PR#13, LLM gateway `_strictify` strict-mode fix) and `7456565` (PR#14,
answer-composer/extraction-service inline JSON-format hints and one-retry validation) hardened
the LLM gateway/composer path after `f4bf404`; `.serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md`
records the completed `dataeyes.ai` key discovery (`ece33d3`, see `mem:TECHDEBT-01-NOW`).

## Contracts And Data

Full flow: React/Vite workbench -> FastAPI (`/sources/upload`, `/sources/import-url`,
`/qa/ask`, `/entities/search`, `/entities/{id}`, `/graph/neighborhood`, `/graph/timeline`,
`/gaps/analyze`, `/eval/summary`) -> DuckDB-backed evidence ledger + entity/relation graph ->
optional Qdrant retrieval augmentation -> deterministic-or-LLM answer synthesis -> claim
verification -> answer-run persistence.

Upload accepts `.csv`, `.md`, `.markdown`, `.txt`, `.text`, `.pdf`, `.docx` with filename/MIME/
size validation (`services/api/routes/sources.py`); `MAX_SOURCE_UPLOAD_BYTES` code default is
`5242880` bytes; bundled web Nginx sets `client_max_body_size 6m` and `proxy_read_timeout 300s`
for `/api/` (`apps/web/nginx.conf`, needed for slow Docling/embedding-model cold starts).

## Invariants

- Do not treat Markdown chunks as source of truth; they are convenience views only.
- Every answer sentence must map to exact evidence IDs.
- DuckDB is authoritative for facts and provenance; if DuckDB and Qdrant disagree, DuckDB wins.
- Qdrant is retrieval-only; NetworkX is graph materialization-only, rebuilt on demand from DuckDB.
- React/Vite and FastAPI are P0 UI/API layers, not P1.
- No OCR: PDFs without a text layer are quarantined, never OCR'd (`NoTextLayerError`).
- Only `src/nornikel_kg/adapters/llm/gateway.py` may `import litellm`.

## Change Rules

Update this index whenever a new durable memory is added, renamed, split, or deleted.

## Verification

- `make ci`: verifies backend ruff/mypy/pytest and frontend typecheck/build.
- `make eval`: runs `scripts/run_eval.py` (12 hardcoded `EVAL_QUESTIONS`).
- `docker compose config`: verifies Compose syntax without requiring local secrets.
- `uv run pytest`: 90 tests pass, 3 skipped at `ece33d3`; `uv run ruff check .` and
  `uv run mypy` report no issues.
