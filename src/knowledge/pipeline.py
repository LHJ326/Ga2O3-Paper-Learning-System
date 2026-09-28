"""Orchestrate extraction, validation, and persistence for one paper."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.schema import Document

from .extractor import ExtractionContext, KnowledgeExtractor
from .schema import KnowledgeSchema
from .validator import KnowledgeValidator
from .writer import KnowledgeWriter


class KnowledgeExtractionPipeline:
    def __init__(
        self,
        *,
        extractor: KnowledgeExtractor,
        validator: KnowledgeValidator,
        writer: KnowledgeWriter,
    ) -> None:
        self.extractor = extractor
        self.validator = validator
        self.writer = writer

    def run(
        self,
        *,
        paper_id: str,
        document: Document,
        schema: KnowledgeSchema,
        source_document: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Path]:
        context = ExtractionContext(
            paper_id=paper_id,
            document=document,
            schema=schema,
            metadata=metadata or {},
            source_document=source_document,
        )
        draft = self.extractor.extract(context)
        self.validator.validate(draft).raise_if_invalid()
        return self.writer.write(draft)
