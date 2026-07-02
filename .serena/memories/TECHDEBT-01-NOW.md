<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: f4bf404 Merge pull request #11 from rldyourmnd/feat/w5-corpus-eval-hardening
Scope: src/nornikel_kg/; apps/web/; services/api/; pyproject.toml; docker-compose.yml; .env.example; .github/workflows/ci.yml; tests/
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
89 passed, 3 skipped (docling/trafilatura optional-dependency skips); `ruff`/`mypy` strict
clean; `make eval` — 12 questions pass offline (deterministic path, `LLM_ENABLED=false`). Server:
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

- **LLM key blocked**: hackathon LLM rules forbid OpenAI/Anthropic; the intended provider is
  `dataeyes.ai` via LiteLLM, but `LLM_EXTRACTION_MODEL`/`LLM_ANSWER_MODEL` remain blank in
  `.env.example` and `LLM_ENABLED=false` is still the default at HEAD. Per hackathon delivery
  context, the server's own `.env` (not committed) currently configures an interim non-open-
  weight dev model (`openai/gpt-5.5-mini`) that must be replaced with a verified open-weight
  `dataeyes.ai` catalog model before the submission freeze; this interim server config is not
  reflected in this repository's tracked files and is not verifiable from the working tree.
- **Timeline empty until decision entities have dates**: `GET /graph/timeline` only returns
  `decision`/`conclusion` entities whose `metadata` dict has a `date` key
  (`services/api/routes/graph.py`); if extraction has not yet produced dated decision/conclusion
  entities for the active ledger, the endpoint returns an empty `events` list rather than an
  error — this is expected behavior, not a bug, but the timeline is only useful once such
  entities exist.
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
