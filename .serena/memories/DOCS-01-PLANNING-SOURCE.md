<!-- Memory Metadata
Last updated: 2026-07-02
Last commit: 1bca77f Merge pull request #6 from rldyourmnd/feat/w0-alignment-and-seams
Scope: README.md; .serena/newproj/nornikel-kg-search/; .serena/plans/; .serena/reviews/; .env.example
Area: DOCS
-->

# DOCS-01-PLANNING-SOURCE

## Purpose

Capture how to use and maintain the planning package before implementation scaffolding exists.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/01_HLO.md`: source-backed research summary (high-level overview).
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
- `.serena/plans/00_PLAN_INDEX.md`: entry point of the 2026-07-02 MVP implementation plan package (waves W0-W5).
- `.serena/plans/01_MVP_SCOPE_AND_DECISIONS.md`: locked owner decisions and hackathon-rule deltas; takes precedence over `19_OWNER_DECISIONS.md` and `18_IMPLEMENTATION_SPEC.md` on conflict.
- `.serena/reviews/01_PLAN_CRITICAL_REVIEW.md` and `.serena/reviews/02_RESEARCH_EVIDENCE_REGISTER.md`: plan self-critique and source-backed research facts (licenses, versions, provider availability).

## Entry Points

- `README.md`: start here for status and document map.
- `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`: use first before writing scaffold code.

## Current Behavior

The planning package now favors a server-first product MVP: React/Vite frontend, FastAPI backend, DuckDB, Qdrant, NetworkX, Docling, LiteLLM/OpenAI-compatible providers, artifact memory bank, stable EvidenceSpans, table-first extraction, claim verification, and evaluation/security dashboard.

A second package, `.serena/plans/` (00-07) plus `.serena/reviews/` (01-02), was added on
2026-07-02 after the organizers clarified track rules. It amends the original package:
OpenAI/Anthropic APIs are forbidden; only open-weight models usable from Russia are allowed
(provider dataeyes.ai through the LiteLLM SDK, optional Ollama fallback); resource economy is
a judged criterion; the system must auto-form new links on KB growth. The plan defines waves
W0-W5 to the ~2026-07-16 deadline (Docling text-layer ingest, GLiNER+LLM extraction with
entity resolution, Qdrant hybrid retrieval, own graph layer in DuckDB+NetworkX, gaps/conflicts,
graph UI, x10 synthetic corpus, Langfuse self-host observability, new-server rollout).

Wave W0 (commits `d5e61fa`, `12b8cd6`, `e98c2e2`, `432044a`; merged as `1bca77f`, PR #6) closed
several planning-to-code gaps: `.env.example` now carries the full open-weight LLM/embedding/
Langfuse env matrix; `19_OWNER_DECISIONS.md`, `05_TECH_STACK.md`, and `08_INFRA.md` each carry a
dated 2026-07-02 amendment note superseding the earlier `openai/gpt-5.5-mini` /
`openai/text-embedding-3-large` defaults; and `README.md` documents the hackathon LLM rules plus
the new live stand `https://nornikel.nddev.asia` (`https://fa.nddev.asia` kept as an interim
mirror). `docs/deployment/fa-nddev.md` was not updated in this wave and still references the
withdrawn `OPENAI_API_KEY`/`LITELLM_API_BASE` env names (see `mem:TECHDEBT-01-NOW`).

## Contracts And Data

Repository artifacts are written in English. User-facing conversation remains Russian unless the owner requests otherwise.
Current instruction docs also record the `/sources/upload` runtime limit contract:
`MAX_SOURCE_UPLOAD_BYTES` code default is `5242880` bytes (`services/api/routes/sources.py`),
while `.env.example` now samples `26214400`, and bundled web Nginx uses
`client_max_body_size 6m` (see `mem:TECHDEBT-01-NOW` for the resulting size-limit mismatch).

## Invariants

- Synthetic fixtures should be committed. Real internal corpora may be committed only when owner-provided/approved for this private repository. Generated artifact memory bank files, local Qdrant storage, DuckDB runtime databases, caches, and secrets must not be committed.
- Planning docs should not claim implemented behavior before scaffold code exists.
- If a planning document conflicts with `18_IMPLEMENTATION_SPEC.md`, P0 implementation follows `18_IMPLEMENTATION_SPEC.md`.

## Change Rules

Keep planning updates source-backed when they mention external tools or current capabilities. Update README when adding, removing, or reprioritizing core planning docs.

## Verification

- `git diff --check`: formatting.
- Targeted `rg` scans: consistency and accidental secret markers.
