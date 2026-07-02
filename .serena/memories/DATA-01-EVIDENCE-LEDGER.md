<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: src/nornikel_kg/domain/; src/nornikel_kg/adapters/duckdb/;
  src/nornikel_kg/resources/dictionaries/; src/nornikel_kg/services/; sample_docs/; eval/;
  scripts/ingest_corpus.py
Area: DATA
-->

# DATA-01-EVIDENCE-LEDGER

## Purpose

Capture evidence identity, artifact memory, scientific schemas, graph/entity/relation storage,
retrieval-unit indexing, and answer-run/eval persistence in the DuckDB ledger.

## Source Of Truth

- `src/nornikel_kg/domain/ids.py`: stable `source_id`, `artifact_id`, `span_id`, `fact_id`,
  `claim_id` helpers.
- `src/nornikel_kg/domain/models.py`: Pydantic API/domain payload models, including
  `AskFilters.geography`/`year_from`/`year_to`.
- `src/nornikel_kg/domain/evidence.py`: `EvidenceSpanFactory`.
- `src/nornikel_kg/domain/normalization.py`: `canonical_key()` mention-normalization helper.
- `src/nornikel_kg/domain/extraction.py`: entity/relation type vocabularies (`ENTITY_TYPES`,
  `RELATION_TYPES`) and the LLM extraction JSON schema — does not include `publication`/
  `DESCRIBED_IN` (see `mem:ARCH-01-EVIDENCE-MVP`).
- `src/nornikel_kg/domain/analysis.py`: `ConflictDetector`/`GapAnalyzer`.
- `src/nornikel_kg/adapters/duckdb/migrations/001_init.sql`, `002_graph.sql`: ledger and
  graph/knowledge schema.
- `src/nornikel_kg/adapters/duckdb/dictionary_loader.py`: idempotent entity/alias seeding.
- `src/nornikel_kg/adapters/duckdb/repositories.py`: `DuckDBLedgerRepository` — the single
  DuckDB adapter for ledger, graph, retrieval-unit listing, and eval persistence.
- `src/nornikel_kg/resources/dictionaries/{materials,regimes,properties,equipment}.yml`:
  dictionary-seeded ontology (see "Real-Corpus Ontology Extension" below).
- `sample_docs/synthetic/`: original P0 fixture. `sample_docs/synthetic_v2/`: W5 corpus.
- `scripts/ingest_corpus.py`: batch real-corpus ingester (see `mem:RELEASE-01-VALIDATION`).
- `eval/*.yml`: legacy fixtures, no longer read by any code (`mem:TEST-01-EVALUATION-GATES`).

## Entry Points

- `DuckDBLedgerRepository.seed_synthetic_fixture` / `ingest_source_bytes`: CSV/Markdown/text
  ingest into `sources`/`evidence_spans`/`property_measurements`/`effect_claims`.
- `DuckDBLedgerRepository.ingest_parsed_document(...)`: writes text/table-row evidence spans
  from a `ParsedDocument`.
- `DuckDBLedgerRepository.record_ingestion_run` / `list_ingestion_runs` /
  `latest_run_statuses`: ingestion run ledger.
- `DuckDBLedgerRepository.set_source_metadata(source_id, *, year: int | None, geography: str |
  None)`: `UPDATE sources SET year = COALESCE(?, year), geography = COALESCE(?, geography) WHERE
  source_id = ?` — a `COALESCE` update, so a later call with `None` never clears an
  already-set value. Called by `IngestionService._apply_source_metadata` after every parsed
  ingest (best-effort, wrapped in a broad `except Exception` so metadata failures never block
  ingest).
- `DuckDBLedgerRepository.source_metadata() -> dict[str, dict[str, Any]]`: `SELECT source_id,
  year, geography FROM sources`, returned as `{source_id: {"year": int | None, "geography": str
  | None}}`; consumed by `DemoQAService._apply_source_scope` via the `RunRecorderProtocol`
  contract.
- `DuckDBLedgerRepository._connect()`: a `@contextmanager` used by every read/write method,
  serializing access behind a class-level `threading.RLock` (`_db_lock`). As of commit
  `f40ab72`, this now holds **one persistent** `duckdb.DuckDBPyConnection` per repository
  instance (`self._connection`) instead of opening/closing a new connection per call — verified:
  `self._connection = duckdb.connect(str(self.db_path))` only runs `if self._connection is
  None`. Consequence: the process holding this repository instance holds the DuckDB file lock
  for its lifetime; an external process (e.g. a `docker exec` DuckDB CLI session) cannot open
  the same file while the `api` service is running.
- `DuckDBLedgerRepository.load_demo_packet`: returns the full evidence/graph packet used by
  `DemoQAService`; returns an empty `EvidenceLedgerPacket` when the ledger is empty.
- `load_dictionaries(connection, dictionaries_dir=None)` / `resolve_alias(connection, mention)`:
  dictionary seeding/lookup helpers.
- Entity/relation repository methods: `find_entity`, `get_entity`, `create_entity`,
  `merge_entity_evidence`, `insert_relation`, `insert_extraction_claim`, `search_entities`,
  `list_graph_entities`, `list_graph_relations`, `list_alias_index`.
- Eval/answer persistence: `record_answer_run`/`get_answer_run`; `store_eval_result`/
  `latest_eval_summary`.

## Current Behavior

CSV uploads still require the P0 measurement columns and become `table_row` spans plus
source-scoped measurements/effects. PDF/DOCX uploads route through `DoclingDocumentParser`;
a PDF with no extractable text layer is quarantined with zero evidence spans.

Every parsed ingest additionally calls `_apply_source_metadata` (in `IngestionService`), which
writes `sources.year`/`sources.geography` via `set_source_metadata` using filename+head-text
year detection and a Cyrillic-vs-Latin geography heuristic (see `mem:ARCH-01-EVIDENCE-MVP` for
the exact heuristic). `sources.year`/`sources.geography` are added via
`DuckDBLedgerRepository.migrate`'s `_ensure_column(connection, "sources", "year", "INTEGER")` /
`_ensure_column(connection, "sources", "geography", "TEXT")` — additive, non-destructive schema
evolution, unchanged migration mechanism from P0.

Extraction writes `entities`/`entity_aliases`/`relations`/`extraction_claims` rows keyed by
stable IDs; every source additionally gets one `publication` entity plus `DESCRIBED_IN`/
`AUTHORED_BY` relations via `ExtractionService._link_publication` (`mem:ARCH-01-EVIDENCE-MVP`).
`EntityResolutionService` never merges entities across `entity_type` and treats a canonical-key
mismatch (but existing entity match) as an alias addition rather than a new entity.

Retrieval indexing writes into two Qdrant collections when `EMBEDDING_BACKEND` is not `off`:
`evidence_units` and `entities`. Both are rebuilt per-source via `RetrievalService.index_source`
and in bulk via `reindex_all()`, now exposed through `POST /sources/reindex-all`
(`mem:RELEASE-01-VALIDATION`).

## Real-Corpus Ontology Extension (2026-07-03, commit `58760b3`)

`src/nornikel_kg/resources/dictionaries/materials.yml` gained 17 metallurgy-domain entries
covering slag/matte pyrometallurgy (slag, copper matte, nickel matte), electrowinning (cathode
nickel, electrolyte/catholyte), desalination (technogenic gypsum, sulfates, chlorides, SO2),
beneficiation (nickel ore, concentrate), and general metallurgy (PGM/precious metals, copper,
nickel, cobalt, metallic phase) — verified via `grep` for the specific canonical names/aliases.
`regimes.yml` gained leaching, electrowinning, slag depletion, converting, smelting, flotation,
desalination, drying, circulation, injection (15 `canonical_name:` entries total, verified by
count). `properties.yml` gained concentration, flow rate, extraction, temperature, coalescence,
metal-loss properties (14 entries total, verified by count). `equipment.yml` gained Vanyukov
furnace, flash smelting furnace, electrowinning bath/cell, diaphragm cell, flotation machine,
tube furnace (9 total entries: 3 original demo entries + 6 new, verified by listing).
**Geomechanics-specific terms are not covered** (verified: no matching alias hits for
`геомех`/`geomechanic`/`горн` in any dictionary file), so this extension only partially closes
gap G1 from `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md` for the full real-corpus
domain span.

`tests/unit/test_scope_and_constraints.py::test_real_domain_dictionary_resolves` verifies
`find_entity("шлак", "material")`, `find_entity("электроэкстракция", "regime")`,
`find_entity("ПВП", "equipment")`, and `find_entity("скорость циркуляции", "property")` all
resolve; `test_publication_and_authors_linked` verifies a source becomes a `publication` entity
with `DESCRIBED_IN`/`AUTHORED_BY` relations after `ExtractionService.process_source`.

## W5 Synthetic Corpus

`scripts/generate_synthetic_docs.py` deterministically writes `sample_docs/synthetic_v2/`
(17 committed sources per `manifest.json`): 4 measurement CSVs, 6 RU DOCX protocols, 3 RU
Markdown notes, 2 EN reportlab PDFs, 1 image-only quarantine PDF, and 1 HTML page, plus
`manifest.json`. `tests/integration/test_synthetic_v2_corpus.py` verifies manifest-vs-committed
consistency and offline/docling/trafilatura-gated ingestion behavior.

## Contracts And Data

Separate IDs for `source_id`, `artifact_id`, `span_id`, `fact_id`, `claim_id`. Table rows/cells
remain first-class evidence units. `entities` rows carry `entity_id`, `entity_type`,
`canonical_key`, `canonical_name`, `metadata_json`, `evidence_span_ids_json`, `confidence`,
`validation_status`. `sources` rows now also carry `year`/`geography` (nullable, additively
migrated). Gap analysis (`GapAnalyzer`) only considers dictionary-seeded entities (IDs not
starting with `ent_`), so `publication`/`person` entities (which use `ent_` IDs via
`EntityResolutionService`) never appear in the coverage matrix.

## Invariants

- Do not reconstruct evidence from Qdrant text alone; hybrid search hits are always rejoined
  against DuckDB and re-filtered by `security_label` before being trusted.
- Do not overwrite conflicting measurements or average them silently.
- Do not call `duckdb.connect(...)` directly from repository methods; always go through
  `DuckDBLedgerRepository._connect()`. The connection is now persistent per instance, so
  external out-of-process access to the DuckDB file is not possible while an instance holding
  the lock (e.g. the running `api` service) is alive.
- Numeric measurements require property, value, unit, and supporting spans.
- LLM-extracted facts without existing EvidenceSpan IDs are rejected; invalid LLM extraction
  payloads are recorded with `status="rejected"` in `extraction_claims` and fall back to
  rule-only mentions.
- `set_source_metadata` uses `COALESCE`, so passing `None` for `year`/`geography` never clears a
  previously-set value.
- Dictionary seeding is upsert-only; entity resolution never merges across `entity_type`.
- Parser/extraction/retrieval failures degrade the ledger write (quarantine, empty indexed
  count, rule-only fallback) but never lose the source registration row.

## Change Rules

Extend `sample_docs/synthetic_v2/manifest.json` and
`tests/integration/test_synthetic_v2_corpus.py` together whenever the synthetic corpus changes.
Extend `tests/unit/test_scope_and_constraints.py` and the relevant dictionary YAML together
whenever the real-corpus ontology changes. Add migrations and domain tests before adding
parser/indexing code that writes new fact types.

## Verification

- `uv run pytest`: 96 tests pass, 3 skipped, at `41ee7ac` (live-run verified in this sync pass).
- `make eval`: `scripts/run_eval.py` — 12 hardcoded questions against the synthetic corpus only.
- `tests/unit/test_dictionary_loader.py`, `tests/unit/test_scope_and_constraints.py`: dictionary
  seeding/idempotency/alias resolution, real-domain ontology resolution, publication/author
  linking, geography/year scope filters, numeric constraint filters.
- `tests/unit/test_entity_resolution.py`, `tests/unit/test_extraction_service.py`,
  `tests/unit/test_retrieval_service.py`, `tests/unit/test_answer_composer.py`,
  `tests/unit/test_ingestion_service.py`: unit coverage for services.
- `tests/integration/test_graph_api.py`, `tests/integration/test_ingest_api.py`: API-level
  coverage for entity/graph/ingest endpoints.
