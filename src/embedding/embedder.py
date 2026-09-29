"""Abstract embedding provider boundary.

No concrete model or API is selected at this phase.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingAdapter(ABC):
    """Model-independent interface implemented by future embedding backends."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one numeric vector per input text."""
        raise NotImplementedError
