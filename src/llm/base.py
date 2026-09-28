"""Common interfaces for text-generation providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping, Sequence, TypeAlias


ChatMessage: TypeAlias = Mapping[str, str]


class LLMAdapter(ABC):
    """Minimal synchronous interface implemented by any future provider."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for a single prompt."""
        raise NotImplementedError

    @abstractmethod
    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Generate a response for an ordered chat history."""
        raise NotImplementedError
