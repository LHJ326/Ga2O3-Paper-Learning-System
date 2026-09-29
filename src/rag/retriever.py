"""Translate natural-language queries into Evidence-aware FAISS results."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence

from src.vectorstore.schema import VectorStore

from .response_schema import RetrievalResult

QueryEncoder = Callable[[str], Sequence[float]]


class Retriever:
    def __init__(self, store: VectorStore, query_encoder: QueryEncoder) -> None:
        self.store = store
        self.query_encoder = query_encoder

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        vector = self.query_encoder(query)
        hits = self.store.search(vector, top_k=top_k)
        return [
            RetrievalResult(
                paper_id=hit.chunk.paper_id,
                chunk_id=hit.chunk.chunk_id,
                similarity=hit.score,
                evidence_ids=hit.chunk.evidence_ids,
                source=hit.chunk.source_file,
            )
            for hit in hits
        ]


def build_mock_query_vector(query: str, *, dimension: int = 16) -> list[float]:
    """Return a deterministic non-semantic vector for dry-run wiring tests."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if dimension <= 0:
        raise ValueError("dimension must be positive")
    seed = hashlib.sha256(query.encode("utf-8")).digest()
    vector = [((seed[index % len(seed)] / 255.0) * 2.0) - 1.0 for index in range(dimension)]
    if not any(vector):
        vector[0] = 1.0
    return vector
