<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: 41ee7ac perf: skip co-occurrence edges on dense catalog-like spans
Scope: Makefile; .github/workflows/ci.yml; docker-compose.yml; docs/deployment/nornikel-nddev.md;
  pyproject.toml; services/api/Dockerfile; apps/web/nginx.conf; .env.example; apps/web/;
  services/api/; scripts/ingest_corpus.py; .serena/plans/08_TRACK_FULL_REQUIREMENTS_AND_GAPS.md
Area: RELEASE
-->

# RELEASE-01-VALIDATION

## Purpose

Capture the current validation and rollout contract after the real-corpus hardening wave.

## Source Of Truth

- `Makefile`: local quality-gate commands (`ci`, `eval`, `reindex`, `warmup`).
- `.github/workflows/ci.yml`: pull-request and `main` CI checks.
- `docker-compose.yml`: local/server container topology (`api`, `web`, `qdrant`).
- `services/api/Dockerfile`: uv-based API image build with Docling system libraries.
- `apps/web/nginx.conf`: bundled web proxy config, `client_max_body_size 32m`.
- `docs/deployment/nornikel-nddev.md`: primary live-stand deployment contract.
- `README.md`: quick start, demo scenario, and implemented-scope summary.

## Entry Points

- `make ci`: backend and frontend quality gate.
- `make eval`: `scripts/run_eval.py` (12 questions against the synthetic corpus).
- `make reindex`: `uv run python scripts/reindex.py` — rebuilds Qdrant collections from DuckDB.
- `make warmup`: `uv run python scripts/warmup.py` — pre-loads embedding/parser models.
- `scripts/ingest_corpus.py --dir <path> [--limit N] [--max-mb N]`: batch-ingests a real corpus
  directory into the ledger from inside the `api` container (no HTTP hop per file); sets
  `IngestionService.synchronous_enrichment = True` for the run so every ingested file reaches a
  terminal `completed`/`quarantined` status before the script exits.
- `docker compose config` / `docker compose up --build`: Compose validation and containerized
  run path.

## Current Behavior

`uv run pytest` passes **96 tests, 3 skipped** at `41ee7ac` (verified by a live run in this sync
pass: progress output totals 99 test outcomes, 96 `.` and 3 `s`, zero failures). The 3 skips
remain the `pytest.importorskip("docling")`/`importorskip("trafilatura")` guards in
`tests/integration/test_synthetic_v2_corpus.py`. `ruff`/`mypy` were not re-run in this sync
pass; the last independently verified clean run was at `ece33d3` (see prior sync history) —
treat their current status as unverified until the next `make ci` run.

`apps/web/nginx.conf` sets `client_max_body_size 32m` (raised from `6m` at commit `ed69686`;
real corpus DOCX files exceeded the old limit and were rejected with HTTP 413 before reaching
the API) and keeps `proxy_read_timeout 300s` for `/api/`.

`services/api/routes/sources.py` now also exposes `POST /sources/{source_id}/enrich`
(`IngestionService.enrich_source`, re-runs extraction/indexing for an already-parsed source) and
`POST /sources/reindex-all` (spawns a background daemon thread running
`RetrievalService.reindex_all()`).

`src/nornikel_kg/services/runtime.py:get_extraction_service` reads `LLM_EXTRACTION_ENABLED`
(default `false`) to gate ingest-time LLM extraction independently of the QA answer composer's
`LLM_ENABLED`/`LLMSettings.llm_enabled`.

Docker Compose defines `api`, `web`, `qdrant`, unchanged topology; `services/api/Dockerfile`
still installs `libgl1`, `libglib2.0-0`, `libxcb1`, `libxext6`, `libsm6` for Docling.

## Contracts And Data

The web container serves the Vite build through Nginx and proxies `/api/` to the FastAPI
container with `client_max_body_size 32m` and `proxy_read_timeout 300s`. `VITE_API_BASE_URL`
defaults to `/api` for container deployment.

The API container sets `PROJECT_ROOT=/app`; `src/nornikel_kg/services/runtime.py` resolves
`data/`, `sample_docs/`, and `data/artifacts` (via `ARTIFACT_ROOT`) relative to that root.

`docs/deployment/nornikel-nddev.md` documents the primary stand: `ssh curestry`
(`165.22.203.232`, 8 vCPU / 31 GiB), TLS terminated by the host-wide `curestry-nginx-1`
(nginx-proxy + acme-companion), `api`/`qdrant` internal-only while `api` also joins the external
`lf-net` network to reach the co-located `/srv/langfuse` self-hosted Langfuse v3 stack.

`DuckDBLedgerRepository._connect()` (`src/nornikel_kg/adapters/duckdb/repositories.py`) now
holds one persistent DuckDB connection behind a class `RLock` (`f40ab72`); the API process holds
the DuckDB file lock for its lifetime, so container-level diagnostics (e.g. a `docker exec`
DuckDB CLI session against `data/catalog.duckdb`) cannot open the file directly while the `api`
service is running — use the API's own endpoints for diagnostics instead.

## Invariants

- Do not commit `.env`, browser artifacts, `.playwright-cli/`, `.venv/`, node_modules, or DuckDB
  runtime files. The gitignored `data/corpus`/`DATA_HACK/` directories must never be staged;
  commit `58760b3` was a history rewrite specifically to remove 4.2GB of such blobs that had been
  accidentally staged before the `.gitignore` entry landed — verify `git status`/`du` before
  large-file operations near corpus directories.
- Do not replace `npm ci` in CI/Docker with non-lockfile installs.
- Compose must remain valid without local secrets.
- Keep `MAX_SOURCE_UPLOAD_BYTES` (wherever configured) at or below the active Nginx
  `client_max_body_size` (currently `32m` in `apps/web/nginx.conf`).
- Keep `apps/web/nginx.conf`'s `proxy_read_timeout` long enough for cold Docling/embedding-model
  loads; do not shorten it without confirming the current model warm-up latency.
- Do not call `duckdb.connect(...)` outside `DuckDBLedgerRepository._connect()`.

## Change Rules

When changing CI, verify referenced GitHub Action major tags exist. When changing frontend
dependencies, update `apps/web/package-lock.json` and run the frontend build. When changing API
dependencies, update `uv.lock` and run backend tests. When changing `MAX_SOURCE_UPLOAD_BYTES` or
the Nginx body-size limit, keep both the FastAPI code default and `apps/web/nginx.conf`'s
`client_max_body_size` consistent, and check any host-level reverse proxy limit/timeout too.

## Verification

- `make ci`: proves Python lint/type/tests and TypeScript/build; `uv run pytest` verified at 96
  passed / 3 skipped at `41ee7ac` in this sync pass (ruff/mypy not re-verified this pass).
- `make eval`: proves the 12-question synthetic-fixture answer/safety metrics; does not exercise
  the real-corpus ontology/scope-filter behavior (see `mem:TECHDEBT-01-NOW`).
- `docker compose config`: proves Compose syntax.
- `git rev-list --left-right --count origin/main...main` -> `0\t0` (verified 2026-07-03): local
  `main` and `origin/main` are in sync; no pending push backlog.
