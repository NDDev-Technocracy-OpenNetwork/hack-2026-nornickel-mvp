<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: d60d647 fix: resolve runtime project root in containers
Scope: Makefile; .github/workflows/ci.yml; docker-compose.yml; docs/deployment/fa-nddev.md; apps/web/; services/api/
Area: RELEASE
-->

# RELEASE-01-VALIDATION

## Purpose

Capture the current validation and rollout contract for the server-first MVP scaffold.

## Source Of Truth

- `Makefile`: local quality-gate commands.
- `.github/workflows/ci.yml`: pull-request and `main` CI checks.
- `docker-compose.yml`: local/server container topology.
- `docs/deployment/fa-nddev.md`: deployment notes for `fa.nddev.asia`.
- `README.md`: quick start and demo scenario.

## Entry Points

- `make ci`: backend and frontend quality gate.
- `make eval`: deterministic fixture evaluation.
- `docker compose config`: Compose syntax validation without requiring `.env`.
- `docker compose up --build`: containerized API, web, and Qdrant run path.

## Current Behavior

CI has separate backend and frontend jobs. Backend runs `uv sync --group dev`,
`uv run ruff check .`, `uv run mypy`, `uv run pytest`, and `uv run python scripts/run_eval.py`.
Frontend runs `npm ci --no-audit`, `npm run typecheck`, and `npm run build`.

Docker Compose defines `api`, `web`, and `qdrant`. The `.env` file is optional in Compose;
runtime secrets are expected to live outside git.

## Contracts And Data

The web container serves the Vite build through Nginx and proxies `/api/` to the FastAPI
container. `VITE_API_BASE_URL` defaults to `/api` for container deployment and can be set to
`http://127.0.0.1:8000` during local dev.

The API container sets `PROJECT_ROOT=/app`; `src/nornikel_kg/services/runtime.py` uses that
root to resolve `data/` and `sample_docs/` after the package is installed into site-packages.

## Invariants

- Do not commit `.env`, browser artifacts, `.playwright-cli/`, `.venv/`, node_modules, or DuckDB runtime files.
- Do not replace `npm ci` in CI/Docker with non-lockfile installs.
- Compose must remain valid without local secrets.

## Change Rules

When changing CI, verify the referenced GitHub Action major tags exist. When changing frontend
dependencies, update `apps/web/package-lock.json` and run the frontend build. When changing API
dependencies, update `uv.lock` and run backend tests.

## Verification

- `make ci`: proves Python lint/type/tests and TypeScript/build.
- `make eval`: proves fixture answer verification metrics.
- `docker compose config`: proves Compose syntax.
- Browser validation: local ignored screenshots under `browser/` prove the workbench desktop/mobile flow.

## Known Gaps

- No server deployment has been executed from this branch yet.
- TLS/reverse proxy for `fa.nddev.asia` is assumed to be handled by server-level infrastructure.
