# Claude Project Notes

## Scope
Repository: `nornikel-hackathon`
Owner workflow: rldyour plugins/skills.

## Project state (verified)
- P0 backend is a deterministic evidence-led QA system built on DuckDB.
- Sources: `src/nornikel_kg/`; API routes: `services/api/routes/`; frontend: `apps/web/`.
- `make ci`, `make eval` and browser/ deploy smoke are used for validation.
- Memory/invariant source-of-truth is `.serena/memories/`.

## Durable Commands
- Backend checks: `uv run ruff check .`, `uv run mypy`, `uv run pytest`.
- Frontend checks: `cd apps/web && npm run lint`, `npm run typecheck`, `npm run build`.
- Combined smoke: `make ci` and `make eval`.

## Branch / Git
- Pushes go through feature branches and PR merge to `main`.
- `main...origin/main` should remain clean and synced.

## Runtime Paths
- DuckDB path defaults to `data/catalog.duckdb`.
- Synthetic fixture path defaults to `sample_docs/synthetic`.

## Validation and deployment notes
- Public deployment target and container path: `fa.nddev.asia`, compose services `api`, `web`, and `qdrant`.
- Do not leave local runtime artifacts (temp DBs, browser artifacts, runtime markers).

## Known TODOs / P1
- Connect Qdrant retrieval path to runtime query stage.
- Add Docling/OCR ingestion path for PDF/DOCX/PPTX/XLSX/image.
- Add LiteLLM extraction / answer synthesis stage.
