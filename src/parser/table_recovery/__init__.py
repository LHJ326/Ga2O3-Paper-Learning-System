"""Lightweight OCR table reconstruction without OCR runtime dependencies."""

from .models import (
    BoundingBox,
    OCRToken,
    ReconstructedTable,
    TableCell,
    TableFootnote,
    TableRecoverySpec,
    load_ocr_tokens,
    load_recovery_manifest,
)
from .normalizer import (
    normalize_footnote_suffix_spacing,
    normalize_ocr_text,
    split_footnote_suffix,
)
from .spatial_reconstructor import SpatialTableReconstructor

__all__ = [
    "BoundingBox",
    "OCRToken",
    "ReconstructedTable",
    "SpatialTableReconstructor",
    "TableCell",
    "TableFootnote",
    "TableRecoverySpec",
    "load_ocr_tokens",
    "load_recovery_manifest",
    "normalize_footnote_suffix_spacing",
    "normalize_ocr_text",
    "split_footnote_suffix",
]
