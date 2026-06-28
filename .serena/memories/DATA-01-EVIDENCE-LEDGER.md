<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 55e8e19 docs: integrate evidence-led mvp review
Scope: .serena/newproj/nornikel-kg-search/06_API.md; .serena/newproj/nornikel-kg-search/07_DATA.md; .serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md
Area: DATA
-->

# DATA-01-EVIDENCE-LEDGER

## Purpose

Capture evidence identity, artifact memory, scientific schemas, and answer-claim contracts.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: ID policy, artifact layout, minimum DuckDB tables, and required schemas.
- `.serena/newproj/nornikel-kg-search/07_DATA.md`: domain model and graph path.
- `.serena/newproj/nornikel-kg-search/06_API.md`: API-level answer and graph response contracts.

## Entry Points

- Future `src/nornikel_kg/domain/ids.py`: stable ID generation.
- Future `src/nornikel_kg/domain/evidence.py`: evidence span invariants.
- Future `src/nornikel_kg/domain/effects.py`: effect-claim invariants.
- Future `src/nornikel_kg/adapters/duckdb/migrations/001_init.sql`: P0 ledger schema.

## Current Behavior

The planned source of truth is a DuckDB scientific evidence ledger. The artifact bank stores raw files and parser outputs; DuckDB stores source registry, ingestion runs, artifacts, evidence spans, table rows/cells, normalized facts, graph node/edge tables, answer claims, evaluation results, and ACL decisions.

## Contracts And Data

Separate IDs are required: `source_id`, `artifact_id`, `span_id`, `extraction_run_id`, `fact_id`, and `claim_id`. `span_id` must never include `extraction_run_id`.

Table rows and table cells are first-class evidence units. `EffectClaim` is required for "what effect" answers and must reference baseline/treated measurements or be marked qualitative-only.

The canonical graph path uses expanded materials-science context: `Experiment -> Sample -> Material`, `Experiment -> ProcessingRegime -> ProcessStep`, `Experiment -> PropertyMeasurement -> Property`, and `PropertyMeasurement -> EvidenceSpan -> Document`. `EffectClaim` links baseline and treated measurements.

## Invariants

- Do not reconstruct evidence from Qdrant text alone.
- Do not overwrite conflicting measurements or average them silently.
- Numeric measurements require property, value, unit, and supporting spans.
- LLM-extracted facts without existing EvidenceSpan IDs are rejected.
- Final answer sentences without support IDs are rejected.

## Change Rules

Freeze ID generation before writing ingestion code. Add migrations and domain tests before adding parser/indexing code that writes facts.

## Verification

- Future `make test`: must include ID stability, evidence span, unit normalization, and answer claim verifier tests.
- Future `make eval`: must report citation coverage, unsupported claim count, table-row recall, and ACL leak count.

