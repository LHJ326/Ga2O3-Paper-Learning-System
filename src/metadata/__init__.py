"""Lightweight bibliographic metadata ingestion."""

from .pipeline import (
    MetadataImportError,
    PaperMetadata,
    import_metadata,
    parse_metadata,
)

__all__ = [
    "MetadataImportError",
    "PaperMetadata",
    "import_metadata",
    "parse_metadata",
]
