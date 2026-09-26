"""Abstract interface implemented by every PDF parser adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..schema.document import (
    Document,
    Equation,
    Figure,
    Metadata,
    Page,
    Section,
    Table,
    TextBlock,
)


class BaseParser(ABC):
    """Define parser capabilities without binding to a concrete tool."""

    @abstractmethod
    def parse(self, source: Path) -> Document:
        """Parse a source PDF into the canonical Document schema."""

    @abstractmethod
    def extract_metadata(self, source: Path) -> Metadata:
        """Extract traceable document metadata."""

    @abstractmethod
    def extract_pages(self, source: Path) -> list[Page]:
        """Extract source pages."""

    @abstractmethod
    def extract_sections(self, source: Path) -> list[Section]:
        """Extract logical sections."""

    @abstractmethod
    def extract_figures(self, source: Path) -> list[Figure]:
        """Extract figures."""

    @abstractmethod
    def extract_tables(self, source: Path) -> list[Table]:
        """Extract tables."""

    @abstractmethod
    def extract_equations(self, source: Path) -> list[Equation]:
        """Extract equations."""

    @abstractmethod
    def extract_text_blocks(self, source: Path) -> list[TextBlock]:
        """Extract text blocks."""
