<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 5acab4a docs: lock implementation decisions
Scope: .serena/newproj/nornikel-kg-search/10_TESTING.md; .serena/newproj/nornikel-kg-search/13_DELIVERY_PLAN.md; .serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md; .serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md
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

- Future `eval/gold_questions.yml`: curated success/conflict/gap/security questions.
- Future `eval/adversarial_questions.yml`: prompt-injection and source-label fixtures.
- Future `make test`: unit and integration checks.
- Future `make eval`: gold and adversarial evaluation.

## Current Behavior

No code scaffold or test runner exists yet. Current verification is document-level: whitespace check, architecture consistency scans, and secret-pattern scans over touched docs.

## Contracts And Data

P0 gold questions must include one polished ideal scenario plus direct material-regime-property questions, comparison questions, provenance questions, contradiction questions, gap questions, negative controls, source-label controls, and prompt-injection controls.

Non-negotiable demo gates are `unsupported_claim_count = 0` and `source_label_leak_count = 0`.

## Invariants

- Do not mark a demo answer successful if unsupported final sentences exist.
- Do not mark a security run successful if restricted evidence enters the context packet.
- Gold questions must list expected evidence span IDs after fixture ingestion.

## Change Rules

When scaffold code is added, add `make test`, `make eval`, and `make demo` targets early rather than after the UI is complete.

## Verification

- Current docs gate: `git diff --check`.
- Current consistency gate: targeted `rg` scans over `README.md` and `.serena/newproj/nornikel-kg-search/`.
- Future P0 gate: `make eval` must expose EvidenceRecall@10, TableRowRecall@10, citation coverage, unsupported claim count, source-label leak count, restricted source in context, and prompt-injection success count.
