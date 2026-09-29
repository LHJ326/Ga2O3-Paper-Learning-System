"""Resolve registered extraction tasks against a loaded Domain Profile."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from src.domain_profiles.model import DomainProfile

from .model import TaskAdapter, TaskAdapterLoadError, TaskRegistration, freeze
from .registry import TaskRegistry, build_default_task_registry


class TaskAdapterLoader:
    """Build immutable adapters without changing existing extraction pipelines."""

    def __init__(self, registry: TaskRegistry | None = None) -> None:
        self.registry = registry or build_default_task_registry()

    def load(self, profile: DomainProfile, task_id: str) -> TaskAdapter:
        registration = self.registry.get(task_id)
        self._validate_profile_identity(profile)
        task_rules = self._mapping_at(profile.extraction_rules, "tasks", task_id)
        output_schema = self._output_schema(profile, registration)
        artifact_path = self._artifact_path(profile, registration)
        selected_validation = self._validation_rules(profile, registration)
        policies = self._mapping_at(profile.extraction_rules, "policies")
        if policies.get("evidence_only") is not True:
            raise TaskAdapterLoadError("task profile must require Evidence-only extraction")
        if policies.get("prohibit_external_knowledge") is not True:
            raise TaskAdapterLoadError("task profile must prohibit external knowledge")
        if "unknown_value" not in policies or policies["unknown_value"] is not None:
            raise TaskAdapterLoadError("task profile unknown_value must be null")

        fingerprint = self._fingerprint(
            profile.fingerprint,
            registration,
            task_rules,
            output_schema,
            selected_validation,
            artifact_path,
        )
        return TaskAdapter(
            task_id=task_id,
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            profile_fingerprint=profile.fingerprint,
            adapter_fingerprint=fingerprint,
            artifact_key=registration.artifact_key,
            artifact_path=artifact_path,
            artifact_format=registration.artifact_format,
            output_schema=freeze(output_schema),
            extraction_rules=freeze(task_rules),
            validation_rules=freeze(selected_validation),
            evidence_only=True,
            prohibit_external_knowledge=True,
            unknown_value=None,
        )

    @staticmethod
    def _validate_profile_identity(profile: DomainProfile) -> None:
        for asset_name, asset in (
            ("schema", profile.schema),
            ("extraction rules", profile.extraction_rules),
            ("validation rules", profile.validation_rules),
        ):
            if asset.get("profile_id") != profile.profile_id:
                raise TaskAdapterLoadError(f"{asset_name} profile_id does not match manifest")

    @classmethod
    def _output_schema(
        cls, profile: DomainProfile, registration: TaskRegistration
    ) -> Mapping[str, Any]:
        if registration.schema_key is not None:
            return cls._mapping_at(profile.schema, registration.schema_key)
        return {
            "required_sections": cls._mapping_at(
                profile.validation_rules, "summary", "required_sections"
            )
        }

    @classmethod
    def _artifact_path(
        cls, profile: DomainProfile, registration: TaskRegistration
    ) -> str:
        compatibility = cls._mapping_at(profile.extraction_rules, "compatibility")
        artifacts = cls._mapping_at(compatibility, "legacy_artifacts")
        value = artifacts.get(registration.artifact_key)
        if not isinstance(value, str) or not value:
            raise TaskAdapterLoadError(
                f"profile has no artifact for task: {registration.task_id}"
            )
        return value

    @classmethod
    def _validation_rules(
        cls, profile: DomainProfile, registration: TaskRegistration
    ) -> dict[str, Any]:
        selected: dict[str, Any] = {
            "policies": cls._mapping_at(profile.validation_rules, "policies")
        }
        for key in registration.validation_rule_keys:
            selected[key] = cls._mapping_at(profile.validation_rules, key)
        return selected

    @staticmethod
    def _mapping_at(root: Mapping[str, Any], *keys: str) -> Mapping[str, Any]:
        current: Any = root
        for key in keys:
            if not isinstance(current, Mapping) or key not in current:
                raise TaskAdapterLoadError(f"profile mapping is missing: {'.'.join(keys)}")
            current = current[key]
        if not isinstance(current, Mapping):
            raise TaskAdapterLoadError(f"profile value must be a mapping: {'.'.join(keys)}")
        return current

    @staticmethod
    def _fingerprint(*values: Any) -> str:
        canonical = json.dumps(values, default=str, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_task_adapter(
    profile: DomainProfile,
    task_id: str,
    *,
    registry: TaskRegistry | None = None,
) -> TaskAdapter:
    return TaskAdapterLoader(registry).load(profile, task_id)
