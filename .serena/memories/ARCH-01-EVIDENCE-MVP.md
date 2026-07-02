<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: ece33d3 docs(plans): record completed dataeyes discovery and configured dev model
Scope: apps/web/; services/api/; src/nornikel_kg/; docker-compose.yml; .github/workflows/ci.yml; pyproject.toml; .serena/newproj/nornikel-kg-search/; README.md
Area: ARCH
-->

# ARCH-01-EVIDENCE-MVP

## Purpose

Capture the current architecture contract for the evidence-first materials research workbench
after waves W0-W5.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: original scaffold decisions.
- `.serena/plans/00_PLAN_INDEX.md` and `.serena/plans/03_IMPLEMENTATION_PLAN.md`: the W0-W5
  implementation plan this architecture now realizes.
- `src/nornikel_kg/ports/`: port protocols (`ledger.py`, `llm.py`, `parser.py`, `retrieval.py`,
  `extraction.py`).
- `src/nornikel_kg/adapters/`: concrete adapters per port.
- `src/nornikel_kg/services/`: application services (orchestration only, no vendor imports
  outside adapters).

## Entry Points

- `src/nornikel_kg/services/qa_service.py`: `DemoQAService` — deterministic evidence selection,
  optional retrieval augmentation (`_augment_with_retrieval`), optional LLM answer composition,
  claim verification, and answer-run recording.
- `src/nornikel_kg/services/ingestion_service.py`: `IngestionService` — routes `.csv/.md/.txt`
  through `repository.ingest_source_bytes`, `.pdf/.docx` through the `DocumentParserPort`
  (lazy-loaded `DoclingDocumentParser`), and URLs through the `UrlFetcherPort` (lazy-loaded
  `TrafilaturaUrlFetcher`); records an `ingestion_runs` row for every ingest attempt with
  `status` in `{running, completed, quarantined}` and archives the raw artifact bytes under
  `ARTIFACT_ROOT/sources/<source_id>/` (best-effort, never blocks ingest).
- `src/nornikel_kg/services/extraction_service.py`: `ExtractionService` — span -> mentions
  (dictionary alias-scan always; GLiNER when `GLINER_ENABLED`; LLM guided JSON when
  `LLMSettings.llm_enabled`) -> `EntityResolutionService` -> co-occurrence relations with span
  provenance. Extraction failures are logged and swallowed; they never fail ingestion.
- `src/nornikel_kg/services/entity_resolution.py`: `EntityResolutionService.resolve_or_create` —
  canonical-key exact match -> alias match -> create; never merges across `entity_type`; an
  embedding-fallback stage (cosine >= 0.90 against a Qdrant `entities` collection) is documented
  in the class docstring but not implemented or called (`mem:TECHDEBT-01-NOW`).
- `src/nornikel_kg/services/graph_service.py`: `GraphService` — builds a NetworkX `MultiDiGraph`
  on demand from `list_graph_entities()`/`list_graph_relations()`; `neighborhood(entity_id,
  depth=1..2, limit)` returns focus node plus evidence-ranked neighbors.
- `src/nornikel_kg/services/retrieval_service.py`: `RetrievalService` — indexes evidence spans
  and dictionary-seeded entities into Qdrant collections (`evidence_units` via
  `QDRANT_COLLECTION` env, `entities`); `retrieve_span_ids` hybrid-searches then rejoins hits
  against DuckDB and re-filters by `security_label`, so the index is never authoritative. Any
  index/network failure degrades to an empty result, never an exception.
- `src/nornikel_kg/services/answer_composer.py`: `LLMAnswerComposer.compose` — strict JSON
  sentences citing `span_id`s from the packet; drops unsupported sentences, allows one
  regeneration, falls back to the deterministic summary on repeated failure or when no evidence
  exists. Because providers do not always enforce `response_format`/`json_schema`, the packet
  prompt (`_packet_prompt`) also spells out the exact required structure
  (`{"sentences": [{"sentence": ..., "supporting_span_ids": [...]}]}`) inline as text; a
  `ValidationError` on attempt 1 sends one reminder-regeneration attempt before falling back on
  attempt 2. `src/nornikel_kg/services/extraction_service.py`'s `_llm_mentions` adds the same
  kind of inline format hint (entities/relations JSON shape) ahead of the fragment text for
  extraction calls.
- `src/nornikel_kg/domain/analysis.py`: `ConflictDetector` (contradictory_direction,
  method_mismatch, numeric_disagreement > 15% under the same method, grouped by
  material+property+regime bucket) and `GapAnalyzer` (material x regime x property coverage
  over dictionary-seeded entities only).
- `src/nornikel_kg/adapters/llm/gateway.py`: `LiteLLMGateway` — the only module allowed to
  `import litellm`; enforced by `tests/unit/test_llm_gateway.py::test_litellm_imported_only_inside_llm_adapter`.
  `_strictify(schema)` recursively sets `additionalProperties: false` on every object schema (and
  recurses into `array.items`) before every `generate_json` call, required for OpenAI-compatible
  strict `json_schema` mode; covered by
  `tests/unit/test_llm_gateway.py::test_strictify_adds_additional_properties`.
- `apps/web/src/`: React/Vite workbench; new widgets `widgets/graph-view` (force-graph
  neighborhood, `react-force-graph-2d@1.29`), `widgets/gaps-board` (coverage matrix,
  clickable cells), `widgets/timeline` (decisions/conclusions timeline).
- `services/api/`: thin FastAPI route layer (`routes/sources.py`, `routes/entities.py`,
  `routes/graph.py`, `routes/gaps.py`, `routes/evals.py`, `routes/query.py`).

## Current Behavior

P0 scaffold uses React 19/Vite 8/TypeScript, FastAPI, Python 3.12, and DuckDB as the evidence
ledger and graph store of record. Runtime wiring (`src/nornikel_kg/services/runtime.py`) lazily
builds every service behind `@lru_cache` singletons:
`get_ledger_repository`, `get_qa_service` (attaches `LLMAnswerComposer` only when
`LLMSettings.llm_enabled`), `get_retrieval_service` (`EMBEDDING_BACKEND=off|local|fake`, `off`
is the default and returns `index=None`), `get_ingestion_service` (wires extraction + retrieval
into every ingest), `get_extraction_service` (`GLINER_ENABLED` default `true`), and
`get_graph_service`.

Docling, GLiNER, sentence-transformers, and fastembed are imported lazily inside their adapter
modules (never at import time), so the core API/tests do not require the `ingest` optional
dependency group unless those code paths execute. `docling`/`trafilatura` are `importorskip`-
guarded in `tests/integration/test_synthetic_v2_corpus.py` and skip when not installed.

## Contracts And Data

Implemented ports: `EvidenceLedgerPort`, `LLMPort`, `DocumentParserPort`/`UrlFetcherPort`
(`ports/parser.py`), `EmbeddingBackendPort`/`VectorIndexPort` (`ports/retrieval.py`), and
`MentionExtractorPort` (`ports/extraction.py`). `ports/parser.py` defines `ParserError` /
`NoTextLayerError` (quarantine path, never OCR), `ParsedBlock`/`ParsedTableCell`/
`ParsedTableRow`/`ParsedTable`/`ParsedDocument` (provenance-carrying), and `FetchedPage`.

`ports/retrieval.py` defines `SparseVector`, `IndexableUnit`, `RetrievalHit`,
`EmbeddingBackendPort.embed_dense`/`embed_sparse`, and `VectorIndexPort.index_units`/
`hybrid_search`/`delete_source_units`. `QdrantVectorIndex` (`adapters/qdrant_index/index.py`)
creates named `dense`+`sparse` vectors (`Modifier.IDF` on sparse), fuses with
`FusionQuery(fusion=Fusion.RRF)`, filters on `security_label`/`source_id` payload fields, and
derives point IDs via `uuid5(NAMESPACE_URL, unit_id)`.

`domain/extraction.py` defines `ENTITY_TYPES` (material, regime, property, equipment, team,
person, laboratory, conclusion, decision, value), `RELATION_TYPES` (MADE_OF, APPLIES_REGIME,
HAS_MEASUREMENT, OF_PROPERTY, PRODUCED_EFFECT, USED_EQUIPMENT, PERFORMED_BY, AUTHORED_BY,
SUPPORTED_BY, FROM_DOCUMENT, DERIVED_FROM, CONTRADICTS, CONCLUDES), `EntityMention`,
`ExtractedRelation`, `ExtractionPayload`, and `EXTRACTION_JSON_SCHEMA` for guided-JSON LLM
extraction. Co-occurrence relations wired in `ExtractionService`: material->USED_EQUIPMENT
(equipment), material->PERFORMED_BY (team), material->HAS_MEASUREMENT (property),
material->APPLIES_REGIME (regime), material->CONCLUDES (decision/conclusion).

Concrete P0 domain services (not hidden behind generic RAG abstractions): `EvidenceSpanFactory`,
`MaterialNormalizer`/`RegimeNormalizer`/`MeasurementNormalizer` equivalents in
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
- Parser/network/extraction/retrieval failures degrade gracefully (quarantine, empty result,
  rule-only fallback) and never surface as an unhandled 500 or an unverified answer.

## Change Rules

Keep implementation changes aligned with `.serena/plans/03_IMPLEMENTATION_PLAN.md` first, then
update ADRs if a stack boundary changes.

## Verification

- `make ci`: backend/frontend gate (`uv run ruff check .`, `uv run mypy`,
  `uv run pytest` — 90 passed, 3 skipped at `ece33d3` — plus frontend typecheck/build).
- `make eval`: deterministic + retrieval-augmented evidence packet verification (12 questions).
- `docker compose config`: validates server-first Compose wiring (`api`, `web`, `qdrant`).
