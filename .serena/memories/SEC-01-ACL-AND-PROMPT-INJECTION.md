<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 55e8e19 docs: integrate evidence-led mvp review
Scope: .serena/newproj/nornikel-kg-search/09_SECURITY.md; .serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md
Area: SEC
-->

# SEC-01-ACL-AND-PROMPT-INJECTION

## Purpose

Capture safety boundaries for internal-document retrieval and LLM answer generation.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/09_SECURITY.md`: security model, ACL sequence, and prompt-injection checks.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: hard ACL and answer-verification gates.

## Entry Points

- Future `src/nornikel_kg/ports/acl_policy.py`: authorization policy boundary.
- Future `src/nornikel_kg/pipelines/security_checks.py`: adversarial fixture checks.
- Future `src/nornikel_kg/services/qa_service.py`: context construction and post-retrieval recheck.

## Current Behavior

The repository has no running app yet. The P0 security design requires ACL filtering before retrieved evidence enters an LLM context and requires post-retrieval rechecks against DuckDB.

## Contracts And Data

Retrieval sequence: resolve user/groups/clearance, resolve allowed source/span IDs in DuckDB, query Qdrant with mandatory ACL payload filters, rejoin to DuckDB, drop disallowed candidates, build LLM context only from allowed evidence, traverse only allowed evidence-backed graph edges, and verify all cited spans before returning the answer.

Prompt-like source content is untrusted evidence. It should be flagged during ingestion and wrapped as untrusted context, not followed as instructions.

## Invariants

- Never retrieve unauthorized chunks into LLM context and filter only after generation.
- Never send restricted docs to external LLM or embedding providers unless explicitly approved.
- Streamlit cache must not leak results across demo users.
- Security fixtures must pass with `acl_leak_count = 0` and `prompt_injection_success_count = 0`.

## Change Rules

When adding retrieval, graph expansion, or answer assembly, add ACL tests in the same change.

## Verification

- Future `make eval`: must include ACL and prompt-injection fixture results.
- Future `tests/unit/test_acl_filters.py`: must prove Qdrant candidates are rechecked against DuckDB before context construction.

