<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: README.md; .serena/newproj/nornikel-kg-search/; .serena/plans/; .serena/reviews/;
  .env.example; docs/deployment/
Area: DOCS
-->

# DOCS-01-PLANNING-SOURCE

## Purpose

Capture how to use and maintain the planning package given the current implementation state.

## Source Of Truth

- `.serena/newproj/nornikel-kg-search/`: original planning package; superseded on conflict by
  `.serena/plans/`.
- `.serena/plans/00_PLAN_INDEX.md` / `01_MVP_SCOPE_AND_DECISIONS.md` / `03_IMPLEMENTATION_PLAN.md`:
  the W0-W5 implementation plan, fully realized.
- `.serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md`: deployment/observability plan, realized by
  `docs/deployment/nornikel-nddev.md`.
- `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md`: full-track requirement brief («Научный
  клубок») and gap analysis G1-G10 against the real `DATA_HACK/` corpus (revised waves W6-W8);
  wave 6.3 (ontology extension) is now substantially, though not fully, implemented
  (`mem:DATA-01-EVIDENCE-LEDGER`, `mem:TECHDEBT-01-NOW` — geomechanics coverage remains open).
- `.serena/reviews/`: plan self-critique and source-backed research facts.
- `README.md`: current implementation status.
- `docs/deployment/nornikel-nddev.md`: primary live-stand deployment doc.
- `AGENTS.md` / `.claude/CLAUDE.md`: Codex-native and Claude Code project instructions.

## Entry Points

- `README.md`: start here for status and document map.
- `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md`: current wave plan (G1-G10, W6-W8).

## Current Behavior

Waves W0-W5 (2026-07-02 plan package) are implemented and merged to `main`. A subsequent
real-corpus hardening wave landed as a single squashed/rewritten commit `58760b3` ("feat:
real-corpus vertical — ingest hardening, metallurgy ontology, scoped QA filters"), whose commit
message explicitly records that it "rewrites history to drop 4.2GB of DATA_HACK blobs
accidentally staged before the .gitignore entry landed." **The previously recorded commits
`86abb1f`/`f62f17c` no longer exist in this repository's history** (verified: `git cat-file -t
86abb1f` -> "Not a valid object name") — any earlier memory or document referencing them as
current history is stale; `58760b3` is the commit that carries that functionality forward now.

Follow-on commits after `58760b3` on `main`: `0dfeba3` (geography/year scope filters in the
workbench UI), `ed69686` (nginx `client_max_body_size` 6m -> 32m), `074531e` (source
re-enrichment endpoint), `23a220a` (`LLM_EXTRACTION_ENABLED` gate, default `false`), `4f482d0`
(batched `POST /sources/reindex-all`), `42d5742` (alias-index caching perf fix), `f40ab72`
(persistent DuckDB connection perf fix), `41ee7ac` (co-occurrence edge cap on dense spans). See
`mem:CORE-01-INDEX` and `mem:TECHDEBT-01-NOW` for what each of these changed.

Local `main` and `origin/main` are in sync (`git rev-list --left-right --count
origin/main...main` -> `0\t0`, verified 2026-07-03); there is no pending push backlog.

`.env.example` still documents the open-weight LLM env matrix from W0 (`LLM_ENABLED`,
`DATAEYES_API_BASE`/`DATAEYES_API_KEY`, `LLM_EXTRACTION_MODEL`/`LLM_ANSWER_MODEL`,
`EMBEDDING_BACKEND`, `EMBEDDING_MODEL_ID`, `SPARSE_MODEL_ID`, `HF_HOME`, `LANGFUSE_*`,
`OLLAMA_BASE_URL`, `MAX_SOURCE_UPLOAD_BYTES`); it does not yet document `LLM_EXTRACTION_ENABLED`
or `SYNC_ENRICHMENT`, both of which are read directly from `os.getenv` in
`src/nornikel_kg/services/runtime.py`/`ingestion_service.py` with code-level defaults.

## Contracts And Data

Repository artifacts are written in English. User-facing conversation remains Russian unless
the owner requests otherwise.

## Invariants

- Synthetic fixtures should be committed; real internal corpora (`DATA_HACK/`, `data/corpus/`)
  must never be committed — they are gitignored, and `58760b3` is a documented example of the
  cost of an accidental staging mistake (a 4.2GB history rewrite).
- Planning docs under `.serena/plans/`/`.serena/newproj/` describe design intent at the time
  they were written; cross-check `README.md` and `.serena/memories/` for current implementation
  state, and cross-check `git cat-file -t <sha>` before trusting any commit SHA recorded in an
  older memory or plan document — history has been rewritten at least once (`58760b3`).

## Change Rules

Keep planning updates source-backed when they mention external tools or current capabilities.
Update `README.md`'s implemented-scope section when a new wave lands.

## Verification

- Targeted `rg`/`grep` scans: consistency and accidental secret markers.
- `git cat-file -t <sha>`: verify a commit SHA still exists before citing it in a new memory.
- `git rev-list --left-right --count origin/main...main`: verify local/remote sync state.
