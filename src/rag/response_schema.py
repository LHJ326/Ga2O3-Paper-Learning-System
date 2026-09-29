"""Structured response schema for evidence-aware retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


class ResponseSchemaError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    paper_id: str
    chunk_id: str
    similarity: float
    evidence_ids: tuple[str, ...]
    source: str

    def __post_init__(self) -> None:
        for name in ("paper_id", "chunk_id", "source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ResponseSchemaError(f"{name} must be a non-empty string")
        if not isinstance(self.similarity, (int, float)) or not isfinite(self.similarity):
            raise ResponseSchemaError("similarity must be finite")
        if not isinstance(self.evidence_ids, tuple) or not self.evidence_ids:
            raise ResponseSchemaError("retrieval results must retain Evidence IDs")
        if any(not isinstance(item, str) or not item for item in self.evidence_ids):
            raise ResponseSchemaError("Evidence IDs must be non-empty strings")

    def as_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "chunk_id": self.chunk_id,
            "similarity": round(float(self.similarity), 8),
            "evidence_ids": list(self.evidence_ids),
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class QueryResponse:
    query: str
    top_k: int
    results: tuple[RetrievalResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ResponseSchemaError("query must be a non-empty string")
        if not isinstance(self.top_k, int) or self.top_k <= 0:
            raise ResponseSchemaError("top_k must be a positive integer")
        if not isinstance(self.results, tuple):
            raise ResponseSchemaError("results must be a tuple")
        if len(self.results) > self.top_k:
            raise ResponseSchemaError("results exceed top_k")

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "top_k": self.top_k,
            "results": [item.as_dict() for item in self.results],
        }
