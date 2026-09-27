"""Canonical document data model shared by every PDF parser adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Evidence:
    """Typed provenance decoded from a backward-compatible source reference."""

    paper_id: str | None
    parser_name: str | None
    parser_version: str | None
    source_file: str
    page: int | None
    mineru_locator: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> Evidence:
        """Build evidence while retaining parser-specific extension fields."""
        known_fields = {
            "paper_id",
            "parser_name",
            "parser_version",
            "source_file",
            "page",
            "mineru_locator",
        }
        return cls(
            paper_id=payload.get("paper_id"),
            parser_name=payload.get("parser_name"),
            parser_version=payload.get("parser_version"),
            source_file=str(payload.get("source_file", "")),
            page=payload.get("page"),
            mineru_locator=payload.get("mineru_locator"),
            details={
                key: value
                for key, value in payload.items()
                if key not in known_fields
            },
        )

    @classmethod
    def from_source_reference(cls, source_reference: str) -> Evidence:
        """Decode JSON evidence, with a safe bridge for legacy string locators."""
        try:
            payload = json.loads(source_reference)
        except (json.JSONDecodeError, TypeError):
            payload = None
        if isinstance(payload, dict):
            return cls.from_mapping(payload)
        return cls(
            paper_id=None,
            parser_name=None,
            parser_version=None,
            source_file=source_reference,
            page=None,
            details={"legacy_source_reference": source_reference},
        )

    def to_source_reference(self) -> str:
        """Serialize evidence using the existing JSON source-reference contract."""
        return json.dumps(
            {
                "paper_id": self.paper_id,
                "parser_name": self.parser_name,
                "parser_version": self.parser_version,
                "source_file": self.source_file,
                "page": self.page,
                "mineru_locator": self.mineru_locator,
                **self.details,
            },
            ensure_ascii=False,
            sort_keys=True,
        )


@dataclass(frozen=True)
class FigureTextRelation:
    """One explicit textual citation linking a Figure and a TextBlock."""

    id: str
    figure_id: str
    text_block_id: str
    relation_type: str
    reference_text: str
    normalized_reference: str
    subfigure_hint: str | None
    evidence: Evidence


@dataclass(frozen=True)
class EquationMetadata:
    """Typed representation details for an extracted Equation."""

    representation_type: str
    formula_image_path: str | None = None
    equation_number: str | None = None
    related_text_block_ids: tuple[str, ...] = ()


@dataclass
class DocumentElement:
    """An extracted object with a traceable reference to its source."""

    id: str
    page_number: int | None
    content: str
    source_reference: str

    @property
    def evidence(self) -> Evidence:
        """Return current typed evidence without duplicating mutable state."""
        return Evidence.from_source_reference(self.source_reference)


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

    metadata: EquationMetadata | None = None


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
    figure_text_relations: list[FigureTextRelation] = field(default_factory=list)
