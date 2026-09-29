"""Resolve batch readiness from lifecycle status with legacy artifact fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .scanner import PaperCandidate


REQUIRED_KNOWLEDGE_FILES = (
    "summary.md", "device_parameters.yaml", "performance.yaml", "mechanism.yaml"
)


@dataclass(frozen=True)
class PaperProcessingState:
    paper_id: str
    metadata_ready: bool
    knowledge_ready: bool
    paper_object_ready: bool
    status_path: Path | None
    missing_knowledge_files: tuple[str, ...]


class PaperStatusTracker:
    def __init__(
        self,
        *,
        metadata_root: str | Path = "data/metadata",
    ) -> None:
        self.metadata_root = Path(metadata_root)

    def inspect(self, candidate: PaperCandidate) -> PaperProcessingState:
        status_path = candidate.object_dir / "status.yaml"
        status = self._load_status(status_path) if status_path.is_file() else {}
        metadata_artifact = self.metadata_root / f"{candidate.paper_id}.yaml"
        metadata_ready = self._status_value(status.get("metadata_ready"))
        if "metadata_ready" not in status:
            metadata_ready = metadata_artifact.is_file()

        knowledge_dir = candidate.object_dir / "knowledge"
        missing = tuple(
            name for name in REQUIRED_KNOWLEDGE_FILES
            if not (knowledge_dir / name).is_file()
        )
        artifact_ready = not missing
        knowledge_ready = self._status_value(status.get("knowledge_ready"))
        if "knowledge_ready" not in status:
            knowledge_ready = artifact_ready
        else:
            knowledge_ready = knowledge_ready and artifact_ready
        return PaperProcessingState(
            candidate.paper_id,
            metadata_ready,
            knowledge_ready,
            (candidate.object_dir / "paper_object.yaml").is_file(),
            status_path if status_path.is_file() else None,
            missing,
        )

    @staticmethod
    def _status_value(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.casefold() in {"true", "ready", "completed", "complete"}
        return False

    @staticmethod
    def _load_status(path: Path) -> dict[str, Any]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
