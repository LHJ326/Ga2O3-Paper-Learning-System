"""Small dependency-free local vector store for future adapter outputs."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .schema import EmbeddingChunk


class VectorStoreError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk: EmbeddingChunk
    score: float


class LocalVectorStore:
    def __init__(self) -> None:
        self._entries: dict[str, tuple[EmbeddingChunk, tuple[float, ...]]] = {}
        self._dimension: int | None = None

    @property
    def dimension(self) -> int | None:
        return self._dimension

    def add(
        self,
        chunks: Sequence[EmbeddingChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise VectorStoreError("chunks and vectors must have equal lengths")
        prepared: list[tuple[EmbeddingChunk, tuple[float, ...]]] = []
        for chunk, raw_vector in zip(chunks, vectors, strict=True):
            if chunk.chunk_id in self._entries or any(
                previous.chunk_id == chunk.chunk_id for previous, _ in prepared
            ):
                raise VectorStoreError(f"duplicate chunk_id: {chunk.chunk_id}")
            try:
                vector = tuple(float(value) for value in raw_vector)
            except (TypeError, ValueError) as exc:
                raise VectorStoreError("vectors must contain numeric values") from exc
            if not vector or any(not math.isfinite(value) for value in vector):
                raise VectorStoreError("vectors must be non-empty and finite")
            dimension = self._dimension or (len(prepared[0][1]) if prepared else len(vector))
            if len(vector) != dimension:
                raise VectorStoreError("all vectors must share one dimension")
            prepared.append((chunk, vector))
        if prepared and self._dimension is None:
            self._dimension = len(prepared[0][1])
        for chunk, vector in prepared:
            self._entries[chunk.chunk_id] = (chunk, vector)

    def search(self, query_vector: Sequence[float], *, top_k: int = 5) -> list[SearchResult]:
        if top_k <= 0:
            raise VectorStoreError("top_k must be positive")
        if self._dimension is None:
            return []
        query = tuple(float(value) for value in query_vector)
        if len(query) != self._dimension or any(not math.isfinite(value) for value in query):
            raise VectorStoreError("query vector has an invalid dimension or value")
        query_norm = math.sqrt(sum(value * value for value in query))
        if query_norm == 0:
            raise VectorStoreError("query vector must not be zero")
        results: list[SearchResult] = []
        for chunk, vector in self._entries.values():
            vector_norm = math.sqrt(sum(value * value for value in vector))
            score = 0.0 if vector_norm == 0 else sum(
                left * right for left, right in zip(query, vector, strict=True)
            ) / (query_norm * vector_norm)
            results.append(SearchResult(chunk=chunk, score=score))
        return sorted(results, key=lambda item: (-item.score, item.chunk.chunk_id))[:top_k]

    def save(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "dimension": self._dimension,
            "entries": [
                {"chunk": chunk.as_dict(), "vector": list(vector)}
                for chunk, vector in sorted(
                    self._entries.values(), key=lambda item: item[0].chunk_id
                )
            ],
        }
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(destination)
        return destination
