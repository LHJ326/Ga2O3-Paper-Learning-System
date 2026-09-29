"""Load, query, and atomically update Registry v2 lifecycle state."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .registry_schema import (
    LIFECYCLE_FIELDS,
    LIFECYCLE_STATUS_VALUES,
    RegistrySchemaError,
    validate_registry,
)


class RegistryPaperNotFound(KeyError):
    pass


class RegistryManager:
    def __init__(self, path: str | Path = "data/papers/registry.yaml") -> None:
        self.path = Path(path)
        self._payload = self.load()

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            raise FileNotFoundError(f"registry does not exist: {self.path}")
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        return validate_registry(payload)

    @property
    def payload(self) -> dict[str, Any]:
        return deepcopy(self._payload)

    def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        for paper in self._payload["papers"]:
            if paper["paper_id"] == paper_id:
                return deepcopy(paper)
        return None

    def require_paper(self, paper_id: str) -> dict[str, Any]:
        paper = self.get_paper(paper_id)
        if paper is None:
            raise RegistryPaperNotFound(paper_id)
        return paper

    def update_status(
        self,
        paper_id: str,
        stage: str,
        status: str,
        *,
        save: bool = True,
    ) -> dict[str, Any]:
        if stage not in LIFECYCLE_FIELDS:
            raise RegistrySchemaError(f"unknown lifecycle stage: {stage}")
        if status not in LIFECYCLE_STATUS_VALUES:
            raise RegistrySchemaError(f"invalid lifecycle status: {status}")
        for paper in self._payload["papers"]:
            if paper["paper_id"] == paper_id:
                paper[stage] = status
                validate_registry(self._payload)
                if save:
                    self.save()
                return deepcopy(paper)
        raise RegistryPaperNotFound(paper_id)

    def pending_tasks(self, paper_id: str | None = None) -> list[dict[str, str]]:
        tasks: list[dict[str, str]] = []
        papers = self._payload["papers"]
        if paper_id is not None:
            papers = [paper for paper in papers if paper["paper_id"] == paper_id]
            if not papers:
                raise RegistryPaperNotFound(paper_id)
        for paper in papers:
            for stage in LIFECYCLE_FIELDS:
                if paper[stage] != "completed":
                    tasks.append({
                        "paper_id": paper["paper_id"],
                        "stage": stage,
                        "status": paper[stage],
                    })
        return tasks

    def completed_papers(self, *, stage: str = "object_status") -> list[dict[str, Any]]:
        if stage not in LIFECYCLE_FIELDS:
            raise RegistrySchemaError(f"unknown lifecycle stage: {stage}")
        return [
            deepcopy(paper) for paper in self._payload["papers"]
            if paper[stage] == "completed"
        ]

    def save(self) -> None:
        validate_registry(self._payload)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(self._payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        temporary.replace(self.path)
