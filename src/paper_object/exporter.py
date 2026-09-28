"""Atomically export validated Paper Objects."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from .validator import PaperObjectValidator

class PaperObjectExporter:
    def __init__(self, *, validator: PaperObjectValidator) -> None:
        self.validator = validator
    def export(self, payload: dict[str, Any], path: str | Path) -> Path:
        self.validator.validate(payload).raise_if_invalid()
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                             encoding="utf-8")
        temporary.replace(output)
        return output
