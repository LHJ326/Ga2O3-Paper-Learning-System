"""Atomically persist validated performance knowledge."""

from __future__ import annotations

from pathlib import Path

import yaml

from .performance_schema import PerformanceDraft
from .performance_validator import PerformanceValidator


class PerformanceWriter:
    def __init__(
        self, *, validator: PerformanceValidator, papers_root: str | Path = "data/papers"
    ) -> None:
        self.validator = validator
        self.papers_root = Path(papers_root)

    def write(self, draft: PerformanceDraft) -> Path:
        self.validator.validate(draft).raise_if_invalid()
        paper = self.papers_root / draft.paper_id
        if not paper.is_dir():
            raise FileNotFoundError(f"Paper Object does not exist: {paper}")
        output = paper / "knowledge" / "performance.yaml"
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(draft.as_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        temporary.replace(output)
        return output
