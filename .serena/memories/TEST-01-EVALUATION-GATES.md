<!-- Memory Metadata
Last updated: 2026-06-29
Last commit: 6d5f606 docs: sync /qa ask filter contract in memories
Scope: Makefile; tests/; scripts/run_eval.py; eval/; .github/workflows/ci.yml
Area: TEST
-->

# TEST-01-EVALUATION-GATES

## Purpose

Capture required verification and acceptance gates for the MVP.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/10_TESTING.md`: metrics, thresholds, and test plan.
- `.serena/newproj/nornikel-kg-search/13_DELIVERY_PLAN.md`: implementation order and hard gates.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: P0 verification requirements.

## Entry Points

- `eval/gold_questions.yml`: curated success/conflict/gap questions for the synthetic fixture.
- `eval/adversarial_questions.yml`: prompt-injection and source-label fixture expectations.
- `tests/unit/`: ID stability, claim verifier, and source-label policy tests.
- `tests/integration/`: FastAPI and DuckDB ledger tests.
- `make ci`: local backend/frontend quality gate matching the current CI workflow.
- `make eval`: deterministic fixture evaluation smoke.

## Current Behavior

The scaffold has executable gates. `make ci` runs backend ruff/mypy/pytest and frontend TypeScript/build. `scripts/run_eval.py` uses the runtime QA service and synthetic DuckDB ledger to verify citation and safety metrics for the ideal question, missing-conductivity gap, and method-mismatch conflict. CI runs the same backend and frontend checks on pull requests and pushes to `main`.

## Contracts And Data

P0 gold questions must include one polished ideal scenario plus direct material-regime-property questions, comparison questions, provenance questions, contradiction questions, gap questions, negative controls, source-label controls, and prompt-injection controls.

Non-negotiable demo gates are `unsupported_claim_count = 0` and `source_label_leak_count = 0`.

Regression coverage includes source upload/evidence listing, thread-safe first repository build,
and preservation of seeded source facts when an overlapping CSV is uploaded.
Additional coverage added for `/qa/ask` filter parsing:
- scalar filter values are accepted (auto-coerced to single-element lists);
- unknown filter keys are rejected with 422 validation errors.

## Invariants

- Do not mark a demo answer successful if unsupported final sentences exist.
- Do not mark a security run successful if restricted evidence enters the context packet.
- Gold questions must list expected evidence span IDs after fixture ingestion.

## Change Rules

When new ingestion/retrieval behavior is added, extend `eval/gold_questions.yml`, tests, and `scripts/run_eval.py` in the same change.

## Verification

- `make ci`: ruff, mypy, pytest, frontend typecheck, frontend build.
- `make eval`: fixture QA metrics.
- `docker compose config`: Compose validation.
- Secret scan: `rg` command used in task excludes lockfiles/runtime dirs and checks for non-placeholder secrets.
- Browser validation: Playwright CLI desktop/mobile snapshots and screenshots under ignored `browser/`;
  latest local proof paths use the `browser/ledger-fixed-*` prefix.
