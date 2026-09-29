"""Explicit Domain Profile and extraction-task selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.task_adapter import TaskAdapter, TaskAdapterLoader, TaskRegistry

from .model import DomainProfile
from .registry import DomainProfileRegistry


class DomainSelectionError(ValueError):
    """Raised when no complete, explicit profile selection is available."""


@dataclass(frozen=True, slots=True)
class DomainProfileSelection:
    profile_id: str
    profile_version: str


@dataclass(frozen=True, slots=True)
class SelectedDomainTask:
    source: str
    profile: DomainProfile
    adapter: TaskAdapter


class DomainTaskSelector:
    """Select explicit configuration first, then an explicit Registry value."""

    def __init__(
        self,
        domain_registry: DomainProfileRegistry,
        *,
        task_registry: TaskRegistry | None = None,
    ) -> None:
        self.domain_registry = domain_registry
        self.adapter_loader = TaskAdapterLoader(task_registry)

    def select(
        self,
        task_id: str,
        *,
        explicit: DomainProfileSelection | Mapping[str, Any] | None = None,
        paper_record: Mapping[str, Any] | None = None,
    ) -> SelectedDomainTask:
        if explicit is not None:
            selection = self._selection(explicit, source="explicit configuration")
            source = "explicit"
        elif paper_record is not None and "domain_profile" in paper_record:
            selection = self._selection(
                paper_record["domain_profile"], source="Registry domain_profile"
            )
            source = "registry"
        else:
            raise DomainSelectionError(
                "Domain Profile selection is required; implicit fallback is disabled"
            )

        profile = self.domain_registry.load_profile(
            selection.profile_id, selection.profile_version
        )
        adapter = self.adapter_loader.load(profile, task_id)
        return SelectedDomainTask(source=source, profile=profile, adapter=adapter)

    def select_for_paper(
        self,
        registry_manager: Any,
        paper_id: str,
        task_id: str,
        *,
        explicit: DomainProfileSelection | Mapping[str, Any] | None = None,
    ) -> SelectedDomainTask:
        paper_record = registry_manager.require_paper(paper_id)
        return self.select(task_id, explicit=explicit, paper_record=paper_record)

    @staticmethod
    def _selection(value: Any, *, source: str) -> DomainProfileSelection:
        if isinstance(value, DomainProfileSelection):
            selection = value
        elif isinstance(value, Mapping):
            profile_id = value.get("profile_id")
            version = value.get("profile_version")
            if not isinstance(profile_id, str) or not profile_id:
                raise DomainSelectionError(f"{source} requires profile_id")
            if not isinstance(version, str) or not version:
                raise DomainSelectionError(f"{source} requires profile_version")
            selection = DomainProfileSelection(profile_id, version)
        else:
            raise DomainSelectionError(f"{source} must be a mapping")
        if not selection.profile_id or not selection.profile_version:
            raise DomainSelectionError(f"{source} must pin profile ID and version")
        return selection
