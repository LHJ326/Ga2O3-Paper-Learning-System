"""Canonical document data model shared by every PDF parser adapter."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocumentElement:
    """An extracted object with a traceable reference to its source."""

    id: str
    page_number: int | None
    content: str
    source_reference: str


@dataclass
class Metadata(DocumentElement):
    """Document-level metadata represented as traceable content."""


@dataclass
class Page(DocumentElement):
    """A single source-document page."""


@dataclass
class Section(DocumentElement):
    """A logical document section."""


@dataclass
class Figure(DocumentElement):
    """A figure and its normalized textual representation."""


@dataclass
class Table(DocumentElement):
    """A table and its normalized textual representation."""


@dataclass
class Equation(DocumentElement):
    """An equation and its normalized textual representation."""


@dataclass
class TextBlock(DocumentElement):
    """A contiguous block of extracted text."""


@dataclass
class Document:
    """Parser-independent representation of one source document."""

    document_id: str
    metadata: Metadata
    pages: list[Page] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    equations: list[Equation] = field(default_factory=list)
    text_blocks: list[TextBlock] = field(default_factory=list)
