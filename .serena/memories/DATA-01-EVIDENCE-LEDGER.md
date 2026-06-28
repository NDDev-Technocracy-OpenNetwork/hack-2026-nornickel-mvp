<!-- Memory Metadata
Last updated: 2026-06-29
Last commit: a3bf103 feat: expose QA filters in frontend workbench
Scope: src/nornikel_kg/domain/; src/nornikel_kg/adapters/duckdb/; src/nornikel_kg/services/qa_service.py; src/nornikel_kg/services/runtime.py; sample_docs/synthetic/; eval/
Area: DATA
-->

# DATA-01-EVIDENCE-LEDGER

## Purpose

Capture evidence identity, artifact memory, scientific schemas, and answer-claim contracts.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: ID policy, artifact layout, minimum DuckDB tables, and required schemas.
- `src/nornikel_kg/domain/ids.py`: implemented stable `source_id`, `artifact_id`, `span_id`, `fact_id`, and `claim_id` helpers.
- `src/nornikel_kg/domain/models.py`: implemented Pydantic API/domain payload models.
- `src/nornikel_kg/domain/evidence.py`: implemented `EvidenceSpanFactory`.
- `src/nornikel_kg/adapters/duckdb/migrations/001_init.sql`: implemented P0 ledger tables.
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
- `DuckDBLedgerRepository.load_demo_packet`: returns the current evidence packet used by QA.
- `DemoQAService.ask`: assembles the response from an `EvidenceLedgerPort` when provided, otherwise uses a deterministic fallback packet.

## Current Behavior

The implemented scaffold writes a DuckDB evidence ledger with `sources`, `evidence_spans`,
`property_measurements`, `effect_claims`, and `answer_claims`. Runtime seeding happens through
`get_ledger_repository()` using `PROJECT_ROOT`, `DUCKDB_PATH`, and `SYNTHETIC_SAMPLE_DIR`,
defaulting to `data/catalog.duckdb` and `sample_docs/synthetic`. Container runtime sets
`PROJECT_ROOT=/app`; local runtime falls back to the current working directory when
`sample_docs/` exists. Runtime repository construction is guarded by a process-level lock so
concurrent first requests cannot race DuckDB migration/seed writes.

CSV uploads must include `experiment_id`, `material`, `regime`, `temperature_c`, `duration_h`,
`atmosphere`, `property`, `method`, `baseline_value`, `treated_value`, `unit`, and `effect`.
Uploaded rows become `table_row` evidence spans plus source-scoped measurements/effects. Markdown
or text uploads are stored as evidence spans without deriving measurements in P0.
Upload accepts `.csv`, `.md`, `.markdown`, `.txt`, `.text`; other extensions are rejected.

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

## Contracts And Data

Separate IDs are implemented for `source_id`, `artifact_id`, `span_id`, `fact_id`, and `claim_id`. `span_id` does not include `extraction_run_id`, and `tests/unit/test_ids.py` verifies whitespace-normalized span stability. Measurement and effect IDs include `source_id` for CSV/table ingestion, and experiment row assembly joins measurements to effects by `experiment_id`, `property_id`, and `source_id`; uploaded overlapping CSV sources must not overwrite seeded report facts.

Table rows and table cells are first-class evidence units. `EffectClaim` is required for "what effect" answers and must reference baseline/treated measurements or be marked qualitative-only.

Current canonical demo graph path is linear for UI clarity: `Material -> Experiment -> Regime -> Step -> Measurement -> Property -> Evidence -> Document`.

P0 demo dictionaries cover Ni-Cu, Cu-Ni, and Ni-Cr-Mo alloys; annealing, aging, cold rolling, solution treatment/quench, welding/cladding; and hardness, tensile strength, elongation, conductivity, corrosion rate, grain size, porosity/cracking, and phase fraction.

## Invariants

- Do not reconstruct evidence from Qdrant text alone.
- Do not overwrite conflicting measurements or average them silently.
- Numeric measurements require property, value, unit, and supporting spans.
- LLM-extracted facts without existing EvidenceSpan IDs are rejected.
- Final answer sentences without support IDs are rejected.

## Change Rules

Freeze ID generation before writing ingestion code. Add migrations and domain tests before adding parser/indexing code that writes facts.

## Verification

- `make ci`: runs ruff, mypy, pytest, frontend typecheck, and frontend build.
- `make eval`: verifies citation coverage, unsupported claim count, source-label leak count, prompt-injection fixture count, experiment count, and evidence count for the current synthetic packet.
