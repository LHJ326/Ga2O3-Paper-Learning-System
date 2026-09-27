"""Unified document schema exposed to parser implementations."""

from .document import (
    Document,
    DocumentElement,
    EquationMetadata,
    Evidence,
    Equation,
    Figure,
    FigureTextRelation,
    Metadata,
    Page,
    Section,
    Table,
    TextBlock,
)

__all__ = [
    "Document",
    "DocumentElement",
    "EquationMetadata",
    "Evidence",
    "Equation",
    "Figure",
    "FigureTextRelation",
    "Metadata",
    "Page",
    "Section",
    "Table",
    "TextBlock",
]
