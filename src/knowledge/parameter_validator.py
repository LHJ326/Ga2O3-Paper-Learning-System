"""Validate parameter structure, Evidence closure, pages, and units."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from .parameter_extractor import ParameterDraft
from .parameter_schema import ParameterSchema, REQUIRED_PARAMETER_FIELDS


@dataclass(frozen=True)
class ParameterValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class ParameterValidationResult:
    issues: tuple[ParameterValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def raise_if_invalid(self) -> None:
        if self.issues:
            raise ParameterValidationError(self.issues)


class ParameterValidationError(ValueError):
    def __init__(self, issues: Iterable[ParameterValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{issue.path}: {issue.message}" for issue in self.issues))


class ParameterValidator:
    def __init__(self, schema: ParameterSchema) -> None:
        self.schema = schema

    def validate(self, draft: ParameterDraft) -> ParameterValidationResult:
        issues: list[ParameterValidationIssue] = []
        if not draft.paper_id.strip():
            issues.append(ParameterValidationIssue("paper_id", "must be a non-empty string"))
        if draft.schema_version != self.schema.schema_version:
            issues.append(ParameterValidationIssue("schema_version", "does not match schema"))
        if draft.domain_id != self.schema.domain_id:
            issues.append(ParameterValidationIssue("domain_id", "does not match schema"))
        evidence_ids = self._validate_evidence(draft.evidence_index, issues)
        self._validate_parameters(draft.parameters, evidence_ids, issues)
        return ParameterValidationResult(tuple(issues))

    @staticmethod
    def _validate_evidence(
        evidence_index: Any,
        issues: list[ParameterValidationIssue],
    ) -> set[str]:
        if not isinstance(evidence_index, list):
            issues.append(ParameterValidationIssue("evidence_index", "must be a list"))
            return set()
        evidence_ids: set[str] = set()
        for position, item in enumerate(evidence_index):
            path = f"evidence_index[{position}]"
            if not isinstance(item, dict):
                issues.append(ParameterValidationIssue(path, "must be a mapping"))
                continue
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                issues.append(ParameterValidationIssue(f"{path}.evidence_id", "must be non-empty"))
            elif evidence_id in evidence_ids:
                issues.append(ParameterValidationIssue(f"{path}.evidence_id", "must be unique"))
            else:
                evidence_ids.add(evidence_id)
            page = item.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(ParameterValidationIssue(f"{path}.page", "must be a positive 1-based integer"))
            source = item.get("source_reference")
            if not isinstance(source, (str, dict)) or not source:
                issues.append(ParameterValidationIssue(f"{path}.source_reference", "must preserve source location"))
        return evidence_ids

    def _validate_parameters(
        self,
        parameters: Any,
        evidence_ids: set[str],
        issues: list[ParameterValidationIssue],
    ) -> None:
        if not isinstance(parameters, dict):
            issues.append(ParameterValidationIssue("parameters", "must be a mapping"))
            return
        for unknown in set(parameters) - set(REQUIRED_PARAMETER_FIELDS):
            issues.append(ParameterValidationIssue(f"parameters.{unknown}", "unknown section"))
        for section, required_fields in REQUIRED_PARAMETER_FIELDS.items():
            section_value = parameters.get(section)
            section_path = f"parameters.{section}"
            if not isinstance(section_value, dict):
                issues.append(ParameterValidationIssue(section_path, "must be a mapping"))
                continue
            for unknown in set(section_value) - set(required_fields):
                issues.append(ParameterValidationIssue(f"{section_path}.{unknown}", "unknown field"))
            for field in required_fields:
                field_path = f"{section_path}.{field}"
                if field not in section_value:
                    issues.append(ParameterValidationIssue(field_path, "required field is missing"))
                    continue
                self._validate_field(
                    section, field, section_value[field], field_path, evidence_ids, issues
                )

    def _validate_field(
        self,
        section: str,
        field: str,
        value: Any,
        path: str,
        evidence_ids: set[str],
        issues: list[ParameterValidationIssue],
    ) -> None:
        if value is None:
            return
        if isinstance(value, dict):
            entries = [value]
        elif isinstance(value, list):
            entries = value
            for position, item in enumerate(entries):
                if not isinstance(item, dict):
                    issues.append(ParameterValidationIssue(f"{path}[{position}]", "list entries must be mappings"))
        else:
            issues.append(ParameterValidationIssue(path, "must be null, a list, or a structured object"))
            return

        units: set[str] = set()
        for position, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            entry_path = path if isinstance(value, dict) else f"{path}[{position}]"
            refs = entry.get("evidence_refs")
            if not isinstance(refs, list) or not refs:
                issues.append(ParameterValidationIssue(f"{entry_path}.evidence_refs", "must be a non-empty list"))
            else:
                for ref_position, ref in enumerate(refs):
                    if not isinstance(ref, str) or ref not in evidence_ids:
                        issues.append(ParameterValidationIssue(
                            f"{entry_path}.evidence_refs[{ref_position}]", "references missing Evidence"
                        ))
            definition = self.schema.field_definition(section, field) or {}
            if definition.get("measurement") and entry.get("value") is not None:
                unit = entry.get("unit")
                if not isinstance(unit, str) or not unit.strip():
                    issues.append(ParameterValidationIssue(f"{entry_path}.unit", "measurement value requires a unit"))
                else:
                    units.add(re.sub(r"\s+", "", unit).casefold())
            elif "unit" in entry and entry["unit"] is not None and not isinstance(entry["unit"], str):
                issues.append(ParameterValidationIssue(f"{entry_path}.unit", "must be a string or null"))
        if len(units) > 1:
            issues.append(ParameterValidationIssue(path, "contains inconsistent units"))
