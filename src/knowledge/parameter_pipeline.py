"""Orchestrate model-neutral parameter extraction, validation, and writing."""

from __future__ import annotations

from pathlib import Path

from .parameter_extractor import ParameterDraft, ParameterExtractionContext, ParameterExtractor
from .parameter_validator import ParameterValidator
from .parameter_writer import ParameterWriter


class ParameterExtractionPipeline:
    def __init__(
        self,
        *,
        extractor: ParameterExtractor,
        validator: ParameterValidator,
        writer: ParameterWriter,
    ) -> None:
        self.extractor = extractor
        self.validator = validator
        self.writer = writer

    def run(self, context: ParameterExtractionContext) -> tuple[ParameterDraft, Path]:
        draft = self.extractor.extract(context)
        if draft.paper_id != context.paper_id:
            raise ValueError("extracted paper_id does not match extraction context")
        self.validator.validate(draft).raise_if_invalid()
        return draft, self.writer.write(draft)
