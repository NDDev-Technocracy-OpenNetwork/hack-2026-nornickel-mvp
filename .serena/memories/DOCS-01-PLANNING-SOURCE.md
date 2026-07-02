<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: f4bf404 Merge pull request #11 from rldyourmnd/feat/w5-corpus-eval-hardening
Scope: README.md; .serena/newproj/nornikel-kg-search/; .serena/plans/; .serena/reviews/; .env.example; docs/deployment/
Area: DOCS
-->

# DOCS-01-PLANNING-SOURCE

## Purpose

Capture how to use and maintain the planning package now that waves W0-W5 are implemented.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/`: original planning package (01_HLO through
  19_OWNER_DECISIONS); superseded on conflict by `.serena/plans/`.
- `.serena/plans/00_PLAN_INDEX.md`: entry point of the 2026-07-02 MVP implementation plan
  (waves W0-W5); `.serena/plans/01_MVP_SCOPE_AND_DECISIONS.md`: locked owner decisions and
  hackathon-rule deltas, takes precedence on conflict.
- `.serena/plans/03_IMPLEMENTATION_PLAN.md`: the wave-by-wave implementation plan that W1-W5
  now realize (Docling ingest, GLiNER+LLM extraction, Qdrant retrieval, own graph layer,
  gaps/conflicts, graph UI).
- `.serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md`: deployment/observability plan, realized
  by `docs/deployment/nornikel-nddev.md`.
- `.serena/reviews/01_PLAN_CRITICAL_REVIEW.md` and `.serena/reviews/02_RESEARCH_EVIDENCE_REGISTER.md`:
  plan self-critique and source-backed research facts.
- `README.md`: current implementation status; documents "Implemented beyond the P0 scaffold
  (waves W0-W5, 2026-07-02)" with the full feature list.
- `docs/deployment/nornikel-nddev.md`: W5 primary live-stand deployment doc.
- `AGENTS.md` / `.claude/CLAUDE.md`: Codex-native and Claude Code project instructions.

## Entry Points

- `README.md`: start here for status and document map.
- `.serena/plans/00_PLAN_INDEX.md`: the plan package that W1-W5 implemented; still useful as
  the wave-by-wave design record even though every wave has now landed.

## Current Behavior

All five waves (W0-W5) from the 2026-07-02 MVP plan package are implemented and merged to
`main`: `1bca77f` (W0, PR#6), `d27bf88` (W1 ingest, PR#7), `824e19a` (W2 extraction/graph,
PR#8), `b117459` (W3 retrieval/LLM QA, PR#9), `f9b0830` (W4 frontend/analytics, PR#10),
`f4bf404` (W5 corpus/hardening, PR#11). `README.md` documents this as "Implemented beyond the
P0 scaffold (waves W0-W5, 2026-07-02)" and lists: Docling PDF/DOCX ingest with quarantine for
scans, trafilatura URL import, GLiNER+dictionary+LLM extraction with entity resolution, an own
graph layer (DuckDB entities/relations + NetworkX neighborhoods), Qdrant hybrid retrieval
(USER-bge-m3 dense + BM25 sparse, RRF), LLM answer synthesis gated by the claim verifier, gap
and conflict analysis, a decisions timeline, answer-run persistence, and the committed
`sample_docs/synthetic_v2/` corpus (17 sources).

The plan package under `.serena/plans/` and `.serena/reviews/` remains as the historical design
record; it was not rewritten to say "implemented" post-hoc — `README.md` and the numbered
memories in `.serena/memories/` are the current-status source of truth, and `.serena/plans/`
should be read as "the plan that produced this state," not as a live status document.

`.env.example` still documents the open-weight LLM env matrix from W0
(`LLM_ENABLED`, `DATAEYES_API_BASE`/`DATAEYES_API_KEY`, `LLM_EXTRACTION_MODEL`/
`LLM_ANSWER_MODEL`, `EMBEDDING_BACKEND`, `EMBEDDING_MODEL_ID=deepvk/USER-bge-m3`,
`SPARSE_MODEL_ID=Qdrant/bm25`, `HF_HOME`, `LANGFUSE_*`, `OLLAMA_BASE_URL`,
`MAX_SOURCE_UPLOAD_BYTES`); `LLM_ENABLED=false` remains the default and the CI/test invariant.

## Contracts And Data

Repository artifacts are written in English. User-facing conversation remains Russian unless
the owner requests otherwise. Upload runtime limit contract unchanged from W0:
`MAX_SOURCE_UPLOAD_BYTES` code default `5242880` bytes; bundled web Nginx now also sets
`proxy_read_timeout 300s` for `/api/` (W1, see `mem:RELEASE-01-VALIDATION`).

## Invariants

- Synthetic fixtures should be committed; the W5 `sample_docs/synthetic_v2/` corpus (17 sources)
  is deterministically regenerable via `scripts/generate_synthetic_docs.py`. Real internal
  corpora may be committed only when owner-provided/approved for this private repository.
  Generated artifact memory bank files, local Qdrant storage, DuckDB runtime databases, caches,
  and secrets must not be committed.
- Planning docs under `.serena/plans/`/`.serena/newproj/` describe design intent at the time
  they were written; do not treat them as a live status report — cross-check `README.md` and
  `.serena/memories/` for current implementation state.
- If a planning document conflicts with `.serena/plans/03_IMPLEMENTATION_PLAN.md`, the
  as-implemented code (verified via this memory set) is authoritative.

## Change Rules

Keep planning updates source-backed when they mention external tools or current capabilities.
Update `README.md`'s "Implemented beyond the P0 scaffold" section when a new wave lands.

## Verification

- `git diff --check`: formatting.
- Targeted `rg` scans: consistency and accidental secret markers.
- `README.md` wave-list cross-check against `git log --oneline` merge commits for
  `d27bf88`/`824e19a`/`b117459`/`f9b0830`/`f4bf404`.
