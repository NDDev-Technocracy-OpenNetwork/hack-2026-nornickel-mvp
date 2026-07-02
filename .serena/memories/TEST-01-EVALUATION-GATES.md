<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: f4bf404 Merge pull request #11 from rldyourmnd/feat/w5-corpus-eval-hardening
Scope: Makefile; tests/; scripts/run_eval.py; eval/; .github/workflows/ci.yml; pyproject.toml
Area: TEST
-->

# TEST-01-EVALUATION-GATES

## Purpose

Capture required verification and acceptance gates after waves W0-W5.

## Source Of Truth

- `scripts/run_eval.py`: the current source of truth for eval fixtures — a hardcoded
  `EVAL_QUESTIONS` list of 12 question dicts run against the live `DemoQAService` and a
  temp-copy DuckDB ledger.
- `eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml`: legacy
  YAML fixtures kept in the repo but **no longer referenced by any code path** (verified: no
  `grep` hits for these filenames under `src/`, `scripts/`, `tests/`, or `Makefile`); treat them
  as stale unless a future change re-wires them.
- `tests/unit/`: ID stability, claim verifier, source-label policy, dictionary-loader, LLM
  gateway, entity resolution, extraction service, retrieval service, answer composer, and
  ingestion service tests.
- `tests/integration/`: FastAPI, DuckDB ledger, graph API, ingest API, and synthetic-v2-corpus
  tests.
- `make ci` / `make eval`: local gates matching CI.

## Current Behavior

`uv run pytest` passes **89 tests, 3 skipped** at `f4bf404`; `uv run ruff check .` and
`uv run mypy` report no issues. The 3 skips are `pytest.importorskip("docling")` /
`pytest.importorskip("trafilatura")` guards in
`tests/integration/test_synthetic_v2_corpus.py` (`test_docx_corpus_ingests_with_docling`,
`test_scan_pdf_quarantines_with_docling`, `test_html_fixture_extracts_via_trafilatura_offline`);
they run when the `ingest` optional dependency group is installed.

`scripts/run_eval.py`'s 12 `EVAL_QUESTIONS` cover: the ideal Ni-30Cu aging/hardness scenario
(`q_ideal_nicu_hardness`), a Cyrillic-alias resolution check (`q_alias_mn30_returns_cuni30`:
`МН30` must resolve to `CuNi30` via `expected_material_names_contain`), a provenance question
(`q_provenance_ideal`), a two-material comparison (`q_comparison_two_materials`), a missing-
conductivity gap (`q_gap_nicu_conductivity`), a method-mismatch conflict
(`q_conflict_method`), three unknown-material-token negative controls
(`q_unknown_material_nicu20_*`: `ni-20`, `ni 20`, `Ni–20`, each expecting zero
experiments/evidence plus `expected_follow_up_contains` close-material suggestions), two exact
spaced-material scoping checks (`q_exact_spaced_nicu30`, `q_exact_spaced_cuni30`), and one
broad family query (`q_family_nicu_temperature_not_material`). `--store` persists per-question
metrics into the runtime DuckDB ledger's `eval_results` table (`GET /eval/summary` then serves
the stored run instead of a live baseline).

CI runs the same backend (`uv sync --group dev`, `ruff`, `mypy`, `pytest`,
`uv run python scripts/run_eval.py`) and frontend (`npm ci`, `typecheck`, `build`) checks; the
backend job does not pass `--extra ingest`, so `docling`/`fastembed`/`gliner`/
`sentence-transformers`/`trafilatura` are not installed in CI (the 3 skips above are expected
there).

## Contracts And Data

Non-negotiable demo gates remain `unsupported_claim_count = 0` and
`source_label_leak_count = 0`; `run_eval.py` raises `SystemExit(1)` if any `EVAL_QUESTIONS` case
fails its assertions (missing/extra experiments or evidence, wrong material set, leaked
forbidden materials, unexpected gap state, missing follow-up suggestions, or any unsupported
claim / label leak).

Additional coverage protects free-text material precision (unchanged from W0): unknown explicit
material tokens `Ni-20`/`ni 20`/`Ni–20` return no experiments/evidence and suggest nearby known
materials; exact `Ni-30Cu`/`Ni 30 Cu`/`Cu Ni 30`/`CuNi30` queries stay scoped to their exact
ledger material; the family query `Ni-Cu 700 C 8 ч` stays broad.

`tests/integration/test_synthetic_v2_corpus.py` adds: `test_manifest_matches_committed_files`
(manifest.json vs. directory listing), `test_csv_and_markdown_corpus_ingests_offline` (offline
ingestion, conflict, and alias assertions against the v2 corpus), and the docling/trafilatura-
gated tests described above.

`tests/unit/test_llm_gateway.py` still covers `build_llm()`/`FakeLLM`/`LiteLLMGateway` behavior
and the repo-wide `litellm`-import guard, unchanged from W0.

## Invariants

- Do not mark a demo answer successful if unsupported final sentences exist.
- Do not mark a security run successful if restricted evidence enters the context packet.
- Whenever `scripts/run_eval.py`'s `EVAL_QUESTIONS` changes, keep the question count and this
  memory's description in sync in the same change; do not resurrect `eval/*.yml` as a second
  source of truth without wiring it into code first.

## Change Rules

When new ingestion/retrieval/extraction behavior is added, extend `EVAL_QUESTIONS` in
`scripts/run_eval.py` and the relevant `tests/unit/` or `tests/integration/` module in the same
change.

## Verification

- `make ci`: ruff, mypy, pytest (89 passed, 3 skipped at `f4bf404`), frontend typecheck, build.
- `make eval`: `scripts/run_eval.py` — 12-question live QA metrics against the DuckDB ledger.
- `docker compose config`: Compose validation.
- Secret scan: repository-wide `rg` pattern scan excludes lockfiles/runtime dirs.
