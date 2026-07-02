from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class SparseVector:
    indices: list[int]
    values: list[float]


@dataclass(frozen=True)
class IndexableUnit:
    """One retrieval unit (evidence span or entity card) with filterable payload."""

    unit_id: str
    text: str
    payload: dict[str, str | int | float | list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalHit:
    unit_id: str
    score: float
    payload: dict[str, object] = field(default_factory=dict)


class EmbeddingBackendPort(Protocol):
    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        """Dense vectors for texts (query and documents share one model)."""

    def embed_sparse(self, texts: list[str]) -> list[SparseVector]:
        """Sparse lexical vectors (BM25-style); may return empty vectors."""


class VectorIndexPort(Protocol):
    def index_units(self, collection: str, units: list[IndexableUnit]) -> int:
        """Upsert units into a collection; returns the number indexed."""

    def hybrid_search(
        self,
        collection: str,
        *,
        query: str,
        top_k: int = 10,
        allowed_labels: list[str] | None = None,
        source_ids: list[str] | None = None,
    ) -> list[RetrievalHit]:
        """Dense+sparse RRF search with payload filters."""

    def delete_source_units(self, collection: str, source_id: str) -> None:
        """Remove all units belonging to one source."""
