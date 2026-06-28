<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 5acab4a docs: lock implementation decisions
Scope: .serena/newproj/nornikel-kg-search/09_SECURITY.md; .serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md; .serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md
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

- Future `src/nornikel_kg/ports/acl_policy.py` or `security_label_policy.py`: source-label policy boundary.
- Future `src/nornikel_kg/pipelines/security_checks.py`: adversarial fixture checks.
- Future `src/nornikel_kg/services/qa_service.py`: context construction and post-retrieval recheck.

## Current Behavior

The repository has no running app yet. P0 has no user auth/RBAC. The P0 security design requires source-label filtering before retrieved evidence enters an LLM context and requires post-retrieval rechecks against DuckDB.

## Contracts And Data

Retrieval sequence: resolve active demo policy and allowed source-label set, resolve allowed source/span IDs in DuckDB, query Qdrant with mandatory source/security-label payload filters, rejoin to DuckDB, drop disallowed candidates, build LLM context only from allowed evidence, traverse only allowed evidence-backed graph edges, and verify all cited spans before returning the answer.

Prompt-like source content is untrusted evidence. It should be flagged during ingestion and wrapped as untrusted context, not followed as instructions.

## Invariants

- Never retrieve unauthorized chunks into LLM context and filter only after generation.
- External LLM and embedding APIs are approved through LiteLLM/OpenAI-compatible providers, but secrets must never be committed or logged.
- Runtime logs may include snippets during the hackathon, but never credentials.
- Security fixtures must pass with `source_label_leak_count = 0` and `prompt_injection_success_count = 0`.

## Change Rules

When adding retrieval, graph expansion, or answer assembly, add source-label filtering tests in the same change.

## Verification

- Future `make eval`: must include source-label and prompt-injection fixture results.
- Future `tests/unit/test_source_label_filters.py`: must prove Qdrant candidates are rechecked against DuckDB before context construction.
