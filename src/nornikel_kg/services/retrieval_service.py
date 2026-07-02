from __future__ import annotations

import logging
import os

from nornikel_kg.adapters.duckdb.repositories import DuckDBLedgerRepository
from nornikel_kg.ports.retrieval import IndexableUnit, VectorIndexPort

logger = logging.getLogger(__name__)

EVIDENCE_COLLECTION = os.getenv("QDRANT_COLLECTION", "evidence_units")
ENTITY_COLLECTION = "entities"


class RetrievalService:
    """Qdrant hybrid retrieval over evidence spans, rejoined to DuckDB.

    Retrieval is additive: the deterministic slot-SQL path stays primary and
    any index failure degrades to an empty candidate list, never an error.
    """

    def __init__(
        self,
        repository: DuckDBLedgerRepository,
        index: VectorIndexPort | None,
    ) -> None:
        self.repository = repository
        self.index = index

    @property
    def enabled(self) -> bool:
        return self.index is not None

    def index_source(self, source_id: str) -> int:
        if self.index is None:
            return 0
        spans = self.repository.list_evidence_spans(source_id)
        units = [
            IndexableUnit(
                unit_id=span.span_id,
                text=span.visible_text,
                payload={
                    "source_id": span.source_id,
                    "span_type": span.span_type,
                    "security_label": span.security_label,
                },
            )
            for span in spans
            if span.visible_text.strip()
        ]
        try:
            self.index.delete_source_units(EVIDENCE_COLLECTION, source_id)
            count = self.index.index_units(EVIDENCE_COLLECTION, units)
            count += self._index_entities()
            return count
        except Exception:
            logger.warning("Indexing failed for %s; retrieval degraded", source_id, exc_info=True)
            return 0

    def reindex_all(self) -> int:
        if self.index is None:
            return 0
        total = 0
        for source in self.repository.list_sources():
            total += self.index_source(source.source_id)
        return total

    def _index_entities(self) -> int:
        assert self.index is not None
        units = [
            IndexableUnit(
                unit_id=entity["entity_id"],
                text=entity["canonical_name"],
                payload={"entity_type": entity["entity_type"]},
            )
            for entity in self.repository.list_graph_entities()
        ]
        return self.index.index_units(ENTITY_COLLECTION, units)

    def retrieve_span_ids(
        self,
        *,
        question: str,
        allowed_labels: list[str],
        source_ids: list[str] | None = None,
        top_k: int = 10,
    ) -> list[str]:
        """Hybrid search -> span IDs verified to still exist in DuckDB."""
        if self.index is None:
            return []
        try:
            hits = self.index.hybrid_search(
                EVIDENCE_COLLECTION,
                query=question,
                top_k=top_k,
                allowed_labels=allowed_labels,
                source_ids=source_ids,
            )
        except Exception:
            logger.warning("Hybrid retrieval failed; degrading to SQL-only", exc_info=True)
            return []
        if not hits:
            return []
        # DuckDB rejoin + allowed-label recheck: the index is never authoritative.
        known = {
            span.span_id: span
            for span in self.repository.list_evidence_spans()
            if span.security_label in allowed_labels
        }
        return [hit.unit_id for hit in hits if hit.unit_id in known]
