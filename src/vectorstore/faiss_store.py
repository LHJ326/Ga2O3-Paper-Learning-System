"""FAISS-backed local vector store using normalized inner-product search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence, Self

import faiss
import numpy as np

from src.embedding.schema import EmbeddingChunk, EmbeddingSchemaError

from .schema import SearchHit, VectorStore, VectorStoreError


class FaissStore(VectorStore):
    """Evidence-preserving cosine-similarity index backed by local FAISS."""

    METADATA_VERSION = "1.0"

    def __init__(self) -> None:
        self._index: faiss.Index | None = None
        self._chunks: list[EmbeddingChunk] = []
        self._chunk_ids: set[str] = set()

    @property
    def size(self) -> int:
        return len(self._chunks)

    @property
    def dimension(self) -> int | None:
        return None if self._index is None else int(self._index.d)

    def add(
        self,
        chunks: Sequence[EmbeddingChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise VectorStoreError("chunks and vectors must have equal lengths")
        if not chunks:
            return
        duplicate = next((chunk.chunk_id for chunk in chunks if chunk.chunk_id in self._chunk_ids), None)
        if duplicate is not None or len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise VectorStoreError(f"duplicate chunk_id: {duplicate or 'within batch'}")
        matrix = self._matrix(vectors)
        if self._index is None:
            self._index = faiss.IndexFlatIP(matrix.shape[1])
        elif matrix.shape[1] != self._index.d:
            raise VectorStoreError(
                f"vector dimension {matrix.shape[1]} does not match index dimension {self._index.d}"
            )
        faiss.normalize_L2(matrix)
        self._index.add(matrix)
        self._chunks.extend(chunks)
        self._chunk_ids.update(chunk.chunk_id for chunk in chunks)

    def search(self, query_vector: Sequence[float], *, top_k: int = 5) -> list[SearchHit]:
        if top_k <= 0:
            raise VectorStoreError("top_k must be positive")
        if self._index is None or not self._chunks:
            return []
        query = self._matrix([query_vector])
        if query.shape[1] != self._index.d:
            raise VectorStoreError(
                f"query dimension {query.shape[1]} does not match index dimension {self._index.d}"
            )
        if float(np.linalg.norm(query[0])) == 0.0:
            raise VectorStoreError("query vector must not be zero")
        faiss.normalize_L2(query)
        scores, indices = self._index.search(query, min(top_k, self.size))
        return [
            SearchHit(chunk=self._chunks[int(index)], score=float(score))
            for score, index in zip(scores[0], indices[0], strict=True)
            if index >= 0
        ]

    def save(self, path: str | Path) -> Path:
        if self._index is None:
            raise VectorStoreError("cannot save an empty FAISS index")
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_index = destination.with_suffix(destination.suffix + ".tmp")
        metadata_path = self._metadata_path(destination)
        temporary_metadata = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
        faiss.write_index(self._index, str(temporary_index))
        payload: dict[str, Any] = {
            "schema_version": self.METADATA_VERSION,
            "backend": "faiss.IndexFlatIP",
            "metric": "cosine",
            "dimension": self.dimension,
            "count": self.size,
            "chunks": [chunk.as_dict() for chunk in self._chunks],
        }
        temporary_metadata.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary_index.replace(destination)
        temporary_metadata.replace(metadata_path)
        return destination

    @classmethod
    def load(cls, path: str | Path) -> Self:
        source = Path(path)
        metadata_path = cls._metadata_path(source)
        if not source.is_file() or not metadata_path.is_file():
            raise FileNotFoundError(f"FAISS index or metadata is missing: {source}")
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != cls.METADATA_VERSION:
            raise VectorStoreError("unsupported vector-store metadata version")
        raw_chunks = payload.get("chunks")
        if not isinstance(raw_chunks, list):
            raise VectorStoreError("vector-store metadata chunks must be a list")
        instance = cls()
        try:
            instance._chunks = [
                EmbeddingChunk(
                    chunk_id=item["chunk_id"],
                    paper_id=item["paper_id"],
                    source_file=item["source_file"],
                    evidence_ids=tuple(item["evidence_ids"]),
                    text=item["text"],
                )
                for item in raw_chunks
            ]
        except (KeyError, TypeError, EmbeddingSchemaError) as exc:
            raise VectorStoreError("invalid chunk metadata") from exc
        instance._index = faiss.read_index(str(source))
        if instance._index.ntotal != len(instance._chunks):
            raise VectorStoreError("FAISS index count does not match chunk metadata")
        if payload.get("dimension") != instance.dimension:
            raise VectorStoreError("FAISS index dimension does not match metadata")
        instance._chunk_ids = {chunk.chunk_id for chunk in instance._chunks}
        if len(instance._chunk_ids) != len(instance._chunks):
            raise VectorStoreError("duplicate chunk IDs in metadata")
        return instance

    @staticmethod
    def _matrix(vectors: Sequence[Sequence[float]]) -> np.ndarray:
        try:
            matrix = np.asarray(vectors, dtype=np.float32)
        except (TypeError, ValueError) as exc:
            raise VectorStoreError("vectors must be a rectangular numeric matrix") from exc
        if matrix.ndim != 2 or matrix.shape[1] == 0:
            raise VectorStoreError("vectors must be a non-empty two-dimensional matrix")
        if not np.isfinite(matrix).all():
            raise VectorStoreError("vectors must contain only finite values")
        if np.any(np.linalg.norm(matrix, axis=1) == 0):
            raise VectorStoreError("vectors must not contain zero vectors")
        return np.ascontiguousarray(matrix)

    @staticmethod
    def _metadata_path(path: Path) -> Path:
        return path.with_suffix(path.suffix + ".meta.json")
