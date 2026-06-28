<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 5acab4a docs: lock implementation decisions
Scope: README.md; .serena/newproj/nornikel-kg-search/
Area: CORE
-->

# CORE-01-INDEX

## Purpose

Index the durable project knowledge for the Nornikel Materials KG Search hackathon MVP.

## Source Of Truth

- `README.md`: repository overview, current planning status, GitHub/private repo context.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: primary scaffold contract for P0 implementation.
- `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`: closed owner decisions for implementation, deployment, data, LLM, security, and UX.
- `.serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md`: product loop and MVP module boundaries.
- `.serena/newproj/nornikel-kg-search/11_PROJECT_STRUCTURE.md`: planned scaffold layout after owner approval.

## Entry Points

- `mem:ARCH-01-EVIDENCE-MVP`: architecture, module boundaries, and stack decisions.
- `mem:DATA-01-EVIDENCE-LEDGER`: evidence IDs, DuckDB ledger, tables, graph, and answer claims.
- `mem:SEC-01-ACL-AND-PROMPT-INJECTION`: source-label filtering, prompt-injection, and internal-document safety invariants.
- `mem:TEST-01-EVALUATION-GATES`: required checks, metrics, and acceptance gates.
- `mem:DOCS-01-PLANNING-SOURCE`: planning-doc ownership and current scaffold status.

## Current Behavior

The repository is docs/planning only, but owner approval for scaffold/code implementation is now recorded. Future implementation should start from `main` in logical branches.

## Contracts And Data

P0 product contract is: React/Vite workbench -> FastAPI API -> artifact memory bank -> stable EvidenceSpans -> table/fact extraction -> DuckDB evidence ledger -> Qdrant candidate retrieval -> NetworkX graph path -> deterministic evidence packet -> LiteLLM summary with claim verification -> evaluation/security dashboard -> server deployment on `fa.nddev.asia`.

## Invariants

- Do not treat Markdown chunks as source of truth; they are convenience views only.
- Every answer sentence must map to exact evidence IDs.
- DuckDB is authoritative for P0 facts and provenance.
- Qdrant is retrieval-only.
- NetworkX is graph materialization-only.
- React/Vite and FastAPI are P0, not P1.

## Change Rules

Update this index whenever a new durable memory is added, renamed, split, or deleted.

## Verification

- `git diff --check`: verifies staged docs have no whitespace errors.
- Targeted `rg` consistency scans over `README.md` and `.serena/newproj/nornikel-kg-search/`: verify old conflicting stack statements do not remain.
