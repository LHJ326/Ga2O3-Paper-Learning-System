"""Persist validated parameter drafts without altering their contents."""

from __future__ import annotations

from pathlib import Path

import yaml

from .parameter_extractor import ParameterDraft
from .parameter_validator import ParameterValidator


class ParameterWriter:
    def __init__(
        self,
        *,
        validator: ParameterValidator,
        papers_root: str | Path = "data/papers",
    ) -> None:
        self.validator = validator
        self.papers_root = Path(papers_root)

    def write(self, draft: ParameterDraft) -> Path:
        self.validator.validate(draft).raise_if_invalid()
        paper_object = self.papers_root / draft.paper_id
        if not paper_object.is_dir():
            raise FileNotFoundError(f"Paper Object does not exist: {paper_object}")
        output = paper_object / "knowledge" / "device_parameters.yaml"
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(draft.as_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        temporary.replace(output)
        return output
