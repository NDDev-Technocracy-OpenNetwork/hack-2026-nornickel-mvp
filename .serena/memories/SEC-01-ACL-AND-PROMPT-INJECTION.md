<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 259ecc6 feat: add react evidence workbench
Scope: src/nornikel_kg/domain/security.py; src/nornikel_kg/domain/answer_claims.py; src/nornikel_kg/services/qa_service.py; tests/unit/test_source_label_policy.py; tests/unit/test_claim_verifier.py; eval/adversarial_questions.yml
Area: SEC
-->

# SEC-01-ACL-AND-PROMPT-INJECTION

## Purpose

Capture safety boundaries for source-label filtering, internal-document retrieval, external LLM use, and answer generation.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/09_SECURITY.md`: security model, source-label filtering sequence, and prompt-injection checks.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: hard source-label and answer-verification gates.
- `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`: owner decisions on open demo access, external APIs, and logging.

## Entry Points

- `src/nornikel_kg/domain/security.py`: `SourceLabelPolicy` allow-list filtering for evidence spans.
- `src/nornikel_kg/domain/answer_claims.py`: `ClaimVerifier` citation coverage and source-label leak counting.
- `src/nornikel_kg/services/qa_service.py`: filters evidence before answer assembly and verifies final claims.
- `eval/adversarial_questions.yml`: current adversarial fixture expectations.

## Current Behavior

P0 has no user auth/RBAC. The implemented scaffold applies source-label filtering before answer assembly and verifies that each answer sentence references allowed evidence spans. The current synthetic fixture includes a prompt-injection-like line in the source Markdown; it is not used as an instruction and `prompt_injection_success_count` remains zero in eval.

## Contracts And Data

Implemented sequence: load evidence packet from DuckDB/fallback, filter spans with `SourceLabelPolicy`, assemble answer only from allowed spans, and run `ClaimVerifier` before returning. Planned retrieval sequence still requires DuckDB allowed-source resolution before Qdrant candidate retrieval and post-retrieval recheck.

Prompt-like source content is untrusted evidence. It should be flagged during ingestion and wrapped as untrusted context, not followed as instructions.

## Invariants

- Never retrieve unauthorized chunks into LLM context and filter only after generation.
- External LLM and embedding APIs are approved through LiteLLM/OpenAI-compatible providers, but secrets must never be committed or logged.
- Runtime logs may include snippets during the hackathon, but never credentials.
- Security fixtures must pass with `source_label_leak_count = 0` and `prompt_injection_success_count = 0`.

## Change Rules

When adding retrieval, graph expansion, or answer assembly, add source-label filtering tests in the same change.

## Verification

- `make eval`: reports `source_label_leak_count = 0` and `prompt_injection_success_count = 0` for the current fixture.
- `tests/unit/test_source_label_policy.py`: verifies disallowed labels are filtered.
- `tests/unit/test_claim_verifier.py`: verifies unsupported claims and restricted evidence references are counted.
