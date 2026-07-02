<!-- Memory Metadata
Last updated: 2026-07-03
Last commit: ece33d3 docs(plans): record completed dataeyes discovery and configured dev model
Scope: Makefile; .github/workflows/ci.yml; docker-compose.yml; docs/deployment/nornikel-nddev.md; pyproject.toml; services/api/Dockerfile; apps/web/nginx.conf; .env.example; apps/web/; services/api/; .serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md
Area: RELEASE
-->

# RELEASE-01-VALIDATION

## Purpose

Capture the current validation and rollout contract after waves W0-W5.

## Source Of Truth

- `Makefile`: local quality-gate commands, now including `reindex` and `warmup` targets.
- `.github/workflows/ci.yml`: pull-request and `main` CI checks.
- `docker-compose.yml`: local/server container topology (`api`, `web`, `qdrant`).
- `services/api/Dockerfile`: uv-based API image build; W1 added system libraries for Docling.
- `apps/web/nginx.conf`: bundled web proxy config.
- `docs/deployment/nornikel-nddev.md`: W5 primary live-stand deployment contract (supersedes
  the earlier `fa.nddev.asia`-only notes as the primary reference; `fa.nddev.asia` remains an
  interim mirror per `README.md`).
- `README.md`: quick start, demo scenario, and W0-W5 implemented-scope summary.

## Entry Points

- `make ci`: backend and frontend quality gate.
- `make eval`: `scripts/run_eval.py` (12 questions).
- `make reindex`: `uv run python scripts/reindex.py` — rebuilds Qdrant collections from DuckDB.
- `make warmup`: `uv run python scripts/warmup.py` — pre-loads embedding/parser models.
- `docker compose config` / `docker compose up --build`: Compose validation and containerized
  run path.

## Current Behavior

CI has separate backend and frontend jobs; backend runs `uv sync --group dev`,
`uv run ruff check .`, `uv run mypy`, `uv run pytest`, and `uv run python scripts/run_eval.py`.
At `ece33d3`, `uv run pytest` passes **90 tests, 3 skipped** and ruff/mypy report no issues. The
backend CI job still does not pass `--extra ingest`, so `docling`, `fastembed`, `gliner`,
`sentence-transformers`, and `trafilatura` are not installed in CI; the 3 skipped tests are the
`importorskip`-guarded Docling/trafilatura cases in
`tests/integration/test_synthetic_v2_corpus.py` (see `mem:TEST-01-EVALUATION-GATES`).

`services/api/Dockerfile` (W1) installs `libgl1`, `libglib2.0-0`, `libxcb1`, `libxext6`,
`libsm6` as system packages (Docling's PDF-rendering dependencies) and copies `scripts/` into
the image, in addition to the W0 uv-based build (`uv sync --frozen --no-dev --extra ingest`
under a BuildKit cache mount).

`apps/web/nginx.conf` sets `client_max_body_size 6m` **and** `proxy_read_timeout 300s` for the
`/api/` location block (W1) — the longer read timeout accommodates slow Docling PDF parsing and
first-request embedding-model loads behind the proxy.

Docker Compose defines `api`, `web`, `qdrant`, unchanged topology from W0; `qdrant` is now
actively used by `RetrievalService` when `EMBEDDING_BACKEND` is `local` or `fake`.

## Contracts And Data

The web container serves the Vite build through Nginx and proxies `/api/` to the FastAPI
container with `client_max_body_size 6m` and `proxy_read_timeout 300s`. `VITE_API_BASE_URL`
defaults to `/api` for container deployment.

The API container sets `PROJECT_ROOT=/app`; `src/nornikel_kg/services/runtime.py` resolves
`data/`, `sample_docs/`, and `data/artifacts` (via `ARTIFACT_ROOT`) relative to that root.

`docs/deployment/nornikel-nddev.md` documents the primary stand: `ssh curestry`
(`165.22.203.232`, 8 vCPU / 31 GiB), TLS terminated by the host-wide `curestry-nginx-1`
(nginx-proxy + acme-companion), `api`/`qdrant` internal-only while `api` also joins the external
`lf-net` network to reach the co-located `/srv/langfuse` self-hosted Langfuse v3 stack, and
`/root/backup-nornikel.sh` running nightly via cron (03:30) to back up the DuckDB ledger.

`pyproject.toml` mypy overrides for `litellm`/`langfuse` are unchanged from W0.

## Invariants

- Do not commit `.env`, browser artifacts, `.playwright-cli/`, `.venv/`, node_modules, or DuckDB
  runtime files.
- Do not replace `npm ci` in CI/Docker with non-lockfile installs.
- Compose must remain valid without local secrets.
- Keep `MAX_SOURCE_UPLOAD_BYTES` (wherever configured) at or below the active Nginx
  `client_max_body_size`.
- Keep `apps/web/nginx.conf`'s `proxy_read_timeout` long enough for cold Docling/embedding-model
  loads; do not shorten it without confirming the current model warm-up latency.

## Change Rules

When changing CI, verify referenced GitHub Action major tags exist. When changing frontend
dependencies, update `apps/web/package-lock.json` and run the frontend build. When changing API
dependencies, update `uv.lock` and run backend tests. When changing `MAX_SOURCE_UPLOAD_BYTES` or
Docling/embedding cold-start behavior, also check `apps/web/nginx.conf` and any host-level
reverse proxy limit/timeout.

## Verification

- `make ci`: proves Python lint/type/tests and TypeScript/build (90 backend tests pass, 3
  skipped, at `ece33d3`).
- `make eval`: proves the 12-question live fixture answer/safety metrics.
- `docker compose config`: proves Compose syntax.
- Server smoke (per `docs/deployment/nornikel-nddev.md`): the live stand at
  `https://nornikel.nddev.asia` runs the full stack; Docling PDF/DOCX ingest verified live;
  Qdrant reindexed; eval runs stored.
- LLM mode: `.serena/plans/06_DEPLOYMENT_AND_OBSERVABILITY.md` "Discovery Results (2026-07-03,
  working key — COMPLETE)" records a working `dataeyes.ai` key against
  `https://platform.dataeyes.ai/v1` (180-model catalog) and an owner decision to configure
  `LLM_ENABLED=true` on the stand since 2026-07-03 with `openai/gpt-5.4-mini` for extraction and
  answers (dev-only; not committed to `.env.example`, which still defaults `LLM_ENABLED=false`
  with blank `LLM_EXTRACTION_MODEL`/`LLM_ANSWER_MODEL`). Browser validation
  (gitignored artifacts under `browser/llm-answer-*.png`, `browser/mobile-answer.png`) confirms
  the workbench renders an LLM-composed answer summary citing `span_id`s, the force-graph with
  its entity-type legend, the gaps matrix, and a decisions timeline (2 events, both without a
  parsed date — see `mem:TECHDEBT-01-NOW`); `browser/llm-answer-zone.png` also shows the
  `v2_scan_no_text_layer.pdf` source tagged `карантин` (quarantine) in the artifact bank. The
  proprietary dev model (`openai/gpt-5.4-mini`) must be swapped for a verified open-weight
  catalog model (`deepseek-v3.2-251201` per the same discovery) before the submission freeze —
  see `mem:TECHDEBT-01-NOW`.
