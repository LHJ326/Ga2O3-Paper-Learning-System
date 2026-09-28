"""Persist validated knowledge artifacts into one Paper Object."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .extractor import KnowledgeDraft
from .validator import KnowledgeValidator


class KnowledgeWriter:
    def __init__(self, *, validator: KnowledgeValidator, papers_root: str | Path = "data/papers") -> None:
        self.validator = validator
        self.papers_root = Path(papers_root)

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
        temporary.replace(path)

    @classmethod
    def _write_yaml(cls, path: Path, payload: dict[str, Any]) -> None:
        cls._write_text(
            path,
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        )

    def write(self, draft: KnowledgeDraft) -> dict[str, Path]:
        """Validate first, then write structured records and requested views."""
        self.validator.validate(draft).raise_if_invalid()
        object_path = self.papers_root / draft.paper_id
        if not object_path.is_dir():
            raise FileNotFoundError(f"Paper Object does not exist: {object_path}")
        knowledge_path = object_path / "knowledge"
        knowledge_path.mkdir(parents=True, exist_ok=True)
        device_parameters = {
            "schema_version": draft.domain.get("schema_version", "1.0"),
            "paper_id": draft.paper_id,
            "domain_id": draft.domain.get("domain_id"),
            "parameters": draft.domain.get("fields", {}),
        }
        paths = {
            "core": knowledge_path / "core.yaml",
            "domain": knowledge_path / "domain.yaml",
            "summary": knowledge_path / "summary.md",
            "key_points": knowledge_path / "key_points.md",
            "device_parameters": knowledge_path / "device_parameters.yaml",
        }
        self._write_yaml(paths["core"], draft.core)
        self._write_yaml(paths["domain"], draft.domain)
        self._write_text(paths["summary"], draft.summary)
        self._write_text(paths["key_points"], draft.key_points)
        self._write_yaml(paths["device_parameters"], device_parameters)
        return paths
