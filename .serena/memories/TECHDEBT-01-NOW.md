<!-- Memory Metadata
Last updated: 2026-07-02
Last commit: 1bca77f Merge pull request #6 from rldyourmnd/feat/w0-alignment-and-seams
Scope: src/nornikel_kg/; apps/web/; services/api/; pyproject.toml; docker-compose.yml; docs/deployment/fa-nddev.md; .env.example; .github/workflows/ci.yml; tests/
Area: TECHDEBT
-->

# TECHDEBT-01-NOW

## Purpose

Capture verified scaffold gaps that matter for future implementation, without using memory as a backlog.

## Source Of Truth

- `src/nornikel_kg/services/qa_service.py`: deterministic QA assembly.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: synthetic ledger seed/load adapter; `migrate()` now also seeds graph dictionaries.
- `src/nornikel_kg/adapters/llm/`: LLM gateway/fake adapters, not yet called by any service.
- `docker-compose.yml`: Qdrant is present but not yet used by runtime retrieval.
- `docs/deployment/fa-nddev.md`: server deployment contract and smoke checks; not updated in wave W0.
- `.env.example`: open-weight LLM/embedding/Langfuse env matrix.
- `apps/web/nginx.conf`: bundled proxy `client_max_body_size`.
- `.github/workflows/ci.yml`: backend job does not install the `ingest` optional dependency group.
- `pyproject.toml`: dependency groups (`ingest`, `fixtures`, `dev`) and mypy overrides.
- `tests/`: current unit/integration coverage.

## Entry Points

- `DuckDBLedgerRepository.seed_synthetic_fixture`: current fixture ingestion path.
- `DemoQAService.ask`: current answer assembly path.
- `get_ledger_repository`: runtime seeding and DuckDB path resolution.
- `build_llm()` / `LiteLLMGateway` / `FakeLLM`: LLM adapter seam, currently unreferenced outside `src/nornikel_kg/adapters/llm/` and its tests.
- `resolve_alias()`: dictionary alias resolver, currently unreferenced outside `dictionary_loader.py` and its tests.

## Current Behavior

The scaffold is a working evidence-led product shell backed by a DuckDB ledger. It seeds a
synthetic Ni-Cu corpus and supports CSV/Markdown upload into source/evidence/fact tables. It does
not yet parse arbitrary uploaded PDFs/DOCX/PPTX/XLSX/images, does not build Qdrant indexes, and
does not call the LLM gateway for extraction or answer writing — `build_llm()`/`LiteLLMGateway`/
`FakeLLM` and `resolve_alias()` exist and are unit-tested but are not wired into
`qa_service.py`, `repositories.py` ingestion paths, or any API route.
QA requests now support filter-aware experiment selection with fallback behavior aligned
to filtered result sets.
`/qa/ask` now uses a typed `AskFilters` contract and rejects unknown filter keys at request parse time.
Scalar filter values are coerced to one-element lists to preserve API ergonomics.
The workbench now provides interactive QA filter controls (sources/material/property/regime/
experiment), which removes manual JSON request editing.
Free-text material queries with explicit composition numbers now use strict matching; unknown
tokens including `Ni-20`, `ni 20`, and `Ni–20` produce no evidence and clickable close-material
suggestions instead of generic family fallback results. Known spaced forms such as `Ni 30 Cu`
and `Cu Ni 30` are normalized to exact ledger materials.
Source lifecycle was hardened with:
- upload extension validation (`.csv`, `.md`, `.markdown`, `.txt`, `.text` only),
- filename, MIME, empty-file, and size validation at `/sources/upload`,
- `MAX_SOURCE_UPLOAD_BYTES` code default `5242880` bytes in `services/api/routes/sources.py`,
- transactional upload/seed paths in DuckDB repository,
- 404-aware source lookup and delete endpoints to avoid silent partial states.

FastAPI tests pass but emit a Starlette deprecation warning that `fastapi.testclient` currently
uses `httpx` and may require `httpx2` in a future dependency cycle.

`services/api/Dockerfile` was reworked in wave W0 to build with `uv` (locked, cache-mounted
`uv sync --frozen --no-dev --extra ingest`) instead of `pip install .`; the earlier tracked gap
about redownloading large wheels on every rebuild is resolved by this change.

## Contracts And Data

The current demo answer must remain evidence-first: answer summary sentences cite spans, evidence
cards expose `EvidenceSpan` IDs, and graph paths connect material, experiment, regime, step,
measurement, property, evidence, and document.

## Invariants

- Keep the deterministic synthetic demo green while adding real ingestion/retrieval.
- Do not let Qdrant become the authoritative evidence store.
- Do not introduce LLM-generated claims without supporting span IDs.
- Only `src/nornikel_kg/adapters/llm/gateway.py` may import `litellm` (enforced by test).

## Change Rules

Wire future ingestion in narrow steps: parser/artifact output first, DuckDB evidence writes second,
retrieval/indexing third, answer assembly last. Extend tests and eval fixtures with each step.

## Verification

- `make ci`: current scaffold regression gate (53 backend tests pass at `1bca77f`; `uv run ruff check .` and `uv run mypy` are clean).
- `make eval`: current evidence/safety smoke.
- Browser validation: verify the workbench still renders evidence cards, graph path, and metrics.

## Known Gaps

- Real Docling/OCR ingestion is not wired.
- Qdrant hybrid retrieval is not wired.
- The LLM gateway (`build_llm()`/`LiteLLMGateway`/`FakeLLM`) and dictionary `resolve_alias()`
  exist and are unit-tested but are not called from any ingestion or QA service; extraction and
  answer synthesis remain deterministic/rule-based in P0.
- Uploaded Markdown/text sources create evidence spans only; P0 does not extract measurements from
  prose uploads.
- `.env.example` samples `MAX_SOURCE_UPLOAD_BYTES=26214400` (25 MiB), but `apps/web/nginx.conf`
  still sets `client_max_body_size 6m`; the bundled proxy would reject uploads between 6 MiB and
  25 MiB before FastAPI's size check runs unless `client_max_body_size` is raised to match.
- `docs/deployment/fa-nddev.md` was not updated in wave W0: it still lists `OPENAI_API_KEY`/
  `LITELLM_API_BASE` as required runtime secrets and describes the 5 MiB default upload limit,
  which is now stale next to the `.env.example` open-weight LLM matrix, `README.md`'s new
  `https://nornikel.nddev.asia` live-stand line, and the `MAX_SOURCE_UPLOAD_BYTES=26214400`
  sample value.
- `LLM_EXTRACTION_MODEL`/`LLM_ANSWER_MODEL` are blank in `.env.example` pending W0.1 provider
  discovery against the `dataeyes.ai` catalog (`.serena/plans/03_IMPLEMENTATION_PLAN.md` row
  0.1); `LLMSettings.model_for()` raises `ValueError` if a task model is not configured.
- `.github/workflows/ci.yml` backend job runs `uv sync --group dev` without `--extra ingest`, so
  the new `ingest`-only dependencies (`docling`, `fastembed`, `gliner`, `sentence-transformers`,
  `trafilatura`) are not installed or exercised by `pytest` in CI.
