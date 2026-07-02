from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

from nornikel_kg.ports.retrieval import SparseVector

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _dense_model() -> Any:
    from sentence_transformers import SentenceTransformer

    model_id = os.getenv("EMBEDDING_MODEL_ID", "deepvk/USER-bge-m3")
    logger.info("Loading dense embedding model %s", model_id)
    return SentenceTransformer(model_id, device="cpu")


@lru_cache(maxsize=1)
def _sparse_model() -> Any:
    from fastembed import SparseTextEmbedding

    model_id = os.getenv("SPARSE_MODEL_ID", "Qdrant/bm25")
    logger.info("Loading sparse embedding model %s", model_id)
    return SparseTextEmbedding(model_name=model_id)


class LocalEmbeddingBackend:
    """CPU embeddings: USER-bge-m3 dense + fastembed BM25 sparse."""

    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        vectors = _dense_model().encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embed_sparse(self, texts: list[str]) -> list[SparseVector]:
        results: list[SparseVector] = []
        for embedding in _sparse_model().embed(texts):
            results.append(
                SparseVector(
                    indices=[int(i) for i in embedding.indices],
                    values=[float(v) for v in embedding.values],
                )
            )
        return results
