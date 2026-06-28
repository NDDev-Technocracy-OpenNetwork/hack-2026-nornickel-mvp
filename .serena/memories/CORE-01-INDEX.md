<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 259ecc6 feat: add react evidence workbench
Scope: README.md; apps/web/; services/api/; src/nornikel_kg/; eval/; sample_docs/; tests/; docker-compose.yml; .github/workflows/ci.yml
Area: CORE
-->

# CORE-01-INDEX

## Purpose

Index the durable project knowledge for the Nornikel Materials KG Search hackathon MVP.

## Source Of Truth

- `README.md`: repository overview, quick start, demo scenario, architecture boundary, and current scaffold status.
- `apps/web/`: React/Vite analysis workbench.
- `services/api/`: FastAPI route layer.
- `src/nornikel_kg/`: backend domain, ports, adapters, and application services.
- `eval/`: gold/adversarial evaluation fixtures.
- `sample_docs/`: committed synthetic smoke-test corpus.
- `tests/`: unit and integration tests.
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

The repository contains a working P0 scaffold on the implementation branch: FastAPI API, React/Vite workbench, DuckDB-backed synthetic evidence ledger, deterministic evidence-backed QA response, fixtures/eval, CI workflow, and Docker Compose configuration.

## Contracts And Data

Current P0 flow is: React/Vite workbench -> FastAPI `/qa/ask` -> DuckDB-backed synthetic evidence ledger -> deterministic evidence packet -> answer claim verification -> experiment table, evidence cards, graph path, conflict, gap, and evaluation/security metrics. Qdrant, Docling, NetworkX, and LiteLLM are prepared as modular next adapters, not yet wired into the scaffold runtime.

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
- `make ci`: verifies backend ruff/mypy/pytest and frontend typecheck/build.
- `make eval`: verifies fixture QA metrics.
- `docker compose config`: verifies Compose syntax without requiring local secrets.
- Targeted `rg` consistency scans over `README.md` and `.serena/newproj/nornikel-kg-search/`: verify old conflicting stack statements do not remain.
