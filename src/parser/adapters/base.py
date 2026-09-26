"""Abstract interface for converting external parser output."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ...schema.document import Document


class ParserAdapter(ABC):
    """Define the boundary between an external parser and the project schema."""

    @abstractmethod
    def parse(self, source: Path) -> object:
        """Produce tool-specific raw output from a source document."""

    @abstractmethod
    def convert(self, raw_output: object) -> Document:
        """Convert tool-specific output into the unified Document schema."""

    @abstractmethod
    def validate(self, document: Document) -> bool:
        """Validate a converted document before downstream use."""
