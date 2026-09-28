"""Model-neutral knowledge extractor interface; no provider implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.llm import ChatMessage, LLMAdapter

from .schema import KnowledgeSchema


@dataclass(frozen=True)
class ExtractionContext:
    paper_id: str
    document: Any
    schema: KnowledgeSchema
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_document: str | None = None


@dataclass(frozen=True)
class KnowledgeDraft:
    paper_id: str
    core: dict[str, Any]
    domain: dict[str, Any]
    summary: str
    key_points: str


class KnowledgeExtractor(ABC):
    """Provider-independent contract for future extraction implementations."""

    def __init__(self, llm: LLMAdapter) -> None:
        self._llm = llm

    @property
    def llm(self) -> LLMAdapter:
        """Adapter injected into this extractor."""
        return self._llm

    def generate(self, prompt: str) -> str:
        """Send one prompt through the configured adapter."""
        return self._llm.generate(prompt)

    def chat(self, messages: list[ChatMessage]) -> str:
        """Send an ordered message history through the configured adapter."""
        return self._llm.chat(messages)

    @abstractmethod
    def extract(self, context: ExtractionContext) -> KnowledgeDraft:
        """Return a draft without writing files or changing lifecycle state."""
        raise NotImplementedError
