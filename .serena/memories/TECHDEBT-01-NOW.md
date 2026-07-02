<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 86abb1f Merge fix/real-corpus-ingest: real-corpus ingest hardening
Scope: src/nornikel_kg/; apps/web/; services/api/; pyproject.toml; docker-compose.yml; .env.example; .github/workflows/ci.yml; tests/; .serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md; .serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md
Area: TECHDEBT
-->

# TECHDEBT-01-NOW

## Purpose

Capture verified current gaps after waves W0-W5, without using memory as a backlog.

## Source Of Truth

- `src/nornikel_kg/services/entity_resolution.py`: `EntityResolutionService` docstring documents
  an unimplemented embedding-fallback stage.
- `services/api/routes/graph.py`: `GET /graph/timeline` reads only `decision`/`conclusion`
  entities with a `metadata.date` field.
- `.github/workflows/ci.yml`: backend job still does not pass `--extra ingest`.
- `.env.example`: `LLM_EXTRACTION_MODEL`/`LLM_ANSWER_MODEL` still blank.
- `eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml`:
  orphaned fixtures (see `mem:TEST-01-EVALUATION-GATES`).

## Resolved Since W0 (verified, do not re-list as gaps)

- Docling PDF/DOCX ingestion is wired (`src/nornikel_kg/adapters/docling/parser.py`,
  `src/nornikel_kg/services/ingestion_service.py`).
- Qdrant hybrid retrieval is wired (`src/nornikel_kg/adapters/qdrant_index/index.py`,
  `src/nornikel_kg/services/retrieval_service.py`), gated by `EMBEDDING_BACKEND` (default
  `off`).
- The LLM gateway is wired into extraction (`ExtractionService._llm_mentions`) and answer
  synthesis (`LLMAnswerComposer.compose`), both gated by `LLMSettings.llm_enabled`
  (`LLM_ENABLED`, default `false`).
- `resolve_alias()`-equivalent mention resolution is wired into ingestion via
  `ExtractionService`/`EntityResolutionService`.
- Uploaded Markdown/text sources now also go through the extraction pipeline (entities/relations
  are derived), though CSV remains the only source of numeric measurements.
- `docs/deployment/fa-nddev.md` drift is superseded: `docs/deployment/nornikel-nddev.md` is now
  the current primary deployment doc (W5); `fa.nddev.asia` is documented as an interim mirror in
  `README.md`.
- `MAX_SOURCE_UPLOAD_BYTES`/Nginx-limit mismatch: `apps/web/nginx.conf` sets
  `client_max_body_size 6m`, matching the FastAPI code default `5242880` bytes; no known
  mismatch remains at HEAD (verify against `.env.example` before deploying with a larger sample
  value).
- **`dataeyes.ai` key blocked**: resolved. `.serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md`
  "Discovery Results (2026-07-03, working key — COMPLETE)" confirms a working key against
  `https://platform.dataeyes.ai/v1` (180-model catalog) and RU guided-JSON smoke results across
  `gpt-5.4-mini`, `deepseek-v3.2-251201`, `qwen3.5-27b`, `glm-4.7`, `Moonshot-Kimi-K2-Instruct`.
  Because providers do not reliably enforce `json_schema`, `src/nornikel_kg/adapters/llm/
  gateway.py` gained `_strictify()` (adds `additionalProperties: false` recursively before every
  `generate_json` call, tested by
  `tests/unit/test_llm_gateway.py::test_strictify_adds_additional_properties`) and
  `answer_composer.py`/`extraction_service.py` now spell the required JSON shape out inline in
  the prompt text, with one reminder-regeneration attempt on a `ValidationError` before the
  deterministic fallback (see `mem:ARCH-01-EVIDENCE-MVP`). This closes the previously-recorded
  "LLM key blocked" gap; see the new proprietary-model gap below for what remains open.
- **Real-corpus LLM extraction/ingestion hardening**: resolved via `86abb1f` (merge of
  `fix/real-corpus-ingest`, commit `f62f17c`). `ExtractionService.MAX_LLM_SPANS_PER_SOURCE = 12`
  caps LLM calls per source, `MAX_SPAN_CHARS = 1200` truncates span text before extraction, and
  only spans longer than 80 characters are LLM-eligible; `IngestionService._schedule_enrichment`
  runs extraction+indexing inline or on a daemon thread per
  `IngestionService.synchronous_enrichment` (`SYNC_ENRICHMENT` env, default `false`), so parsed-
  document ingest can return with run `status="running"`/`stage="extraction"` while enrichment
  finishes in the background. Motivated by a live test: a real 816KB Gipronikel DOCX (278
  evidence spans, gitignored `DATA_HACK/` corpus) previously blocked `/sources/upload` for over
  5 minutes behind the bundled web proxy's `proxy_read_timeout 300s`.

## Entry Points

- `EntityResolutionService.resolve_or_create`: exact key -> alias -> create; no embedding stage.
- `RetrievalService`: indexes a Qdrant `entities` collection (`_index_entities`) but nothing
  currently reads it back for resolution — only for `/entities/search`-adjacent retrieval, not
  for `EntityResolutionService`.
- `GET /graph/timeline` (`services/api/routes/graph.py`).
- `ExtractionService.mention_extractor` (GLiNER lazy import via
  `src/nornikel_kg/adapters/gliner_ner/extractor.py`).

## Current Behavior

The system is a working evidence-led product with real ingestion (Docling/trafilatura),
extraction (dictionary+GLiNER+LLM), retrieval (Qdrant hybrid), LLM-gated answer synthesis, graph
analytics (conflicts/gaps/timeline), and a 17-source synthetic corpus. Gates: `make ci` green —
90 passed, 3 skipped (docling/trafilatura optional-dependency skips); `ruff`/`mypy` strict
clean; `make eval` — 12 questions pass offline (deterministic path, `LLM_ENABLED=false` remains
the tracked `.env.example` default). Server:
`https://nornikel.nddev.asia` runs the full stack; Docling PDF/DOCX ingest verified live; Qdrant
reindexed (76+ units per the server run log); eval runs stored; Langfuse v3 runs at
`/srv/langfuse` (`lf-net`).

## Contracts And Data

The current demo answer must remain evidence-first regardless of which extraction/retrieval
paths are enabled: answer summary sentences cite spans, evidence cards expose `EvidenceSpan`
IDs, and graph paths connect material, experiment, regime, step, measurement, property,
evidence, and document.

## Invariants

- Keep the deterministic synthetic demo green while any LLM/retrieval path is toggled on or off.
- Do not let Qdrant become the authoritative evidence or entity store.
- Do not introduce LLM-generated claims without supporting span IDs.
- Only `src/nornikel_kg/adapters/llm/gateway.py` may import `litellm`.

## Change Rules

When closing a gap below, verify it against the working tree (not this memory) before removing
it, and move the corresponding "Resolved Since" bullet into the resolved list above in the same
change.

## Known Gaps

- **Stand model `openai/gpt-5.4-mini` — approved by organizers (gap resolved 2026-07-03)**:
  `.serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md` records that the organizers explicitly
  approved `gpt-5.4-mini` for this team (owner confirmation, 2026-07-03), so the earlier
  mandatory pre-freeze swap is withdrawn. `LLM_ENABLED=true` runs on the `nornikel.nddev.asia`
  stand with `LLM_EXTRACTION_MODEL=LLM_ANSWER_MODEL=openai/gpt-5.4-mini` (server `.env`, not
  committed; `.env.example` still defaults `LLM_ENABLED=false`). `deepseek-v3.2-251201`
  (7 s RU guided-JSON, clean JSON, HF weights) remains the documented one-line fallback if the
  approval changes.
- **LLM answer latency**: end-to-end `/qa/ask` latency in LLM mode was reported at roughly 32 s
  p50 during stand validation on 2026-07-03 (owner/session observation against the live stand;
  not reproducible from a committed fixture or test, since CI keeps `LLM_ENABLED=false` with
  deterministic fakes per `mem:TEST-01-EVALUATION-GATES`) — a smaller evidence packet or a
  faster catalog model is a candidate optimization before demo.
- **Timeline events without dates**: `GET /graph/timeline` only returns `decision`/`conclusion`
  entities whose `metadata` dict has a `date` key (`services/api/routes/graph.py`); browser
  validation of the live stand on 2026-07-03 (`browser/llm-answer-s2.png`, gitignored) shows the
  synthetic-v2 ledger already has 2 timeline events (one `decision`, one `conclusion`) but both
  render "без даты" (no date), so date extraction into `metadata.date` for these entity types is
  still an open gap, not just a theoretical empty-list case.
- **Entity-resolution embedding fallback not wired**: `EntityResolutionService`'s docstring
  documents a planned cosine->=0.90 embedding-fallback stage against a Qdrant `entities`
  collection, but `resolve_or_create` only implements exact-key and alias matching; the
  `entities` Qdrant collection is populated by `RetrievalService._index_entities` but nothing
  reads it back during resolution.
- **GLiNER model not pre-pulled in CI**: `.github/workflows/ci.yml`'s backend job does not
  install the `ingest` optional dependency group or pre-download `urchade/gliner_multi-v2.1`
  (or the Docling/embedding models); `GLINER_ENABLED` defaults to `true` at runtime, but CI's
  `pytest` run never exercises the real GLiNER path — `ExtractionService.mention_extractor`
  catches `ImportError` and falls back to dictionary-only rules in that environment.
- `eval/gold_questions.yml`, `eval/adversarial_questions.yml`, `eval/expected_spans.yml` are
  orphaned: no code path reads them; `scripts/run_eval.py` hardcodes its own 12-question list
  instead (see `mem:TEST-01-EVALUATION-GATES`). Either wire them back in or remove them in a
  future change — do not assume they run today.
- FastAPI tests still emit a Starlette deprecation warning that `fastapi.testclient` uses
  `httpx` and may need `httpx2` in a future dependency cycle (unchanged from W0).
- **GitHub push backlog (network outage)**: local `main` is at `86abb1f` (merge of
  `fix/real-corpus-ingest`) and ahead of `origin/main` by 2 commits (`f62f17c`, `86abb1f`;
  verified via `git rev-list --left-right --count origin/main...main` -> `0	2`) because GitHub
  pushes keep timing out (multiple retries observed on 2026-07-03), though `git ls-remote origin
  main` (read-only) still succeeds. The `fix/real-corpus-ingest` branch has been merged and
  deleted locally; the live stand already runs equivalent code (deployed earlier via `git
  archive`, independently verified: `/srv/nornikel-kg-search/src/nornikel_kg/services/
  extraction_service.py` has `MAX_LLM_SPANS_PER_SOURCE = 12`, no `.git` directory there). Push
  `main` to `origin/main` as soon as GitHub connectivity recovers; until then, `origin/main` is
  stale relative to the local/stand state.
- **Dictionary/ontology coverage does not extend to the real corpus domains**: the dictionaries
  under `src/nornikel_kg/resources/dictionaries/` only seed Ni-Cu/Cu-Ni/Ni-Cr-Mo alloys and their
  regimes/properties (see `mem:DATA-01-EVIDENCE-LEDGER`, `Contracts And Data`), so
  slag/matte pyrometallurgy, electrowinning, desalination, beneficiation, and geomechanics
  questions against the real `DATA_HACK/` corpus slot-parse to no entities (live finding,
  2026-07-03). Tracked as gap G1 in `.serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md`
  (dictionary/ontology extension plus new Publication/Expert/Facility entity types, planned for
  wave W6.3).
