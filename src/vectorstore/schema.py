"""Abstract contract shared by local vector-store implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Self

from src.embedding.schema import EmbeddingChunk


class VectorStoreError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk: EmbeddingChunk
    score: float


class VectorStore(ABC):
    @abstractmethod
    def add(
        self,
        chunks: Sequence[EmbeddingChunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        """Add aligned chunks and vectors to the index."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query_vector: Sequence[float], *, top_k: int = 5) -> list[SearchHit]:
        """Return the highest-scoring chunks for one query vector."""
        raise NotImplementedError

    @abstractmethod
    def save(self, path: str | Path) -> Path:
        """Persist the index and its evidence-linked metadata."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(cls, path: str | Path) -> Self:
        """Load a previously persisted index."""
        raise NotImplementedError
