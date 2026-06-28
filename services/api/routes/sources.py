from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from nornikel_kg.adapters.duckdb.repositories import SourceIngestError
from nornikel_kg.domain.models import EvidenceSpan, SourceIngestResponse, SourceSummary
from nornikel_kg.services.runtime import get_ledger_repository

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources() -> dict[str, list[SourceSummary]]:
    return {"sources": get_ledger_repository().list_sources()}


@router.get("/{source_id}/evidence")
def list_source_evidence(source_id: str) -> dict[str, list[EvidenceSpan]]:
    repository = get_ledger_repository()
    if repository.get_source(source_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {"evidence": repository.list_evidence_spans(source_id)}


@router.delete("/{source_id}")
def delete_source(source_id: str) -> dict[str, object]:
    repository = get_ledger_repository()
    if not repository.delete_source(source_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return {"source_id": source_id, "deleted": True}


_ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".md", ".markdown", ".txt", ".text"}


@router.post("/upload")
async def upload_source(file: Annotated[UploadFile, File(...)]) -> SourceIngestResponse:
    filename = file.filename or "uploaded-source"
    extension = Path(filename).suffix.lower()
    if extension not in _ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported upload type. Allowed: .csv, .md, .markdown, .txt",
        )
    content = await file.read()
    try:
        return get_ledger_repository().ingest_source_bytes(
            filename=filename,
            content=content,
        )
    except SourceIngestError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
