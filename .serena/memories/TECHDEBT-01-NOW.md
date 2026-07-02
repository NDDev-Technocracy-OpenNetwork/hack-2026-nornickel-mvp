<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: src/nornikel_kg/; apps/web/; services/api/; scripts/ingest_corpus.py; pyproject.toml;
  docker-compose.yml; .env.example; .github/workflows/ci.yml; tests/;
  .serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md
Area: TECHDEBT
-->

# TECHDEBT-01-NOW

## Purpose

Capture verified current gaps after the real-corpus hardening wave, without using memory as a backlog.

## Source Of Truth

- `src/nornikel_kg/services/entity_resolution.py`: `EntityResolutionService` docstring documents
  an unimplemented embedding-fallback stage.
- `services/api/routes/graph.py`: `GET /graph/timeline` reads only `decision`/`conclusion`
  entities with a `metadata.date` field.
- `src/nornikel_kg/services/runtime.py`: `get_extraction_service` gates ingest-time LLM
  extraction behind `LLM_EXTRACTION_ENABLED` (default `false`).
- `src/nornikel_kg/domain/extraction.py`: `ENTITY_TYPES`/`RELATION_TYPES` tuples do not include
  `publication`/`DESCRIBED_IN`, which `ExtractionService._link_publication` uses anyway.
- `.github/workflows/ci.yml`: backend job still does not pass `--extra ingest`.
- `.env.example`: `LLM_EXTRACTION_MODEL`/`LLM_ANSWER_MODEL` still blank.
- `eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml`:
  orphaned fixtures (see `mem:TEST-01-EVALUATION-GATES`).

## Resolved Since W0 (verified, do not re-list as gaps)

- Docling PDF/DOCX ingestion, Qdrant hybrid retrieval, the LLM gateway (extraction + answer
  synthesis), and `resolve_alias()`-equivalent mention resolution are wired end to end
  (`mem:ARCH-01-EVIDENCE-MVP`).
- `dataeyes.ai` key discovery and `_strictify()`/inline-format-hint LLM-gateway hardening are
  complete (`mem:ARCH-01-EVIDENCE-MVP`).
- **Real-corpus ingest hardening and metallurgy ontology extension (resolved, commit `58760b3`,
  squashed/rewritten history that also dropped 4.2GB of accidentally staged `DATA_HACK` blobs)**:
  - `src/nornikel_kg/resources/dictionaries/materials.yml`/`regimes.yml`/`properties.yml`/
    `equipment.yml` now cover pyrometallurgy (slag, matte, Vanyukov furnace, flash smelting,
    converting, smelting), electrowinning (cathode nickel, electrolyte, electrowinning cell/bath,
    diaphragm cell), flotation/beneficiation (ore, concentrate, flotation, flotation machine), and
    desalination (technogenic gypsum, sulfates, chlorides, SO2, desalination regime, tube
    furnace) domains — verified counts: materials.yml has the 17 new entries described in the gap
    (G1 in `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md`), regimes.yml has 15
    `canonical_name:` entries total, properties.yml has 14, equipment.yml has 9 (3 original demo
    + 6 new). **Geomechanics-specific terms are still not covered** (verified: no `геомех`/
    `geomechanic`/`горн` alias hits in any dictionary), so G1 is only partially closed for the
    real corpus's full domain span.
  - `ExtractionService._link_publication` makes every source a `publication` entity with
    `DESCRIBED_IN` edges from mentioned material/regime/property entities and `AUTHORED_BY`
    edges from `_extract_authors`-derived `person` entities — this closes the G1/G8
    Publication/Expert entity-type gap from the plan, though `publication`/`DESCRIBED_IN` remain
    outside the `ENTITY_TYPES`/`RELATION_TYPES` vocab used for LLM-guided extraction (see Known
    Gaps below).
  - `src/nornikel_kg/services/qa_service.py` gained `_parse_numeric_constraints`/
    `_apply_numeric_constraints` (G2, numeric range queries) and `_apply_source_scope` (G3,
    geography/year filters), both covered by
    `tests/unit/test_scope_and_constraints.py` (6 test functions, all passing).
  - `scripts/ingest_corpus.py` (G4, corpus-scale ingestion): batch-ingests a directory into the
    ledger inside the API container with per-file size caps; unsupported formats
    (`.zip`/`.rar`/`.doc`/`.pptx`/`.xls`) are counted and skipped, not silently dropped.
- **Real DOCX/PDF upload 413 rejection (resolved, `ed69686`)**: `apps/web/nginx.conf`'s
  `client_max_body_size` raised from `6m` to `32m`; real corpus DOCX files over 6MB were being
  rejected by the bundled web proxy before reaching the API.
- **No re-enrichment/recovery path (resolved, `074531e`)**: `IngestionService.enrich_source`
  (re)runs the extraction/enrichment stage for an already-parsed source; exposed via
  `POST /sources/{id}/enrich`.
- **Unbounded reindex operations (resolved, `4f482d0`)**: `POST /sources/reindex-all`
  (`services/api/routes/sources.py`) runs `RetrievalService.reindex_all()` on a background
  daemon thread instead of blocking the request.
- **Ingest-time LLM extraction producing consistently schema-invalid payloads on real spans
  (mitigated, `23a220a`)**: `LLM_EXTRACTION_ENABLED` (default `false`,
  `src/nornikel_kg/services/runtime.py:get_extraction_service`) gates ingest-time LLM calls
  separately from the QA answer composer's `LLMSettings.llm_enabled`; dictionary rules (plus
  GLiNER when enabled) carry ingest extraction by default. The underlying model-behavior gap is
  not fixed, only worked around — see Known Gaps below.
- **Quadratic alias-index re-query per span (resolved, `42d5742`)**: `ExtractionService.
  _alias_index()` caches `repository.list_alias_index()` per service instance instead of
  per-span, verified in `src/nornikel_kg/services/extraction_service.py`.
- **DuckDB connect/close overhead under concurrent enrichment threads (resolved, `f40ab72`)**:
  `DuckDBLedgerRepository._connect()` now holds one persistent connection behind the class
  `_db_lock` (`threading.RLock`) instead of opening/closing per call. Trade-off introduced: the
  API process now holds the DuckDB file lock for its entire lifetime, so any out-of-process tool
  (e.g. a `docker exec` DuckDB CLI session) cannot open `data/catalog.duckdb` directly while the
  `api` container is running — diagnostics must go through the API's own endpoints instead.
- **Quadratic noisy co-occurrence edges on dense spans (resolved, `41ee7ac`)**:
  `ExtractionService.MAX_CO_OCCURRENCE_ENTITIES = 12` skips the co-occurrence relation loop for
  spans that resolve more than 12 entities (catalog/TOC/reference-list spans in real documents).
- **GitHub push backlog (resolved)**: local `main` and `origin/main` are in sync (`git rev-list
  --left-right --count origin/main...main` -> `0\t0`, verified 2026-07-03); the history rewrite
  in `58760b3` (which replaced the earlier `86abb1f`/`f62f17c` commit line to drop 4.2GB of
  `DATA_HACK` blobs) has already been pushed. Do not reference `86abb1f`/`f62f17c` as current
  history — those commits no longer exist (`git cat-file -t 86abb1f` -> "Not a valid object
  name", verified).

## Entry Points

- `EntityResolutionService.resolve_or_create`: exact key -> alias -> create; no embedding stage.
- `GET /graph/timeline` (`services/api/routes/graph.py`).
- `ExtractionService.mention_extractor` (GLiNER lazy import).
- `ExtractionService._llm_mentions`: LLM extraction call site, gated by `LLM_EXTRACTION_ENABLED`.

## Current Behavior

The system is a working evidence-led product with real ingestion (Docling/trafilatura),
extraction (dictionary+GLiNER+optional-LLM), retrieval (Qdrant hybrid), LLM-gated answer
synthesis, graph analytics (conflicts/gaps/timeline/publication-author), scoped QA filters
(numeric constraints, geography, year), and a metallurgy-domain dictionary extension for the
real corpus. `uv run pytest` passes 96 tests, 3 skipped, at `41ee7ac` (live-run verified in this
sync pass).

## Contracts And Data

The current demo answer must remain evidence-first regardless of which extraction/retrieval
paths are enabled: answer summary sentences cite spans, evidence cards expose `EvidenceSpan`
IDs, and graph paths connect material, experiment, regime, step, measurement, property,
evidence, and document.

## Invariants

- Keep the deterministic synthetic demo green while any LLM/retrieval path is toggled on or off.
- Do not let Qdrant become the authoritative evidence or entity store.
- Do not introduce LLM-generated claims without supporting span IDs.
- Only `src/nornikel_kg/adapters/llm/gateway.py` may import `litellm`.
- Do not call `duckdb.connect(...)` outside `DuckDBLedgerRepository._connect()`.

## Change Rules

When closing a gap below, verify it against the working tree (not this memory) before removing
it, and move the corresponding "Resolved Since" bullet into the resolved list above in the same
change.

## Known Gaps

- **`gpt-5.4-mini` extraction payloads are consistently schema-invalid on real-corpus spans**:
  the answer-composer task works with inline JSON-format hints, but the extraction task does
  not reliably produce valid `ExtractionPayload` JSON for real (non-synthetic) span text, which
  motivated gating ingest-time LLM extraction off by default (`LLM_EXTRACTION_ENABLED=false`,
  see Resolved list above). If LLM extraction is re-enabled, this needs either a few-shot
  extraction prompt or a different extraction-capable catalog model; current inline format
  hints in `ExtractionService._llm_mentions` are insufficient by themselves.
- **Person extraction may pick up reference-list names**: `_extract_authors`
  (`src/nornikel_kg/services/extraction_service.py`) is a regex heuristic (RU «Фамилия И.О.»,
  EN "I.O. Surname") applied to the first 12 spans of a source; it is only verified against the
  `test_author_extraction_ru_and_en` fixture in `tests/unit/test_scope_and_constraints.py`
  (author names near an affiliation/email), not against a real document's reference/bibliography
  section, where the same name pattern also occurs. No automated test currently distinguishes
  head-section authors from bibliography citations.
- **Eval questions target only the synthetic fixture**: `scripts/run_eval.py`'s hardcoded
  `EVAL_QUESTIONS` (12 questions) run against the synthetic `sample_docs/synthetic`/
  `synthetic_v2` corpora only; there is no gold-question set for the real `DATA_HACK/` corpus, so
  `make eval` does not exercise the new ontology/publication/scope-filter behavior against real
  data (only `tests/unit/test_scope_and_constraints.py` does, with synthetic fixtures).
- **"Experts by topic" neighborhood ranking is not person/publication-aware**:
  `GraphService.neighborhood` (`src/nornikel_kg/services/graph_service.py`) ranks neighbors by
  evidence count with no entity-type-aware boost; on a real, densely-annotated source, material
  nodes with many co-occurrence edges can crowd out `person`/`publication` nodes within the
  neighborhood limit, so a "who works on topic X" style query is not well served by the current
  ranking. No automated test currently covers this ranking behavior.
- **`publication`/`DESCRIBED_IN` are outside the declared extraction vocabulary**:
  `domain/extraction.py`'s `ENTITY_TYPES`/`RELATION_TYPES` tuples (used to build
  `EXTRACTION_JSON_SCHEMA` for LLM-guided extraction) do not list `publication` or
  `DESCRIBED_IN`; `ExtractionService._link_publication` creates them directly via
  `EntityResolutionService.resolve_or_create`/`repository.insert_relation`, which do not
  validate against those tuples, so this does not currently break anything, but the two
  vocabularies have drifted apart and should be reconciled if publication/authorship data is
  ever meant to be LLM-extractable.
- **Geomechanics domain not covered by the ontology**: the 2026-07-03 dictionary extension
  (`58760b3`) added pyrometallurgy/electrowinning/flotation/desalination terms but no
  geomechanics-specific materials/regimes (verified: no matching alias hits in any dictionary
  file), so questions specific to that domain in the real corpus still slot-parse to no entities.
- **Entity-resolution embedding fallback not wired**: `EntityResolutionService`'s docstring
  documents a planned cosine>=0.90 embedding-fallback stage against a Qdrant `entities`
  collection, but `resolve_or_create` only implements exact-key and alias matching.
- **GLiNER model not pre-pulled in CI**: `.github/workflows/ci.yml`'s backend job does not
  install the `ingest` optional dependency group; `GLINER_ENABLED` defaults to `true` at
  runtime, but CI's `pytest` run never exercises the real GLiNER path.
- `eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml` are
  orphaned: no code path reads them; `scripts/run_eval.py` hardcodes its own 12-question list
  instead (see `mem:TEST-01-EVALUATION-GATES`).
- **Timeline events without dates**: `GET /graph/timeline` only returns `decision`/`conclusion`
  entities whose `metadata` dict has a `date` key (`services/api/routes/graph.py`); date
  extraction into `metadata.date` for these entity types remains an open gap.
