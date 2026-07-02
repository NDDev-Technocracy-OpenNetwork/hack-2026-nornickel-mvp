<!-- Memory Metadata
Last updated: 2026-07-02
Last commit: 1bca77f Merge pull request #6 from rldyourmnd/feat/w0-alignment-and-seams
Scope: Makefile; .github/workflows/ci.yml; docker-compose.yml; docs/deployment/fa-nddev.md; pyproject.toml; services/api/Dockerfile; .env.example; apps/web/; services/api/
Area: RELEASE
-->

# RELEASE-01-VALIDATION

## Purpose

Capture the current validation and rollout contract for the server-first MVP scaffold.

## Source Of Truth

- `Makefile`: local quality-gate commands.
- `.github/workflows/ci.yml`: pull-request and `main` CI checks.
- `docker-compose.yml`: local/server container topology.
- `services/api/Dockerfile`: API container build (uv-based since wave W0).
- `.env.example`: local/server runtime env matrix including LLM/embedding/Langfuse keys.
- `docs/deployment/fa-nddev.md`: deployment notes for `fa.nddev.asia`; not updated in wave W0 (see `mem:TECHDEBT-01-NOW`).
- `README.md`: quick start and demo scenario; documents the new `https://nornikel.nddev.asia` live stand.

## Entry Points

- `make ci`: backend and frontend quality gate.
- `make eval`: deterministic fixture evaluation.
- `docker compose config`: Compose syntax validation without requiring `.env`.
- `docker compose up --build`: containerized API, web, and Qdrant run path.
- Playwright CLI session: validates React workbench query/upload flow and mobile layout with ignored
  `browser/ledger-fixed-*` artifacts.

## Current Behavior

CI has separate backend and frontend jobs. Backend runs `uv sync --group dev`,
`uv run ruff check .`, `uv run mypy`, `uv run pytest`, and `uv run python scripts/run_eval.py`.
Frontend runs `npm ci --no-audit`, `npm run typecheck`, and `npm run build`. At `1bca77f`,
`uv run pytest` passes 53 tests and `uv run ruff check .` / `uv run mypy` report no issues.
`scripts/run_eval.py` currently runs 9 fixture QA cases, including strict unknown material
no-result checks for `ni-20`, `ni 20`, and `Ni–20`, exact scoped material checks for spaced
known alloys, and the broad `Ni-Cu 700 C 8 ч` family query.

The backend CI job does not pass `--extra ingest`, so the `ingest` optional dependency group
(`docling`, `fastembed`, `gliner`, `sentence-transformers`, `trafilatura`) is not installed or
exercised by CI `pytest` runs; only the core LLM gateway (`litellm`, `langfuse`) and graph/
dictionary code paths are covered.

`services/api/Dockerfile` was reworked to build with `uv`: it copies `pyproject.toml`/`uv.lock`
first and runs `uv sync --frozen --no-install-project --no-dev --extra ingest` under a
`--mount=type=cache,target=/root/.cache/uv` BuildKit cache mount, then copies application code
(`README.md`, `src`, `services`, `eval`, `sample_docs`) and re-runs
`uv sync --frozen --no-dev --extra ingest` to install the project. The image sets
`HF_HOME=/app/data/hf-cache` and puts `/app/.venv/bin` on `PATH`; this replaces the earlier
`pip install .` build path.

Docker Compose defines `api`, `web`, and `qdrant`. The `.env` file is optional in Compose;
runtime secrets are expected to live outside git. `.env.example` documents the open-weight LLM
matrix (`LLM_ENABLED`, `DATAEYES_API_BASE`/`DATAEYES_API_KEY`, `LLM_EXTRACTION_MODEL`/
`LLM_ANSWER_MODEL`, `EMBEDDING_BACKEND=local` with `EMBEDDING_MODEL_ID=deepvk/USER-bge-m3` and
`SPARSE_MODEL_ID=Qdrant/bm25`, `HF_HOME`, `LANGFUSE_*`, `OLLAMA_BASE_URL`) plus
`MAX_SOURCE_UPLOAD_BYTES=26214400` as the sample value.

The `fa.nddev.asia` deployment uses a server-only Compose override at
`/home/ubuntu/nornikel-kg-search/docker-compose.server.yml`: `web` binds to
`127.0.0.1:8513`, `api` stays internal to the Compose network, and `qdrant` is not published
to the host. `docs/deployment/fa-nddev.md` was not updated by wave W0 and still references
`OPENAI_API_KEY`/`LITELLM_API_BASE` and the 5 MiB default upload size, which no longer match
`.env.example` or `README.md`'s open-weight LLM rules and new `https://nornikel.nddev.asia`
live-stand line.

## Contracts And Data

The web container serves the Vite build through Nginx and proxies `/api/` to the FastAPI
container. `VITE_API_BASE_URL` defaults to `/api` for container deployment and can be set to
`http://127.0.0.1:8000` during local dev.
The bundled web Nginx config (`apps/web/nginx.conf`) sets `client_max_body_size 6m`; the FastAPI
code default for `MAX_SOURCE_UPLOAD_BYTES` (`services/api/routes/sources.py`) is `5242880`
bytes, but `.env.example` now samples `26214400` (25 MiB), which exceeds the bundled Nginx
limit — see `mem:TECHDEBT-01-NOW` for the resulting gap. Host-level reverse proxies must keep an
equal or larger body limit than whatever `MAX_SOURCE_UPLOAD_BYTES` is configured to.

The API container sets `PROJECT_ROOT=/app`; `src/nornikel_kg/services/runtime.py` uses that
root to resolve `data/` and `sample_docs/` after the package is installed into site-packages.

Host-level Nginx terminates TLS for `fa.nddev.asia` in
`/etc/nginx/conf.d/fa-nddev-asia.conf`, uses the existing Let's Encrypt certificate under
`/etc/letsencrypt/live/fa.nddev.asia/`, and proxies HTTPS traffic to `127.0.0.1:8513`.

`pyproject.toml` adds `[[tool.mypy.overrides]]` for `litellm`/`langfuse` modules
(`ignore_missing_imports = true`, `follow_imports = "skip"`), so `uv run mypy --strict` does not
require type stubs for those packages.

## Invariants

- Do not commit `.env`, browser artifacts, `.playwright-cli/`, `.venv/`, node_modules, or DuckDB runtime files.
- Do not replace `npm ci` in CI/Docker with non-lockfile installs.
- Compose must remain valid without local secrets.
- Keep `MAX_SOURCE_UPLOAD_BYTES` (wherever configured) at or below the active Nginx `client_max_body_size`.

## Change Rules

When changing CI, verify the referenced GitHub Action major tags exist. When changing frontend
dependencies, update `apps/web/package-lock.json` and run the frontend build. When changing API
dependencies, update `uv.lock` and run backend tests. When changing `MAX_SOURCE_UPLOAD_BYTES` in
`.env.example` or code, also check `apps/web/nginx.conf` and any host-level reverse proxy limit.

## Verification

- `make ci`: proves Python lint/type/tests and TypeScript/build (53 backend tests pass at `1bca77f`).
- `make eval`: proves fixture answer verification metrics and exact material anti-regression
  cases.
- `docker compose config`: proves Compose syntax.
- Server smoke: `curl -fsS https://fa.nddev.asia/api/health` and public
  `POST https://fa.nddev.asia/api/qa/ask` prove the deployed reverse proxy and API route.
- Browser validation: local ignored screenshots under `browser/` prove the workbench desktop query,
  CSV upload, source counts, evidence cards, graph path, mobile layout, and strict material
  no-result/follow-up behavior.
