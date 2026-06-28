<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 55e8e19 docs: integrate evidence-led mvp review
Scope: README.md; .serena/newproj/nornikel-kg-search/
Area: CORE
-->

# CORE-01-INDEX

## Purpose

Index the durable project knowledge for the Nornikel Materials KG Search hackathon MVP.

## Source Of Truth

- `README.md`: repository overview, current planning status, GitHub/private repo context.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: primary scaffold contract for P0 implementation.
- `.serena/newproj/nornikel-kg-search/16_MVP_BLUEPRINT.md`: product loop and MVP module boundaries.
- `.serena/newproj/nornikel-kg-search/11_PROJECT_STRUCTURE.md`: planned scaffold layout after owner approval.

## Entry Points

- `mem:ARCH-01-EVIDENCE-MVP`: architecture, module boundaries, and stack decisions.
- `mem:DATA-01-EVIDENCE-LEDGER`: evidence IDs, DuckDB ledger, tables, graph, and answer claims.
- `mem:SEC-01-ACL-AND-PROMPT-INJECTION`: retrieval ACL, prompt-injection, and internal-document safety invariants.
- `mem:TEST-01-EVALUATION-GATES`: required checks, metrics, and acceptance gates.
- `mem:DOCS-01-PLANNING-SOURCE`: planning-doc ownership and current scaffold status.

## Current Behavior

The repository is still docs/planning only. Implementation scaffolding has not been created. Code creation requires owner approval because the planning docs explicitly say no scaffold code should be created before approval.

## Contracts And Data

P0 product contract is: artifact memory bank -> stable EvidenceSpans -> table/fact extraction -> DuckDB evidence ledger -> Qdrant candidate retrieval -> NetworkX graph path -> deterministic evidence packet -> LLM summary with claim verification -> evaluation/security dashboard.

## Invariants

- Do not treat Markdown chunks as source of truth; they are convenience views only.
- Every answer sentence must map to exact evidence IDs.
- DuckDB is authoritative for P0 facts and provenance.
- Qdrant is retrieval-only.
- NetworkX is graph materialization-only.

## Change Rules

Update this index whenever a new durable memory is added, renamed, split, or deleted.

## Verification

- `git diff --check`: verifies staged docs have no whitespace errors.
- Targeted `rg` consistency scans over `README.md` and `.serena/newproj/nornikel-kg-search/`: verify old conflicting stack statements do not remain.

