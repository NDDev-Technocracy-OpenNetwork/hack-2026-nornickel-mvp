from __future__ import annotations

from fastapi import APIRouter

from nornikel_kg.services.runtime import get_ledger_repository

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
def list_sources() -> dict[str, object]:
    return {"sources": get_ledger_repository().list_sources()}
