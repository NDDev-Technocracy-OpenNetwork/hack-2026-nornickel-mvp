# Nornikel Materials KG Search

Evidence-first materials research workbench for the Nornikel hackathon.

The P0 product promise is:

> For every answer sentence, show the exact document/span/table row, validation status,
> and graph path that supports it.

## Current Scope

This repository now contains a working scaffold for the MVP:

- FastAPI backend with deterministic evidence-backed QA contracts.
- React/Vite frontend for the analysis workbench.
- Stable `EvidenceSpan` ID primitives.
- Pydantic domain models for evidence, measurements, effects, graph paths, and answer claims.
- Synthetic fixture corpus and gold/adversarial evaluation placeholders.
- CI for backend lint/type/tests/eval and frontend type/build.
- Docker Compose with API, web, and Qdrant services.

Planning and architecture documents live in `.serena/newproj/nornikel-kg-search/`.
The current implementation contract is `.serena/newproj/nornikel-kg-search/18_IMPLEMENTATION_SPEC.md`.
Owner decisions are recorded in `.serena/newproj/nornikel-kg-search/19_OWNER_DECISIONS.md`.

## Quick Start

Requirements:

- Python 3.12
- uv
- Node 24
- Docker Compose, optional for container run

Install dependencies:

```bash
make install
```

Run the backend:

```bash
make api
```

Run the frontend:

```bash
cd apps/web
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

Run all local quality gates:

```bash
make ci
make eval
docker compose config
```

## Demo Scenario

The scaffold ships one ideal synthetic scenario:

```text
What has already been done for Ni-30Cu under aging at 700 C for 8 h,
and what effect was observed on hardness?
```

The API returns:

- grounded Russian summary;
- experiment table;
- exact `EvidenceSpan` cards;
- canonical graph path:
  `Material -> Experiment -> Regime -> Step -> Measurement -> Property -> Evidence -> Document`;
- one method-mismatch conflict;
- one missing-conductivity data gap;
- verification metrics with unsupported claims and source-label leaks set to zero.

## Architecture Boundary

P0 keeps the system modular but intentionally simple:

- DuckDB is the future system of record for the scientific evidence ledger.
- Qdrant is retrieval only.
- NetworkX is reserved for per-query graph neighborhoods.
- LiteLLM/OpenAI-compatible providers are prepared through environment variables.
- Docling/OCR ingestion is a P1 adapter path; current scaffold uses synthetic fixtures.

No real secrets are committed. Copy `.env.example` to `.env` on a runtime host and fill provider keys there.

## Repository Layout

```text
apps/web/          React/Vite workbench
services/api/      FastAPI app and routes
src/nornikel_kg/   Domain, services, adapters, resources
eval/              Gold and adversarial question fixtures
sample_docs/       Synthetic smoke-test corpus
tests/             Unit and integration tests
docs/deployment/   Server deployment notes
```
