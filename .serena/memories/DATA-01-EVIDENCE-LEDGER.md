<!-- Memory Metadata
Last updated: 2026-07-02
Last commit: 1bca77f Merge pull request #6 from rldyourmnd/feat/w0-alignment-and-seams
Scope: src/nornikel_kg/domain/; src/nornikel_kg/adapters/duckdb/; src/nornikel_kg/resources/dictionaries/; src/nornikel_kg/services/qa_service.py; src/nornikel_kg/services/runtime.py; sample_docs/synthetic/; eval/
Area: DATA
-->

# DATA-01-EVIDENCE-LEDGER

## Purpose

Capture evidence identity, artifact memory, scientific schemas, graph/dictionary seeding, and answer-claim contracts.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: ID policy, artifact layout, minimum DuckDB tables, and required schemas.
- `src/nornikel_kg/domain/ids.py`: implemented stable `source_id`, `artifact_id`, `span_id`, `fact_id`, and `claim_id` helpers.
- `src/nornikel_kg/domain/models.py`: implemented Pydantic API/domain payload models.
- `src/nornikel_kg/domain/evidence.py`: implemented `EvidenceSpanFactory`.
- `src/nornikel_kg/domain/normalization.py`: `canonical_key()` mention-normalization helper for entity resolution.
- `src/nornikel_kg/adapters/duckdb/migrations/001_init.sql`: implemented P0 ledger tables.
- `src/nornikel_kg/adapters/duckdb/migrations/002_graph.sql`: graph/knowledge schema (`ingestion_runs`, `artifacts`, `entities`, `entity_aliases`, `relations`, `extraction_claims`, `answer_runs`, `eval_results`).
- `src/nornikel_kg/adapters/duckdb/dictionary_loader.py`: idempotent entity/alias seeding from YAML dictionaries and mention resolution.
- `src/nornikel_kg/resources/dictionaries/*.yml`: `materials.yml` (3 entries), `regimes.yml` (5), `properties.yml` (8), `equipment.yml` (3), `teams.yml` (3), plus `units.yml`.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: implemented DuckDB seed/load/upload adapter.
- `sample_docs/synthetic/`: committed synthetic report and mechanical property table.
- `.serena/newproj/nornikel-kg-search/07_DATA.md`: domain model and graph path.
- `.serena/newproj/nornikel-kg-search/06_API.md`: API-level answer and graph response contracts.
- `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`: demo scope and fixture/corpus decisions.

## Entry Points

- `DuckDBLedgerRepository.seed_synthetic_fixture`: reads committed synthetic CSV/Markdown, creates source/evidence/measurement/effect records, and writes DuckDB.
- `DuckDBLedgerRepository.ingest_source_bytes`: ingests uploaded CSV or Markdown/text sources into DuckDB.
- `DuckDBLedgerRepository.list_sources`: returns source summaries with evidence and measurement counts.
- `DuckDBLedgerRepository.list_evidence_spans`: returns evidence spans globally or for one source.
- `DuckDBLedgerRepository.get_source`: returns a source summary by id or `None`.
- `DuckDBLedgerRepository.delete_source`: hard-deletes a source with related source/evidence/fact records and returns success flag.
- `DuckDBLedgerRepository.ingest_source_bytes`: now wraps seed/upload in explicit transaction boundaries and raises
  `SourceIngestError` on decode/schema violations.
- `DuckDBLedgerRepository.migrate`: applies every `migrations/*.sql` file (now including `002_graph.sql`), backfills legacy columns, and then calls `load_dictionaries(connection)` to seed the graph entity tables.
- `DuckDBLedgerRepository.load_demo_packet`: returns the current evidence packet used by QA.
- `load_dictionaries(connection, dictionaries_dir=None)`: idempotently upserts `entities`/`entity_aliases` from the dictionary YAML files (keyed by stable dictionary IDs); returns per-entity-type seeded counts.
- `resolve_alias(connection, mention)`: resolves a mention to `entity_id`, checking `entities.canonical_key` first, then `entity_aliases.alias_norm`, both via `canonical_key(mention)`. Not yet called by any ingestion/QA service.
- `canonical_key(value)`: lowercases, strips, unifies dash variants (`‐‑‒–—―−_`) to `-`, folds `ё`→`е`, and collapses whitespace runs.
- `DemoQAService.ask`: assembles the response from an `EvidenceLedgerPort` when provided, otherwise uses a deterministic fallback packet.

## Current Behavior

The implemented scaffold writes a DuckDB evidence ledger with `sources`, `evidence_spans`,
`property_measurements`, `effect_claims`, and `answer_claims`. Runtime seeding happens through
`get_ledger_repository()` using `PROJECT_ROOT`, `DUCKDB_PATH`, and `SYNTHETIC_SAMPLE_DIR`,
defaulting to `data/catalog.duckdb` and `sample_docs/synthetic`. Container runtime sets
`PROJECT_ROOT=/app`; local runtime falls back to the current working directory when
`sample_docs/` exists. Runtime repository construction is guarded by a process-level lock so
concurrent first requests cannot race DuckDB migration/seed writes.

`migrate()` also applies `002_graph.sql` (all `CREATE TABLE IF NOT EXISTS`, so re-running
migration is safe) and seeds `entities`/`entity_aliases` from the YAML dictionaries on every
run; `_upsert_entity` uses `ON CONFLICT ... DO UPDATE` on `entity_id` and on
`(alias_norm, entity_id)`, so repeated seeding does not duplicate rows.
`resolve_alias()` resolves both canonical names and known aliases, including Cyrillic aliases
(`МН30`/`мн30` → `mat_cuni_30`; `Ni-30Cu`/`Ni–30Cu` → `mat_nicu_30`; `старение` →
`regime_aging`; `твердость по Виккерсу` → `prop_vickers_hardness`; unknown mentions return
`None`).

CSV uploads must include `experiment_id`, `material`, `regime`, `temperature_c`, `duration_h`,
`atmosphere`, `property`, `method`, `baseline_value`, `treated_value`, `unit`, and `effect`.
Uploaded rows become `table_row` evidence spans plus source-scoped measurements/effects. Markdown
or text uploads are stored as evidence spans without deriving measurements in P0.
Upload accepts `.csv`, `.md`, `.markdown`, `.txt`, `.text`; other extensions are rejected.
The API also rejects blank filenames, path separators, control characters, overlong filenames,
unsupported MIME types, empty files, and payloads larger than `MAX_SOURCE_UPLOAD_BYTES`
(code default `5242880` bytes in `services/api/routes/sources.py`; `.env.example` now samples
`MAX_SOURCE_UPLOAD_BYTES=26214400`, see `mem:TECHDEBT-01-NOW` for the resulting Nginx-limit
mismatch). Bundled web Nginx sets `client_max_body_size 6m` so multipart overhead
is not rejected before FastAPI can return the structured upload error.

`DemoQAService` now applies `AskRequest.filters` before ranking experiments; filtered
queries can constrain by `source_ids`, `material`/`material_name`, `property`/`property_name`,
`regime`/`regime_id`, and other stable keys from experiment metadata.
The filters model is now typed as `AskFilters`:
`source_ids`, `source_id`, `material_name`, `material`,
`property_name`, `property`, `regime_summary`, `regime`,
`experiment_id`, and `regime_id`.
Single scalar values are coerced to one-element lists to preserve API usability,
while unknown filter keys are rejected by request validation.

Frontend now includes a dedicated workbench filter surface and sends `AskFilters`
for source/material/property/regime/experiment scope at request time.
Free-text QA extracts explicit material-like tokens containing element symbols and composition
numbers. Known tokens such as `Ni-30Cu`, `Ni 30 Cu`, and `Cu Ni 30` stay scoped to that material;
unknown tokens such as `Ni-20`, `ni 20`, and `Ni–20` return an empty grounded result plus close
material suggestions through `follow_up_queries`.

## Contracts And Data

Separate IDs are implemented for `source_id`, `artifact_id`, `span_id`, `fact_id`, and `claim_id`. `span_id` does not include `extraction_run_id`, and `tests/unit/test_ids.py` verifies whitespace-normalized span stability. Measurement and effect IDs include `source_id` for CSV/table ingestion, and experiment row assembly joins measurements to effects by `experiment_id`, `property_id`, and `source_id`; uploaded overlapping CSV sources must not overwrite seeded report facts.

Table rows and table cells are first-class evidence units. `EffectClaim` is required for "what effect" answers and must reference baseline/treated measurements or be marked qualitative-only.

Current canonical demo graph path is linear for UI clarity: `Material -> Experiment -> Regime -> Step -> Measurement -> Property -> Evidence -> Document`.

`entities` rows carry `entity_id`, `entity_type`, `canonical_key`, `canonical_name`,
`metadata_json`, `evidence_span_ids_json`, `confidence`, and `validation_status`.
`entity_aliases` is keyed by `(alias_norm, entity_id)` with `alias` and `source` columns
(`'dictionary'` for seeded rows). `relations` links `src_entity_id`/`dst_entity_id` through a
`relation_type`, evidence span IDs, confidence, and `validation_status`. `ingestion_runs`,
`artifacts`, `extraction_claims`, `answer_runs`, and `eval_results` are prepared for the P1
extraction/answer/evaluation pipelines but are not yet written by any runtime code path.

P0 demo dictionaries cover Ni-Cu, Cu-Ni, and Ni-Cr-Mo alloys; annealing, aging, cold rolling, solution treatment/quench, welding/cladding; and hardness, tensile strength, elongation, conductivity, corrosion rate, grain size, porosity/cracking, and phase fraction.

## Invariants

- Do not reconstruct evidence from Qdrant text alone.
- Do not overwrite conflicting measurements or average them silently.
- Numeric measurements require property, value, unit, and supporting spans.
- LLM-extracted facts without existing EvidenceSpan IDs are rejected.
- Final answer sentences without support IDs are rejected.
- Dictionary seeding is upsert-only (`ON CONFLICT ... DO UPDATE`); do not add seeding code that deletes or truncates `entities`/`entity_aliases` on re-run.

## Change Rules

Freeze ID generation before writing ingestion code. Add migrations and domain tests before adding parser/indexing code that writes facts.

## Verification

- `make ci`: runs ruff, mypy, pytest, frontend typecheck, and frontend build.
- `make eval`: verifies citation coverage, unsupported claim count, source-label leak count, prompt-injection fixture count, experiment count, and evidence count for the current synthetic packet.
- `tests/unit/test_dictionary_loader.py`: verifies `canonical_key()` normalization rules, that `load_dictionaries()` seeds all five entity types (`material`, `regime`, `property`, `equipment`, `team`) and is idempotent, and that `МН30`/`Ni-30Cu`/Russian-alias mentions resolve to the expected `entity_id` via `resolve_alias()`.
