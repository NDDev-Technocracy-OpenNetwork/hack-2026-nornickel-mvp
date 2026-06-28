from __future__ import annotations

from fastapi import APIRouter

from nornikel_kg.domain.models import AskRequest, AskResponse
from nornikel_kg.services.runtime import get_qa_service

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask")
def ask(request: AskRequest) -> AskResponse:
    return get_qa_service().ask(request)
