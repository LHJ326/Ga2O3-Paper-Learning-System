"""MinerU adapter interface placeholder.

No MinerU package is imported or executed in this phase.
"""

from __future__ import annotations

from pathlib import Path

from ...schema.document import Document
from .base import ParserAdapter


class MinerUAdapter(ParserAdapter):
    """Reserve the MinerU integration boundary for a later implementation."""

    def parse(self, source: Path) -> object:
        """Return MinerU raw output when integration is implemented."""
        raise NotImplementedError(
            "MinerU parsing is not implemented in Phase 1.5D-1A."
        )

    def convert(self, raw_output: object) -> Document:
        """Convert MinerU raw output when the output contract is defined."""
        raise NotImplementedError(
            "MinerU schema conversion is not implemented in Phase 1.5D-1A."
        )

    def validate(self, document: Document) -> bool:
        """Validate converted MinerU output when integration is implemented."""
        raise NotImplementedError(
            "MinerU document validation is not implemented in Phase 1.5D-1A."
        )
