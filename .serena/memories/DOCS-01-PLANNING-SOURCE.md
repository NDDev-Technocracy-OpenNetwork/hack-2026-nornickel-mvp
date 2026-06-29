<!-- Memory Metadata
Last updated: 2026-06-28
Last updated: 2026-06-29
Last commit: 1b0c3f4 fix: align upload limits with proxy validation
Scope: README.md; .serena/newproj/nornikel-kg-search/
Area: DOCS
-->

# DOCS-01-PLANNING-SOURCE

## Purpose

Capture how to use and maintain the planning package before implementation scaffolding exists.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/01_RESEARCH_SUMMARY.md`: source-backed research summary.
- `.serena/newproj/nornikel-kg-search/02_REQUIREMENTS.md`: product requirements.
- `.serena/newproj/nornikel-kg-search/03_ARCHITECTURE.md`: broad system architecture.
- `.serena/newproj/nornikel-kg-search/04_ADRS.md`: decisions.
- `.serena/newproj/nornikel-kg-search/06_API.md`: API contracts.
- `.serena/newproj/nornikel-kg-search/07_DATA.md`: data model.
- `.serena/newproj/nornikel-kg-search/09_SECURITY.md`: security constraints.
- `.serena/newproj/nornikel-kg-search/10_TESTING.md`: evaluation plan.
- `.serena/newproj/nornikel-kg-search/17_GPT_55_PRO_REVIEW_PROMPT.md`: prompt for external model review.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: scaffold authority.
- `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`: closed owner decisions for implementation.
- `AGENTS.md`: Codex-native project instructions.
- `.claude/CLAUDE.md`: Claude Code project memory and operational notes.

## Entry Points

- `README.md`: start here for status and document map.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: use first before writing scaffold code.

## Current Behavior

The planning package now favors a server-first product MVP: React/Vite frontend, FastAPI backend, DuckDB, Qdrant, NetworkX, Docling, LiteLLM/OpenAI-compatible providers, artifact memory bank, stable EvidenceSpans, table-first extraction, claim verification, and evaluation/security dashboard.

## Contracts And Data

Repository artifacts are written in English. User-facing conversation remains Russian unless the owner requests otherwise.
Current instruction docs also record the `/sources/upload` runtime limit contract:
`MAX_SOURCE_UPLOAD_BYTES` defaults to 5242880 bytes, and bundled web Nginx uses
`client_max_body_size 6m`.

## Invariants

- Synthetic fixtures should be committed. Real internal corpora may be committed only when owner-provided/approved for this private repository. Generated artifact memory bank files, local Qdrant storage, DuckDB runtime databases, caches, and secrets must not be committed.
- Planning docs should not claim implemented behavior before scaffold code exists.
- If a planning document conflicts with `18_IMPLEMENTATION_SPEC.md`, P0 implementation follows `18_IMPLEMENTATION_SPEC.md`.

## Change Rules

Keep planning updates source-backed when they mention external tools or current capabilities. Update README when adding, removing, or reprioritizing core planning docs.

## Verification

- `git diff --check`: formatting.
- Targeted `rg` scans: consistency and accidental secret markers.
