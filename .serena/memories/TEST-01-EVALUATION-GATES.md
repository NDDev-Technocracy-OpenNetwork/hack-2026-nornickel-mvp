<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: Makefile; tests/; scripts/run_eval.py; eval/; .github/workflows/ci.yml; pyproject.toml
Area: TEST
-->

# TEST-01-EVALUATION-GATES

## Purpose

Capture required verification and acceptance gates after the real-corpus hardening wave.

## Source Of Truth

- `scripts/run_eval.py`: hardcoded `EVAL_QUESTIONS` list of 12 question dicts run against the
  live `DemoQAService` and a temp-copy DuckDB ledger, covering only the synthetic corpus.
- `eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml`: legacy
  YAML fixtures kept in the repo but not referenced by any code path.
- `tests/unit/`: ID stability, claim verifier, source-label policy, dictionary-loader, LLM
  gateway, entity resolution, extraction service, retrieval service, answer composer, ingestion
  service, and scope/constraint tests.
- `tests/integration/`: FastAPI, DuckDB ledger, graph API, ingest API, and synthetic-v2-corpus
  tests.
- `make ci` / `make eval`: local gates matching CI.

## Current Behavior

`uv run pytest` passes **96 tests, 3 skipped** at `41ee7ac` — verified by a live run in this
sync pass (test-progress output totaled 99 outcomes: 96 `.` and 3 `s`, no failures). This is an
increase of 6 tests over the previously recorded 90-passed baseline at `ece33d3`, matching the 6
new test functions added by `tests/unit/test_scope_and_constraints.py` (see below). `ruff`/
`mypy` were not re-run in this sync pass.

The 3 skips remain `pytest.importorskip("docling")` / `pytest.importorskip("trafilatura")`
guards in `tests/integration/test_synthetic_v2_corpus.py`
(`test_docx_corpus_ingests_with_docling`, `test_scan_pdf_quarantines_with_docling`,
`test_html_fixture_extracts_via_trafilatura_offline`).

`tests/unit/test_scope_and_constraints.py` (new, `58760b3`) has 6 test functions:
`test_numeric_constraint_parser_handles_ru_operators` (RU/symbolic numeric operator parsing:
"не более", "≤", "не менее"), `test_author_extraction_ru_and_en` (`_extract_authors` on a mixed
RU/EN article head), `test_real_domain_dictionary_resolves` (шлак/электроэкстракция/ПВП/
"скорость циркуляции" all resolve via the extended dictionaries), `test_publication_and_authors_linked`
(a source becomes a `publication` entity with `DESCRIBED_IN`/`AUTHORED_BY` relations after
`ExtractionService.process_source`), `test_geography_and_year_scope_filters` (an `AskFilters`
`geography`/`year_from`/`year_to` combination correctly includes/excludes an experiment based on
`set_source_metadata`), and `test_numeric_constraint_filters_experiments` (a "не более 250 HV"
question filters out a 320 HV experiment while keeping a 245 HV one).

`scripts/run_eval.py`'s 12 `EVAL_QUESTIONS` are unchanged by this wave and still cover only the
synthetic `sample_docs/synthetic`/`synthetic_v2` corpora (ideal Ni-30Cu scenario, Cyrillic-alias
resolution, provenance, comparison, gap, conflict, unknown-material negative controls, exact
spaced-material scoping, and one broad family query). **No gold-question set exists yet for the
real `DATA_HACK/` corpus** or for the new geography/year/numeric-constraint filters at the
`/eval/summary` level — those are covered only by `tests/unit/test_scope_and_constraints.py`
against synthetic fixtures (see `mem:TECHDEBT-01-NOW`).

CI runs the same backend (`uv sync --group dev`, `ruff`, `mypy`, `pytest`,
`uv run python scripts/run_eval.py`) and frontend (`npm ci`, `typecheck`, `build`) checks; the
backend job still does not pass `--extra ingest`.

## Contracts And Data

Non-negotiable demo gates remain `unsupported_claim_count = 0` and
`source_label_leak_count = 0`; `run_eval.py` raises `SystemExit(1)` if any `EVAL_QUESTIONS` case
fails its assertions.

`tests/unit/test_scope_and_constraints.py` protects: RU/symbolic numeric-constraint parsing and
filtering, the real-domain dictionary extension's resolvability, publication/author graph
linking, and geography/year scope filtering — all against synthetic in-memory DuckDB fixtures
built with `DuckDBLedgerRepository(tmp_path / "scope.duckdb")`.

## Invariants

- Do not mark a demo answer successful if unsupported final sentences exist.
- Do not mark a security run successful if restricted evidence enters the context packet.
- Whenever `scripts/run_eval.py`'s `EVAL_QUESTIONS` changes, keep the question count and this
  memory's description in sync in the same change; do not resurrect `eval/*.yml` as a second
  source of truth without wiring it into code first.
- Whenever the real-corpus ontology or scope filters change, extend
  `tests/unit/test_scope_and_constraints.py` in the same change.

## Change Rules

When new ingestion/retrieval/extraction behavior is added, extend `EVAL_QUESTIONS` in
`scripts/run_eval.py` and the relevant `tests/unit/` or `tests/integration/` module in the same
change.

## Verification

- `make ci`: ruff, mypy, pytest (96 passed, 3 skipped at `41ee7ac`, live-run verified), frontend
  typecheck, build.
- `make eval`: `scripts/run_eval.py` — 12-question live QA metrics against the synthetic DuckDB
  ledger only.
- `docker compose config`: Compose validation.
