from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from nornikel_kg.domain.models import EvidenceSpan, SourceIngestResponse, SourceSummary
from nornikel_kg.services.runtime import get_ledger_repository

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources() -> dict[str, list[SourceSummary]]:
    return {"sources": get_ledger_repository().list_sources()}


@router.get("/{source_id}/evidence")
def list_source_evidence(source_id: str) -> dict[str, list[EvidenceSpan]]:
    return {"evidence": get_ledger_repository().list_evidence_spans(source_id)}


@router.post("/upload")
async def upload_source(file: Annotated[UploadFile, File(...)]) -> SourceIngestResponse:
    content = await file.read()
    return get_ledger_repository().ingest_source_bytes(
        filename=file.filename or "uploaded-source",
        content=content,
    )
