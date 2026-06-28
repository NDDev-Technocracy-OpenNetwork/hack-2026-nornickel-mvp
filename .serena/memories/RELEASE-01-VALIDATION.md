<!-- Memory Metadata
Last updated: 2026-06-28
Last commit: 1e5e37a fix: harden ledger uploads and runtime init
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
- Playwright CLI session: validates React workbench query/upload flow and mobile layout with ignored
  `browser/ledger-fixed-*` artifacts.

## Current Behavior

CI has separate backend and frontend jobs. Backend runs `uv sync --group dev`,
`uv run ruff check .`, `uv run mypy`, `uv run pytest`, and `uv run python scripts/run_eval.py`.
Frontend runs `npm ci --no-audit`, `npm run typecheck`, and `npm run build`.

Docker Compose defines `api`, `web`, and `qdrant`. The `.env` file is optional in Compose;
runtime secrets are expected to live outside git.

The `fa.nddev.asia` deployment uses a server-only Compose override at
`/home/ubuntu/nornikel-kg-search/docker-compose.server.yml`: `web` binds to
`127.0.0.1:8513`, `api` stays internal to the Compose network, and `qdrant` is not published
to the host.

## Contracts And Data

The web container serves the Vite build through Nginx and proxies `/api/` to the FastAPI
container. `VITE_API_BASE_URL` defaults to `/api` for container deployment and can be set to
`http://127.0.0.1:8000` during local dev.

The API container sets `PROJECT_ROOT=/app`; `src/nornikel_kg/services/runtime.py` uses that
root to resolve `data/` and `sample_docs/` after the package is installed into site-packages.

Host-level Nginx terminates TLS for `fa.nddev.asia` in
`/etc/nginx/conf.d/fa-nddev-asia.conf`, uses the existing Let's Encrypt certificate under
`/etc/letsencrypt/live/fa.nddev.asia/`, and proxies HTTPS traffic to `127.0.0.1:8513`.

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
- Server smoke: `curl -fsS https://fa.nddev.asia/api/health` and public
  `POST https://fa.nddev.asia/api/qa/ask` prove the deployed reverse proxy and API route.
- Browser validation: local ignored screenshots under `browser/` prove the workbench desktop query,
  CSV upload, source counts, evidence cards, graph path, and mobile layout.
