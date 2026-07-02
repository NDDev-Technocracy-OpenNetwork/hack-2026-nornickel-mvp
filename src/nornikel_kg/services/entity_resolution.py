from __future__ import annotations

import logging
from dataclasses import dataclass

from nornikel_kg.adapters.duckdb.repositories import DuckDBLedgerRepository
from nornikel_kg.domain.ids import stable_hash
from nornikel_kg.domain.normalization import canonical_key

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolutionResult:
    entity_id: str
    action: str  # "matched_key" | "matched_alias" | "created"


class EntityResolutionService:
    """LightRAG-style resolution: exact canonical key -> alias -> create.

    The embedding fallback (cosine >= 0.90 against the Qdrant `entities`
    collection) plugs in between alias match and creation once retrieval
    lands in W3; the ordering contract stays stop-at-first-hit.

    Guard: entities of the same type with different canonical keys are never
    merged (`Ni-30Cu` vs `Ni-20Cu` stay distinct), and resolution never
    crosses entity types.
    """

    def __init__(self, repository: DuckDBLedgerRepository) -> None:
        self.repository = repository

    def resolve_or_create(
        self,
        *,
        mention: str,
        entity_type: str,
        span_ids: list[str],
        confidence: float = 0.85,
    ) -> ResolutionResult:
        mention = mention.strip()
        if not mention:
            raise ValueError("Cannot resolve an empty mention")

        existing = self.repository.find_entity(mention, entity_type)
        if existing is not None:
            is_key_match = existing["canonical_key"] == canonical_key(mention)
            self.repository.merge_entity_evidence(
                existing["entity_id"],
                span_ids=span_ids,
                new_alias=None if is_key_match else mention,
            )
            return ResolutionResult(
                entity_id=existing["entity_id"],
                action="matched_key" if is_key_match else "matched_alias",
            )

        entity_id = f"ent_{entity_type}_{stable_hash([entity_type, canonical_key(mention)], 16)}"
        self.repository.create_entity(
            entity_id=entity_id,
            entity_type=entity_type,
            canonical_name=mention,
            evidence_span_ids=span_ids,
            confidence=confidence,
        )
        return ResolutionResult(entity_id=entity_id, action="created")
