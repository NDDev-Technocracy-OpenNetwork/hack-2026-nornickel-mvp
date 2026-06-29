<!-- Memory Metadata
Last updated: 2026-06-29
Last commit: 0bd652e fix: enforce exact material matches in QA
Scope: src/nornikel_kg/; apps/web/; services/api/; pyproject.toml; docker-compose.yml; docs/deployment/fa-nddev.md; tests/
Area: TECHDEBT
-->

# TECHDEBT-01-NOW

## Purpose

Capture verified scaffold gaps that matter for future implementation, without using memory as a backlog.

## Source Of Truth

- `src/nornikel_kg/services/qa_service.py`: deterministic QA assembly.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: synthetic ledger seed/load adapter.
- `docker-compose.yml`: Qdrant is present but not yet used by runtime retrieval.
- `docs/deployment/fa-nddev.md`: server deployment contract and smoke checks.
- `pyproject.toml`: Docling, fixture generators, LiteLLM, Qdrant, DuckDB, and dev tooling dependencies.
- `tests/`: current unit/integration coverage.

## Entry Points

- `DuckDBLedgerRepository.seed_synthetic_fixture`: current fixture ingestion path.
- `DemoQAService.ask`: current answer assembly path.
- `get_ledger_repository`: runtime seeding and DuckDB path resolution.

## Current Behavior

The scaffold is a working evidence-led product shell backed by a DuckDB ledger. It seeds a
synthetic Ni-Cu corpus and supports CSV/Markdown upload into source/evidence/fact tables. It does
not yet parse arbitrary uploaded PDFs/DOCX/PPTX/XLSX/images, does not build Qdrant indexes, and
does not call LiteLLM for extraction or answer writing.
QA requests now support filter-aware experiment selection with fallback behavior aligned
to filtered result sets.
`/qa/ask` now uses a typed `AskFilters` contract and rejects unknown filter keys at request parse time.
Scalar filter values are coerced to one-element lists to preserve API ergonomics.
The workbench now provides interactive QA filter controls (sources/material/property/regime/
experiment), which removes manual JSON request editing.
Free-text material queries with explicit composition numbers now use strict matching; unknown
tokens produce no evidence and clickable close-material suggestions instead of generic family
fallback results.
Source lifecycle was hardened with:
- upload extension validation (`.csv`, `.md`, `.markdown`, `.txt`, `.text` only),
- filename, MIME, empty-file, and size validation at `/sources/upload`,
- `MAX_SOURCE_UPLOAD_BYTES` defaulting to 5242880 bytes,
- web Nginx `client_max_body_size 6m` aligned above the FastAPI upload limit,
- transactional upload/seed paths in DuckDB repository,
- 404-aware source lookup and delete endpoints to avoid silent partial states.

FastAPI tests pass but emit a Starlette deprecation warning that `fastapi.testclient` currently
uses `httpx` and may require `httpx2` in a future dependency cycle.

The server deployment works behind Nginx on `https://fa.nddev.asia`, but the API Docker image
currently installs dependencies with `pip install .` during image build. Rebuilds can therefore
redownload large wheels when the Docker cache is invalidated.

## Contracts And Data

The current demo answer must remain evidence-first: answer summary sentences cite spans, evidence
cards expose `EvidenceSpan` IDs, and graph paths connect material, experiment, regime, step,
measurement, property, evidence, and document.

## Invariants

- Keep the deterministic synthetic demo green while adding real ingestion/retrieval.
- Do not let Qdrant become the authoritative evidence store.
- Do not introduce LLM-generated claims without supporting span IDs.

## Change Rules

Wire future ingestion in narrow steps: parser/artifact output first, DuckDB evidence writes second,
retrieval/indexing third, answer assembly last. Extend tests and eval fixtures with each step.

## Verification

- `make ci`: current scaffold regression gate.
- `make eval`: current evidence/safety smoke.
- Browser validation: verify the workbench still renders evidence cards, graph path, and metrics.

## Known Gaps

- Real Docling/OCR ingestion is not wired.
- Qdrant hybrid retrieval is not wired.
- LiteLLM extraction and answer synthesis are not wired.
- Uploaded Markdown/text sources create evidence spans only; P0 does not extract measurements from
  prose uploads.
- API Docker builds should be optimized with a lock-aware install and Docker build cache mounts
  before frequent server redeploys.
