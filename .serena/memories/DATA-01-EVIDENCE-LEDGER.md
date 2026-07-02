<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: ece33d3 docs(plans): record completed dataeyes discovery and configured dev model
Scope: src/nornikel_kg/domain/; src/nornikel_kg/adapters/duckdb/; src/nornikel_kg/resources/dictionaries/; src/nornikel_kg/services/; sample_docs/; eval/
Area: DATA
-->

# DATA-01-EVIDENCE-LEDGER

## Purpose

Capture evidence identity, artifact memory, scientific schemas, graph/entity/relation storage,
retrieval-unit indexing, and answer-run/eval persistence in the DuckDB ledger.

## Source Of Truth

- `src/nornikel_kg/domain/ids.py`: stable `source_id`, `artifact_id`, `span_id`, `fact_id`,
  `claim_id` helpers, plus `source_id_from_bytes`/`stable_hash` used by W1-W3 code.
- `src/nornikel_kg/domain/models.py`: Pydantic API/domain payload models.
- `src/nornikel_kg/domain/evidence.py`: `EvidenceSpanFactory`.
- `src/nornikel_kg/domain/normalization.py`: `canonical_key()` mention-normalization helper.
- `src/nornikel_kg/domain/extraction.py`: entity/relation type vocabularies and the LLM
  extraction JSON schema (see `mem:ARCH-01-EVIDENCE-MVP`).
- `src/nornikel_kg/domain/analysis.py`: `ConflictDetector`/`GapAnalyzer`.
- `src/nornikel_kg/ports/parser.py`, `ports/retrieval.py`, `ports/extraction.py`: port
  contracts for parsing, retrieval, and mention extraction.
- `src/nornikel_kg/adapters/duckdb/migrations/001_init.sql`: P0 ledger tables.
- `src/nornikel_kg/adapters/duckdb/migrations/002_graph.sql`: graph/knowledge schema
  (`ingestion_runs`, `artifacts`, `entities`, `entity_aliases`, `relations`,
  `extraction_claims`, `answer_runs`, `eval_results`) — all now written by runtime code.
- `src/nornikel_kg/adapters/duckdb/dictionary_loader.py`: idempotent entity/alias seeding.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: `DuckDBLedgerRepository` — the single
  DuckDB adapter for ledger, graph, retrieval-unit listing, and eval persistence.
- `sample_docs/synthetic/`: original P0 fixture (report + mechanical property table).
- `sample_docs/synthetic_v2/`: W5 corpus (see "W5 Synthetic Corpus" below).
- `eval/*.yml`: legacy fixtures, no longer read by any code (`mem:TEST-01-EVALUATION-GATES`).

## Entry Points

- `DuckDBLedgerRepository.seed_synthetic_fixture` / `ingest_source_bytes`: CSV/Markdown/text
  ingest into `sources`/`evidence_spans`/`property_measurements`/`effect_claims`.
- `DuckDBLedgerRepository.ingest_parsed_document(source_id, raw_sha256, title, document_type,
  parsed: ParsedDocument, artifact_locator)`: writes text and table-row evidence spans from a
  `ParsedDocument` (Docling/trafilatura output or the empty quarantine placeholder); returns
  `(text_span_count, table_span_count)`.
- `DuckDBLedgerRepository.record_ingestion_run(run_id, source_id, status, stage, error=None,
  counters=None)`: appends a row to `ingestion_runs`; `status` is one of
  `running`/`completed`/`quarantined`.
- `DuckDBLedgerRepository.list_ingestion_runs(source_id=None)` /
  `latest_run_statuses() -> dict[source_id, status]`: read the run ledger; `list_sources()`
  joins the latest run status (`MAX(ir.status)` via a `ROW_NUMBER()` window) into each
  `SourceSummary.status`, falling back to `"ledger"` when no run row exists.
- `DuckDBLedgerRepository.get_source` / `delete_source`: unchanged from P0.
- `DuckDBLedgerRepository.migrate`: applies every `migrations/*.sql` file, backfills legacy
  columns, and seeds the graph dictionaries via `load_dictionaries(connection)`; runs at most
  once per repository instance (`self._migrated` guard) instead of once per call.
- `DuckDBLedgerRepository._connect()`: a `@contextmanager` used by every read/write method
  instead of a bare `duckdb.connect(...)`; it serializes all access behind a class-level
  `threading.RLock` (`_db_lock`) because concurrent request threads sharing one repository
  instance used to race on writes (`TransactionContext Error: Conflict on update!`). Fixed in
  `src/nornikel_kg/adapters/duckdb/repositories.py` (merge PR#12, `31f2459`).
- `DuckDBLedgerRepository.load_demo_packet`: returns the full evidence/graph packet used by
  `DemoQAService`; returns an **empty** `EvidenceLedgerPacket` when the ledger has no sources
  or evidence — it does not raise `LookupError` (verified: no such raise exists in
  `repositories.py`).
- `load_dictionaries(connection, dictionaries_dir=None)` / `resolve_alias(connection, mention)`:
  unchanged dictionary seeding/lookup helpers from W0.
- Entity/relation repository methods (all in `repositories.py`): `find_entity(mention,
  entity_type=None)`, `get_entity(entity_id)`, `create_entity(...)`,
  `merge_entity_evidence(entity_id, span_ids, new_alias=None)`, `insert_relation(src_entity_id,
  relation_type, dst_entity_id, evidence_span_ids)`, `insert_extraction_claim(claim_id_value,
  source_id, span_id, payload, model_id, status)`, `search_entities(query, limit=20)`,
  `list_graph_entities()`, `list_graph_relations()`, `list_alias_index() ->
  list[tuple[alias_norm, entity_type, alias]]`.
- Eval/answer persistence: `record_answer_run(run_id, question, filters, packet_stats,
  model_id, latency_ms, verification)` / `get_answer_run(run_id)`; `store_eval_result(run_id,
  question_id, metrics)` / `latest_eval_summary()`.

## Current Behavior

CSV uploads still require `experiment_id`, `material`, `regime`, `temperature_c`, `duration_h`,
`atmosphere`, `property`, `method`, `baseline_value`, `treated_value`, `unit`, `effect`, and
become `table_row` evidence spans plus source-scoped measurements/effects. Markdown/text
uploads remain evidence spans without derived measurements.

PDF/DOCX uploads route through `DoclingDocumentParser` (`do_ocr=False`, `do_table_structure=
True`); each Docling `ParsedBlock` becomes a `text` evidence span with a `block_N[:bbox_LxT]`
locator and page number, and each `ParsedTableRow` becomes a `table_row` span. A PDF with no
extractable text layer raises `NoTextLayerError`, which the ingestion service turns into a
`quarantined` run row with **zero** evidence spans (the source row itself is still registered so
the UI can show the quarantined state) — OCR is explicitly out of scope. URL imports route
through `TrafilaturaUrlFetcher.fetch`, producing one `ParsedBlock` per non-empty line with
`parser_profile="trafilatura_v1"` and optional `date` metadata.

Every successful or quarantined ingest writes an `ingestion_runs` row
(`run_id = "ing_" + stable_hash([source_id], 16)`). Raw uploaded/fetched bytes are archived
best-effort under `ARTIFACT_ROOT/sources/<source_id>/<filename or "parsed.txt">`
(`ARTIFACT_ROOT` defaults to `data/artifacts`, resolved via `services/runtime.py`); archive
failures are logged and never block ingestion.

Extraction writes `entities`/`entity_aliases`/`relations`/`extraction_claims` rows keyed by
stable IDs (`ent_<type>_<hash>` for created entities); `EntityResolutionService` never merges
entities across `entity_type` and treats a canonical-key mismatch (but existing entity match) as
an alias addition rather than a new entity.

Retrieval indexing writes into two Qdrant collections when `EMBEDDING_BACKEND` is not `off`:
`evidence_units` (`QDRANT_COLLECTION` env, default name) carries `source_id`, `span_type`,
`security_label` payload; `entities` carries `entity_type` payload. Both are rebuilt per-source
via `RetrievalService.index_source` (delete-then-reindex) and in bulk via `reindex_all()`.

## W5 Synthetic Corpus

`scripts/generate_synthetic_docs.py` deterministically writes `sample_docs/synthetic_v2/`
(17 committed sources — verified via `manifest.json` `sources` list and directory listing): 4
measurement CSVs (`v2_measurements_cuni.csv`, `_nicrmo.csv`, `_nicu.csv`, `_solution.csv`), 6 RU
DOCX protocols (`v2_protocol_01..06_*.docx`, built with `python-docx`), 3 RU Markdown notes
(`v2_note_corrosion.md`, `_decisions.md`, `_qualitative.md`), 2 EN reportlab PDFs
(`v2_report_nicrmo_rolling_en.pdf`, `_nicu_aging_en.pdf`), 1 image-only quarantine PDF
(`v2_scan_no_text_layer.pdf`), and 1 HTML page for URL import (`v2_online_resource.html`), plus
`manifest.json`. The corpus seeds analytics fixtures: an HV-vs-HRC method mismatch, a
contradictory elongation direction, coverage gaps, dated decision/conclusion entities for the
timeline, alias pairs `МН30`/`CuNi30` and `Ni30Cu`/`Ni-30Cu`, and one injected prompt-like line
in `v2_protocol_02` (untrusted evidence text, not followed as an instruction — see
`mem:SEC-01-ACL-AND-PROMPT-INJECTION`).
`tests/integration/test_synthetic_v2_corpus.py` verifies manifest-vs-committed-file
consistency, offline CSV/Markdown ingestion with conflict and alias assertions
(`test_csv_and_markdown_corpus_ingests_offline`), and `docling`/`trafilatura`-gated tests via
`pytest.importorskip` (`test_docx_corpus_ingests_with_docling`,
`test_scan_pdf_quarantines_with_docling`, `test_html_fixture_extracts_via_trafilatura_offline`)
that skip when those optional packages are absent.

## Contracts And Data

Separate IDs for `source_id`, `artifact_id`, `span_id`, `fact_id`, `claim_id` unchanged from P0.
Table rows/cells remain first-class evidence units.

`entities` rows carry `entity_id`, `entity_type`, `canonical_key`, `canonical_name`,
`metadata_json`, `evidence_span_ids_json`, `confidence`, `validation_status`. `entity_aliases`
is keyed by `(alias_norm, entity_id)`. `relations` links `src_entity_id`/`dst_entity_id`
through `relation_type`, evidence span IDs, confidence, `validation_status`. `ingestion_runs`,
`artifacts`, `extraction_claims`, `answer_runs`, and `eval_results` are all now written by
runtime code paths (ingestion, extraction, QA, and eval respectively) — none remain unused P1
placeholders.

P0/P1 dictionaries cover Ni-Cu, Cu-Ni, Ni-Cr-Mo alloys; annealing, aging, cold rolling, solution
treatment/quench, welding/cladding; and hardness, tensile strength, elongation, conductivity,
corrosion rate, grain size, porosity/cracking, phase fraction. Gap analysis (`GapAnalyzer`) only
considers dictionary-seeded entities (IDs not starting with `ent_`), so extracted-but-unseeded
entities never appear in the coverage matrix.

## Invariants

- Do not reconstruct evidence from Qdrant text alone; hybrid search hits are always rejoined
  against DuckDB and re-filtered by `security_label` before being trusted
  (`RetrievalService.retrieve_span_ids`).
- Do not overwrite conflicting measurements or average them silently.
- Do not call `duckdb.connect(...)` directly from repository methods; always go through
  `DuckDBLedgerRepository._connect()` so concurrent request threads stay serialized.
- Numeric measurements require property, value, unit, and supporting spans.
- LLM-extracted facts without existing EvidenceSpan IDs are rejected; invalid LLM extraction
  payloads are recorded with `status="rejected"` in `extraction_claims` and fall back to
  rule-only mentions.
- Final answer sentences without support IDs are rejected/dropped by the composer.
- Dictionary seeding is upsert-only; entity resolution never merges across `entity_type`.
- Parser/extraction/retrieval failures degrade the ledger write (quarantine, empty indexed
  count, rule-only fallback) but never lose the source registration row.

## Change Rules

Extend `sample_docs/synthetic_v2/manifest.json` and
`tests/integration/test_synthetic_v2_corpus.py` together whenever the synthetic corpus changes.
Add migrations and domain tests before adding parser/indexing code that writes new fact types.

## Verification

- `make ci`: runs ruff, mypy, pytest (90 passed, 3 skipped at `ece33d3`), frontend typecheck/build.
- `make eval`: `scripts/run_eval.py` — 12 hardcoded questions verifying citation coverage,
  material alias resolution (`МН30` -> `CuNi30`), provenance, comparison, gap, and conflict
  behavior against the live DuckDB ledger.
- `tests/unit/test_dictionary_loader.py`: dictionary seeding/idempotency/alias resolution.
- `tests/unit/test_entity_resolution.py`, `tests/unit/test_extraction_service.py`,
  `tests/unit/test_retrieval_service.py`, `tests/unit/test_answer_composer.py`,
  `tests/unit/test_ingestion_service.py`: unit coverage for the W1-W3 services.
- `tests/integration/test_graph_api.py`, `tests/integration/test_ingest_api.py`: API-level
  coverage for entity/graph/ingest endpoints.
