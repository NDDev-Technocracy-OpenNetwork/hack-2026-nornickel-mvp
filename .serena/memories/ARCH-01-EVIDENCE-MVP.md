<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: apps/web/; services/api/; src/nornikel_kg/; docker-compose.yml; .github/workflows/ci.yml;
  pyproject.toml; .serena/newproj/nornikel-kg-search/; README.md
Area: ARCH
-->

# ARCH-01-EVIDENCE-MVP

## Purpose

Capture the current architecture contract for the evidence-first materials research workbench
after the real-corpus hardening wave.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: original scaffold decisions.
- `src/nornikel_kg/ports/`: port protocols (`ledger.py`, `llm.py`, `parser.py`, `retrieval.py`,
  `extraction.py`).
- `src/nornikel_kg/adapters/`: concrete adapters per port.
- `src/nornikel_kg/services/`: application services (orchestration only, no vendor imports
  outside adapters).

## Entry Points

- `src/nornikel_kg/services/qa_service.py`: `DemoQAService` — deterministic evidence selection,
  scoped filtering (`_apply_source_scope` for geography/year, `_apply_numeric_constraints` for
  parsed numeric ranges via `_parse_numeric_constraints`), optional retrieval augmentation
  (`_augment_with_retrieval`), optional LLM answer composition, claim verification, and
  answer-run recording. `RunRecorderProtocol` requires both `record_answer_run` and
  `source_metadata() -> dict[str, dict[str, Any]]` (`source_id -> {year, geography}`).
- `src/nornikel_kg/services/ingestion_service.py`: `IngestionService` — routes `.csv/.md/.txt`
  through `repository.ingest_source_bytes`, `.pdf/.docx` through the `DocumentParserPort`, and
  URLs through the `UrlFetcherPort`; after `ingest_parsed_document` it calls
  `_apply_source_metadata(source_id, filename, parsed)` (year/geography heuristics: max
  plausible 4-digit year in `filename + head text`; `ru` vs `foreign` geography from a
  Cyrillic-vs-Latin character ratio over the first ~3000 chars of head text, only set when at
  least 40 alphabetic characters are seen) before scheduling enrichment. `enrich_source
  (source_id)` re-runs the extraction/enrichment stage for an already-parsed source
  (recovery/re-enrichment path, exposed via `POST /sources/{id}/enrich`).
- `src/nornikel_kg/services/extraction_service.py`: `ExtractionService` — span -> mentions
  (dictionary alias-scan always; GLiNER when `GLINER_ENABLED`; LLM guided JSON only when both
  `LLMSettings.llm_enabled` and `LLM_EXTRACTION_ENABLED` are set, see
  `src/nornikel_kg/services/runtime.py:get_extraction_service`) -> `EntityResolutionService` ->
  co-occurrence relations with span provenance. Guards for real-corpus scale:
  `MAX_LLM_SPANS_PER_SOURCE = 12` (LLM calls per source), `MAX_SPAN_CHARS = 1200` (span text
  truncation before extraction, LLM-eligible only above 80 chars), `MAX_CO_OCCURRENCE_ENTITIES =
  12` (skips co-occurrence-edge generation for spans resolving more than 12 entities — dense
  catalog/TOC/reference-list spans). `_alias_index()` caches `repository.list_alias_index()` per
  service instance (fixes a full-table-scan-per-span quadratic cost). `process_source` also
  calls `_link_publication(source_id, spans, mentioned_entity_ids)`, which creates one
  `publication` entity per source (`resolve_or_create(mention=source.title[:120],
  entity_type="publication", span_ids=<first 3 span ids>)`), links mentioned
  `material`/`regime`/`property` entities to it via `DESCRIBED_IN`, and extracts author names
  from the first 12 spans (up to 4000 chars) via `_extract_authors` (RU «Фамилия И.О.» /
  EN "I.O. Surname" regexes, capped at 12 names), linking each as a `person` entity via
  `AUTHORED_BY`. `publication`/`DESCRIBED_IN` are not present in `domain/extraction.py`'s
  `ENTITY_TYPES`/`RELATION_TYPES` tuples (those only gate the LLM-guided JSON schema), so this
  path never goes through LLM-schema validation — see `mem:TECHDEBT-01-NOW`.
- `src/nornikel_kg/services/entity_resolution.py`: `EntityResolutionService.resolve_or_create` —
  canonical-key exact match -> alias match -> create; never merges across `entity_type`; does not
  validate `entity_type` against `domain/extraction.py`'s `ENTITY_TYPES`. An embedding-fallback
  stage (cosine >= 0.90 against a Qdrant `entities` collection) is documented in the class
  docstring but not implemented or called (`mem:TECHDEBT-01-NOW`).
- `src/nornikel_kg/services/graph_service.py`: `GraphService` — builds a NetworkX `MultiDiGraph`
  on demand from `list_graph_entities()`/`list_graph_relations()`; `neighborhood(entity_id,
  depth=1..2, limit)` returns focus node plus evidence-ranked neighbors (no entity-type-aware
  boost, so dense `material` nodes can crowd out `person`/`publication` nodes within the limit —
  `mem:TECHDEBT-01-NOW`).
- `src/nornikel_kg/services/retrieval_service.py`: `RetrievalService` — indexes evidence spans
  and dictionary-seeded entities into Qdrant collections (`evidence_units`, `entities`);
  `retrieve_span_ids` hybrid-searches then rejoins hits against DuckDB and re-filters by
  `security_label`; `reindex_all()` is now exposed via `POST /sources/reindex-all` on a
  background daemon thread.
- `src/nornikel_kg/services/answer_composer.py`: `LLMAnswerComposer.compose` — strict JSON
  sentences citing `span_id`s from the packet; drops unsupported sentences, allows one
  regeneration, falls back to the deterministic summary on repeated failure or when no evidence
  exists.
- `src/nornikel_kg/domain/analysis.py`: `ConflictDetector` and `GapAnalyzer` (material x regime
  x property coverage over dictionary-seeded entities only).
- `src/nornikel_kg/adapters/llm/gateway.py`: `LiteLLMGateway` — the only module allowed to
  `import litellm`; enforced by `tests/unit/test_llm_gateway.py::test_litellm_imported_only_inside_llm_adapter`.
- `apps/web/src/`: React/Vite workbench;
  `widgets/analysis-workbench/ui/AnalysisWorkbench.tsx` now also has geography/year_from/
  year_to filter inputs (`geographyFilter`/`yearFromFilter`/`yearToFilter` state, wired into
  `AskFilters.geography`/`year_from`/`year_to`); `shared/api/types.ts`'s `AskFilters` type gained
  `geography?: string[]`, `year_from?: number`, `year_to?: number`; `shared/api/client.ts`'s
  `hasNonEmptyFilters` now handles scalar (non-array) filter values as well as arrays.
- `services/api/`: thin FastAPI route layer; `routes/sources.py` gained
  `POST /sources/{source_id}/enrich` and `POST /sources/reindex-all`.

## Current Behavior

P0 scaffold uses React 19/Vite 8/TypeScript, FastAPI, Python 3.12, and DuckDB as the evidence
ledger and graph store of record. Runtime wiring (`src/nornikel_kg/services/runtime.py`) lazily
builds every service behind `@lru_cache` singletons: `get_ledger_repository`, `get_qa_service`
(attaches `LLMAnswerComposer` only when `LLMSettings.llm_enabled`), `get_retrieval_service`
(`EMBEDDING_BACKEND=off|local|fake`), `get_ingestion_service` (`SYNC_ENRICHMENT` env gates
inline-vs-background enrichment), `get_extraction_service` (`GLINER_ENABLED` default `true`,
`LLM_EXTRACTION_ENABLED` default `false` gates ingest-time LLM calls independently of
`LLM_ENABLED`), and `get_graph_service`.

Docling, GLiNER, sentence-transformers, and fastembed are imported lazily inside their adapter
modules (never at import time), so the core API/tests do not require the `ingest` optional
dependency group unless those code paths execute.

## Contracts And Data

Implemented ports: `EvidenceLedgerPort`, `LLMPort`, `DocumentParserPort`/`UrlFetcherPort`,
`EmbeddingBackendPort`/`VectorIndexPort`, and `MentionExtractorPort`.

`domain/extraction.py` defines `ENTITY_TYPES` (material, regime, property, equipment, team,
person, laboratory, conclusion, decision, value — note: `publication` is not in this tuple, see
Entry Points above), `RELATION_TYPES` (MADE_OF, APPLIES_REGIME, HAS_MEASUREMENT, OF_PROPERTY,
PRODUCED_EFFECT, USED_EQUIPMENT, PERFORMED_BY, AUTHORED_BY, SUPPORTED_BY, FROM_DOCUMENT,
DERIVED_FROM, CONTRADICTS, CONCLUDES — note: `DESCRIBED_IN` is not in this tuple), and
`EXTRACTION_JSON_SCHEMA` for guided-JSON LLM extraction. Co-occurrence relations wired in
`ExtractionService`: material->USED_EQUIPMENT (equipment), material->PERFORMED_BY (team),
material->HAS_MEASUREMENT (property), material->APPLIES_REGIME (regime),
material->CONCLUDES (decision/conclusion); publication/author linking is a separate code path
using entity_type `publication` and relation_type `DESCRIBED_IN`/`AUTHORED_BY` that bypasses
those tuples entirely.

`domain/models.py`'s `AskFilters` now carries `geography: list[str]` (default empty),
`year_from: int | None`, `year_to: int | None`, alongside the existing filter fields.

Concrete P0 domain services: `EvidenceSpanFactory`, normalization helpers in
`domain/normalization.py`, `ConflictDetector`, `GapAnalyzer`, `ClaimVerifier`, and
`DemoQAService` as the answer assembler.

## Invariants

- Domain logic depends on ports, not vendor clients.
- React must call FastAPI contracts and must not bypass application services.
- If DuckDB and Qdrant disagree, DuckDB wins; Qdrant hits are always rejoined and re-filtered
  against DuckDB before being trusted.
- Only `src/nornikel_kg/adapters/llm/gateway.py` may `import litellm`.
- Extraction and answer-composer system prompts explicitly instruct the model that fragment
  text is data, not instructions (see `mem:SEC-01-ACL-AND-PROMPT-INJECTION`).
- Parser/network/extraction/retrieval failures degrade gracefully and never surface as an
  unhandled 500 or an unverified answer.
- Do not call `duckdb.connect(...)` outside `DuckDBLedgerRepository._connect()` — the connection
  is now persistent per repository instance behind a class `RLock`
  (`mem:DATA-01-EVIDENCE-LEDGER`).

## Change Rules

Keep implementation changes aligned with `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md`
(current wave plan) first, then update ADRs if a stack boundary changes.

## Verification

- `make ci`: backend/frontend gate; `uv run pytest` verified 96 passed / 3 skipped at `41ee7ac`
  (live-run verified in this sync pass).
- `make eval`: deterministic + retrieval-augmented evidence packet verification (12 questions,
  synthetic corpus only).
- `docker compose config`: validates server-first Compose wiring (`api`, `web`, `qdrant`).
