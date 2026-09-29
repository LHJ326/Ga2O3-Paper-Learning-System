"""Coordinate chunk indexing without selecting or calling an embedding API."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Sequence

from src.embedding.schema import EmbeddingChunk

from .faiss_store import FaissStore
from .schema import VectorStore


def build_mock_vectors(
    chunks: Sequence[EmbeddingChunk], *, dimension: int = 16
) -> list[list[float]]:
    """Build deterministic non-semantic vectors for dry-runs and tests only."""

    if dimension <= 0:
        raise ValueError("dimension must be positive")
    vectors: list[list[float]] = []
    for chunk in chunks:
        seed = hashlib.sha256(chunk.chunk_id.encode("utf-8")).digest()
        vector = [((seed[index % len(seed)] / 255.0) * 2.0) - 1.0 for index in range(dimension)]
        if not any(vector):
            vector[0] = 1.0
        vectors.append(vector)
    return vectors


class IndexManager:
    def __init__(self, store_factory: Callable[[], VectorStore] = FaissStore) -> None:
        self.store_factory = store_factory

    def build(
        self,
        chunks: Sequence[EmbeddingChunk],
        vectors: Sequence[Sequence[float]],
    ) -> VectorStore:
        store = self.store_factory()
        store.add(chunks, vectors)
        return store

    def dry_run(
        self,
        chunks: Sequence[EmbeddingChunk],
        *,
        paper_id: str,
        storage_path: str | Path,
        registry_vectorstore_status: str,
        mock_dimension: int = 16,
    ) -> dict[str, Any]:
        vectors = build_mock_vectors(chunks, dimension=mock_dimension)
        store = self.build(chunks, vectors)
        index_count = getattr(store, "size", len(chunks))
        return {
            "paper_id": paper_id,
            "mode": "dry_run",
            "backend": "faiss.IndexFlatIP",
            "vector_source": "deterministic_mock",
            "vector_dimension": mock_dimension,
            "chunk_count": len(chunks),
            "index_count": index_count,
            "storage_path": Path(storage_path).as_posix(),
            "index_saved": False,
            "embedding_api_calls": 0,
            "registry_vectorstore_status": registry_vectorstore_status,
            "status": "ready_for_index_persistence" if chunks else "no_chunks",
        }
