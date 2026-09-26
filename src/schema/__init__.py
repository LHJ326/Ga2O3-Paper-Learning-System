"""Unified document schema exposed to parser implementations."""

from .document import (
    Document,
    DocumentElement,
    Equation,
    Figure,
    Metadata,
    Page,
    Section,
    Table,
    TextBlock,
)

__all__ = [
    "Document",
    "DocumentElement",
    "Equation",
    "Figure",
    "Metadata",
    "Page",
    "Section",
    "Table",
    "TextBlock",
]
