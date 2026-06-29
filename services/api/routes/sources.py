from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from nornikel_kg.adapters.duckdb.repositories import SourceIngestError
from nornikel_kg.domain.models import EvidenceSpan, SourceIngestResponse, SourceSummary
from nornikel_kg.services.runtime import get_ledger_repository

router = APIRouter(prefix="/sources", tags=["sources"])


def _max_upload_bytes() -> int:
    raw_value = os.getenv("MAX_SOURCE_UPLOAD_BYTES", "5242880")
    try:
        value = int(raw_value)
    except ValueError:
        return 5 * 1024 * 1024
    return max(1, value)


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
_ALLOWED_MIME_TYPES = {
    ".csv": {
        "text/csv",
        "text/plain",
        "application/csv",
        "application/vnd.ms-excel",
    },
    ".md": {
        "text/markdown",
        "text/x-markdown",
        "text/plain",
    },
    ".markdown": {
        "text/markdown",
        "text/x-markdown",
        "text/plain",
    },
    ".txt": {"text/plain"},
    ".text": {"text/plain"},
}


@router.post("/upload")
async def upload_source(file: Annotated[UploadFile, File(...)]) -> SourceIngestResponse:
    filename = file.filename or "uploaded-source"
    extension = Path(filename).suffix.lower()
    max_upload_bytes = _max_upload_bytes()

    if extension not in _ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported upload type. Allowed: .csv, .md, .markdown, .txt, .text",
        )
    if file.size is not None and file.size > max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Uploaded file is too large. Maximum allowed size is {max_upload_bytes} bytes.",
        )
    content_type = (file.content_type or "").lower()
    allowed_mime_types = _ALLOWED_MIME_TYPES.get(extension, set())
    if content_type and content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported MIME type '{content_type}'. "
                "Allowed: text/csv, text/plain, text/markdown, text/x-markdown."
            ),
        )

    content = await file.read(max_upload_bytes + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(content) > max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Uploaded file is too large. Maximum allowed size is {max_upload_bytes} bytes.",
        )
    try:
        return get_ledger_repository().ingest_source_bytes(
            filename=filename,
            content=content,
        )
    except SourceIngestError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
