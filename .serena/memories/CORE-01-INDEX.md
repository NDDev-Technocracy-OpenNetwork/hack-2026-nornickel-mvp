<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: README.md; apps/web/; services/api/; src/nornikel_kg/; eval/; sample_docs/; scripts/;
  tests/; docker-compose.yml; .github/workflows/ci.yml; .env.example; pyproject.toml;
  .serena/plans/; .serena/reviews/; docs/deployment/; .gitignore
Area: CORE
-->

# CORE-01-INDEX

## Purpose

Index the durable project knowledge for the Nornikel Materials KG Search hackathon MVP.

## Source Of Truth

- `README.md`: repository overview, quick start, demo scenario, and implemented scope.
- `AGENTS.md`: Codex-native project instructions and plugin/tooling policy.
- `.claude/CLAUDE.md`: Claude Code project memory and operational commands.
- `apps/web/`: React/Vite analysis workbench.
- `services/api/`: FastAPI route layer.
- `src/nornikel_kg/`: backend domain, ports, adapters, and application services.
- `scripts/ingest_corpus.py`: batch-ingests a real document corpus directory (`.pdf`, `.docx`,
  `.csv`, `.md`, `.markdown`, `.txt`) into the ledger inside the API container, with per-file
  size caps and quarantine-over-crash semantics (`SUPPORTED` set, `--max-mb` flag).
- `eval/`: legacy YAML gold/adversarial fixtures; not read by any code path (`mem:TEST-01-EVALUATION-GATES`).
- `sample_docs/synthetic/`: original P0 fixture. `sample_docs/synthetic_v2/`: W5 17-source synthetic corpus with `manifest.json`.
- `tests/`: unit and integration tests.
- `docs/deployment/nornikel-nddev.md`: primary live-stand deployment contract (W5).
- `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md`: full-track requirement brief («Научный
  клубок») and gap analysis G1-G10 against the real `DATA_HACK/` corpus; wave W6.3 (ontology
  extension) is now substantially implemented (`mem:DATA-01-EVIDENCE-LEDGER`,
  `mem:TECHDEBT-01-NOW`).
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

Waves W0-W5 closed the ingest/extraction/retrieval/frontend/corpus gaps that were open at W0
(see `mem:DOCS-01-PLANNING-SOURCE` for the merge-commit chain). A real-corpus hardening wave
(commit `58760b3`, squashed and rewritten to drop 4.2GB of accidentally staged `DATA_HACK`
blobs, followed by `0dfeba3`, `ed69686`, `074531e`, `23a220a`, `4f482d0`, `42d5742`, `f40ab72`,
`41ee7ac`) then extended the system for the real case corpus:

- **Ontology extension** (`58760b3`): `src/nornikel_kg/resources/dictionaries/materials.yml`
  gained 17 metallurgy materials (slag, matte, cathode nickel, electrolyte, technogenic gypsum,
  sulfates, chlorides, SO2, ore, concentrate, PGM/precious metals, copper, nickel, cobalt,
  metallic phase, etc.); `regimes.yml` gained leaching, electrowinning, slag depletion,
  converting, smelting, flotation, desalination, drying, circulation, injection (10 entries,
  verified `grep -c canonical_name: regimes.yml` -> 15 total); `properties.yml` gained
  concentration/flow-rate/extraction/temperature/coalescence/metal-loss properties (14 total);
  `equipment.yml` gained Vanyukov furnace, flash smelting furnace, electrowinning bath,
  diaphragm cell, flotation machine, tube furnace (6 entries, verified by entry count).
- **Publication/author graph** (`src/nornikel_kg/services/extraction_service.py`,
  `ExtractionService._link_publication`): every ingested source becomes a `publication` entity
  (via `EntityResolutionService.resolve_or_create`); mentioned material/regime/property entities
  get a `DESCRIBED_IN` edge to it; author names found via `_extract_authors` (RU «Фамилия И.О.»
  and EN "I.O. Surname" regexes, capped at 12) get `person` entities with `AUTHORED_BY` edges.
  `publication`/`DESCRIBED_IN` are **not** listed in `domain/extraction.py`'s `ENTITY_TYPES`/
  `RELATION_TYPES` tuples (those tuples only constrain the LLM guided-JSON schema); this is a
  verified vocabulary gap, not a runtime error, since `resolve_or_create`/`insert_relation`
  never validate against those tuples.
- **Scoped QA filters** (`src/nornikel_kg/services/qa_service.py`): `_parse_numeric_constraints`
  parses RU/symbolic numeric operators (≤/≥/не более/не менее/от + value + unit) from the
  question text and `_apply_numeric_constraints` filters experiments whose measurement unit
  matches; `_apply_source_scope` filters experiments by `AskFilters.geography`/`year_from`/
  `year_to` via `RunRecorderProtocol.source_metadata()`.
- **Corpus ingestion hardening**: `IngestionService.enrich_source` (re)runs the enrichment stage
  for an already-parsed source (recovery/re-enrichment); `POST /sources/{id}/enrich` and
  `POST /sources/reindex-all` (`services/api/routes/sources.py`) expose this and a batched
  background `RetrievalService.reindex_all()` respectively; `LLM_EXTRACTION_ENABLED` (default
  `false`, `src/nornikel_kg/services/runtime.py:get_extraction_service`) gates ingest-time LLM
  extraction separately from the QA answer composer.
- **Performance fixes**: `ExtractionService._alias_index()` caches the alias table snapshot per
  service instance instead of re-querying per span; `DuckDBLedgerRepository._connect()`
  (`src/nornikel_kg/adapters/duckdb/repositories.py`) now holds one persistent
  `duckdb.DuckDBPyConnection` behind the class `_db_lock` (`threading.RLock`) instead of
  connecting/closing per call — this means the API process holds the DuckDB file lock for its
  lifetime, so `docker exec`-based diagnostics cannot open the DB file directly while the `api`
  container runs; `ExtractionService.MAX_CO_OCCURRENCE_ENTITIES = 12` skips co-occurrence-edge
  generation on spans that resolve more than 12 entities (dense catalog/TOC/reference-list spans).
- **Frontend geography/year filters**: `apps/web/src/widgets/analysis-workbench/ui/AnalysisWorkbench.tsx`
  adds geography/year_from/year_to inputs; `apps/web/src/shared/api/types.ts`'s `AskFilters`
  gained matching optional fields; `apps/web/src/shared/api/client.ts`'s `hasNonEmptyFilters`
  handles scalar (not just array) filter values.
- **Nginx body limit**: `apps/web/nginx.conf` raised `client_max_body_size` from `6m` to `32m`
  (real DOCX files over 6MB were being 413-rejected).

`uv run pytest` passes **96 tests, 3 skipped** at `41ee7ac` (verified by a live run; skips remain
the `docling`/`trafilatura` `importorskip` guards); `uv run ruff check .` and `uv run mypy` were
not re-run in this sync pass — see `mem:RELEASE-01-VALIDATION` for the last verified status.
Local `main` is in sync with `origin/main` (`git rev-list --left-right --count
origin/main...main` -> `0\t0`, verified) — the history rewrite in `58760b3` has already been
pushed; there is no pending push backlog (previously recorded in `mem:TECHDEBT-01-NOW`, now
resolved).

## Contracts And Data

Full flow: React/Vite workbench -> FastAPI (`/sources/upload`, `/sources/import-url`,
`/sources/{id}/enrich`, `/sources/reindex-all`, `/qa/ask`, `/entities/search`, `/entities/{id}`,
`/graph/neighborhood`, `/graph/timeline`, `/gaps/analyze`, `/eval/summary`) -> DuckDB-backed
evidence ledger + entity/relation graph -> optional Qdrant retrieval augmentation ->
deterministic-or-LLM answer synthesis -> claim verification -> answer-run persistence.

Upload accepts `.csv`, `.md`, `.markdown`, `.txt`, `.text`, `.pdf`, `.docx` with filename/MIME/
size validation (`services/api/routes/sources.py`); `MAX_SOURCE_UPLOAD_BYTES` code default is
`5242880` bytes; bundled web Nginx sets `client_max_body_size 32m` (raised from `6m`) and
`proxy_read_timeout 300s` for `/api/` (`apps/web/nginx.conf`).

## Invariants

- Do not treat Markdown chunks as source of truth; they are convenience views only.
- Every answer sentence must map to exact evidence IDs.
- DuckDB is authoritative for facts and provenance; if DuckDB and Qdrant disagree, DuckDB wins.
- Qdrant is retrieval-only; NetworkX is graph materialization-only, rebuilt on demand from DuckDB.
- React/Vite and FastAPI are P0 UI/API layers, not P1.
- No OCR: PDFs without a text layer are quarantined, never OCR'd (`NoTextLayerError`).
- Only `src/nornikel_kg/adapters/llm/gateway.py` may `import litellm`.
- Do not call `duckdb.connect(...)` outside `DuckDBLedgerRepository._connect()`; the connection
  is now persistent and shared, so external processes must go through the API, not a direct
  file open, while the API is running.

## Change Rules

Update this index whenever a new durable memory is added, renamed, split, or deleted.

## Verification

- `make ci`: verifies backend ruff/mypy/pytest and frontend typecheck/build.
- `make eval`: runs `scripts/run_eval.py` (12 hardcoded `EVAL_QUESTIONS`).
- `docker compose config`: verifies Compose syntax without requiring local secrets.
- `uv run pytest`: 96 tests pass, 3 skipped at `41ee7ac` (live-run verified).
