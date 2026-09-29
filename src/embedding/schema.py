"""Data contracts for evidence-linked embedding chunks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class EmbeddingSchemaError(ValueError):
    """Raised when an embedding chunk violates the local schema."""


@dataclass(frozen=True, slots=True)
class EmbeddingChunk:
    chunk_id: str
    paper_id: str
    source_file: str
    evidence_ids: tuple[str, ...]
    text: str

    def __post_init__(self) -> None:
        for field_name in ("chunk_id", "paper_id", "source_file", "text"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise EmbeddingSchemaError(f"{field_name} must be a non-empty string")
        if not isinstance(self.evidence_ids, tuple):
            raise EmbeddingSchemaError("evidence_ids must be a tuple")
        if not self.evidence_ids:
            raise EmbeddingSchemaError("embedding chunks must retain at least one Evidence ID")
        if any(not isinstance(item, str) or not item.strip() for item in self.evidence_ids):
            raise EmbeddingSchemaError("Evidence IDs must be non-empty strings")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise EmbeddingSchemaError("evidence_ids must be unique")

    def as_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "source_file": self.source_file,
            "evidence_ids": list(self.evidence_ids),
            "text": self.text,
        }
