"""Immutable contracts for profile-driven extraction tasks."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping


class TaskAdapterError(ValueError):
    """Base error for task registration, loading, or Evidence binding."""


class TaskRegistrationError(TaskAdapterError):
    """Raised when a task registration is invalid or duplicated."""


class TaskAdapterLoadError(TaskAdapterError):
    """Raised when a profile cannot satisfy a registered task contract."""


class TaskEvidenceError(TaskAdapterError):
    """Raised when task Evidence would lose traceability."""


def freeze(value: Any) -> Any:
    """Recursively copy and freeze YAML-compatible values."""

    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze(child) for key, child in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(child) for child in value)
    return value


@dataclass(frozen=True, slots=True)
class TaskRegistration:
    """Trusted Python-side mapping between a task and profile assets."""

    task_id: str
    schema_key: str | None
    artifact_key: str
    artifact_format: str
    validation_rule_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskRequest:
    """Evidence-preserving input prepared for a downstream extractor."""

    task_id: str
    profile_id: str
    profile_version: str
    adapter_fingerprint: str
    evidence: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True, slots=True)
class TaskAdapter:
    """Resolved connection between one Domain Profile and one task."""

    task_id: str
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    adapter_fingerprint: str
    artifact_key: str
    artifact_path: str
    artifact_format: str
    output_schema: Mapping[str, Any]
    extraction_rules: Mapping[str, Any]
    validation_rules: Mapping[str, Any]
    evidence_only: bool
    prohibit_external_knowledge: bool
    unknown_value: Any

    def bind_evidence(self, records: Iterable[Mapping[str, Any]]) -> TaskRequest:
        """Validate identity/page basics and retain every Evidence field unchanged."""

        bound: list[Mapping[str, Any]] = []
        seen: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                raise TaskEvidenceError(f"Evidence item {index} must be a mapping")
            evidence_id = record.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                raise TaskEvidenceError(f"Evidence item {index} has no evidence_id")
            if evidence_id in seen:
                raise TaskEvidenceError(f"duplicate Evidence ID: {evidence_id}")
            page = record.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                raise TaskEvidenceError(f"Evidence {evidence_id} requires a 1-based page")
            seen.add(evidence_id)
            bound.append(freeze(record))
        if not bound:
            raise TaskEvidenceError("Evidence-only task requires at least one Evidence item")
        return TaskRequest(
            task_id=self.task_id,
            profile_id=self.profile_id,
            profile_version=self.profile_version,
            adapter_fingerprint=self.adapter_fingerprint,
            evidence=tuple(bound),
        )
