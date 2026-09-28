"""Batch ingestion for project-controlled paper objects."""

from .pipeline import (
    IngestedPaper,
    IngestionError,
    ingest_directory,
    next_paper_id,
    scan_pdf_directory,
)

__all__ = [
    "IngestedPaper",
    "IngestionError",
    "ingest_directory",
    "next_paper_id",
    "scan_pdf_directory",
]
