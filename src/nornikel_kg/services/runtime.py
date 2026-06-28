from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from nornikel_kg.adapters.duckdb.repositories import DuckDBLedgerRepository
from nornikel_kg.services.qa_service import DemoQAService


def project_root() -> Path:
    configured_root = os.getenv("PROJECT_ROOT")
    if configured_root:
        return Path(configured_root).resolve()

    current_directory = Path.cwd()
    if (current_directory / "sample_docs").exists():
        return current_directory

    return Path(__file__).resolve().parents[3]


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root() / path


@lru_cache
def get_ledger_repository() -> DuckDBLedgerRepository:
    db_path = resolve_project_path(os.getenv("DUCKDB_PATH", "data/catalog.duckdb"))
    sample_dir = resolve_project_path(os.getenv("SYNTHETIC_SAMPLE_DIR", "sample_docs/synthetic"))
    repository = DuckDBLedgerRepository(db_path)
    repository.seed_synthetic_fixture(sample_dir)
    return repository


@lru_cache
def get_qa_service() -> DemoQAService:
    return DemoQAService(ledger_repository=get_ledger_repository())
