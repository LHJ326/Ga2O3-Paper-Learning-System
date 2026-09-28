"""Validate mechanism structure and Evidence closure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .mechanism_schema import MECHANISM_FIELDS, MechanismDraft, MechanismSchema


@dataclass(frozen=True)
class MechanismValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class MechanismValidationResult:
    issues: tuple[MechanismValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def raise_if_invalid(self) -> None:
        if self.issues:
            raise MechanismValidationError(self.issues)


class MechanismValidationError(ValueError):
    def __init__(self, issues: tuple[MechanismValidationIssue, ...]) -> None:
        self.issues = issues
        super().__init__("; ".join(f"{item.path}: {item.message}" for item in issues))


class MechanismValidator:
    _REQUIRED = ("value", "evidence_id", "page", "source_type", "confidence", "review_status")
    _STATUSES = frozenset({"unreviewed", "review_required"})

    def __init__(self, schema: MechanismSchema) -> None:
        self.schema = schema

    def validate(self, draft: MechanismDraft) -> MechanismValidationResult:
        issues: list[MechanismValidationIssue] = []
        if draft.schema_version != self.schema.schema_version:
            issues.append(MechanismValidationIssue("schema_version", "does not match schema"))
        if draft.domain_id != self.schema.domain_id:
            issues.append(MechanismValidationIssue("domain_id", "does not match schema"))
        if not draft.paper_id.strip():
            issues.append(MechanismValidationIssue("paper_id", "must be non-empty"))
        evidence = self._evidence(draft.evidence_index, issues)
        if not isinstance(draft.mechanisms, dict):
            issues.append(MechanismValidationIssue("mechanisms", "must be a mapping"))
            return MechanismValidationResult(tuple(issues))
        for unknown in set(draft.mechanisms) - set(MECHANISM_FIELDS):
            issues.append(MechanismValidationIssue(f"mechanisms.{unknown}", "unknown field"))
        for field in MECHANISM_FIELDS:
            path = f"mechanisms.{field}"
            if field not in draft.mechanisms:
                issues.append(MechanismValidationIssue(path, "required field is missing"))
                continue
            self._field(draft.mechanisms[field], path, evidence, issues)
        return MechanismValidationResult(tuple(issues))

    @staticmethod
    def _evidence(
        records: Any, issues: list[MechanismValidationIssue]
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(records, list):
            issues.append(MechanismValidationIssue("evidence_index", "must be a list"))
            return {}
        result: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(records):
            path = f"evidence_index[{index}]"
            if not isinstance(record, dict):
                issues.append(MechanismValidationIssue(path, "must be a mapping"))
                continue
            evidence_id = record.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                issues.append(MechanismValidationIssue(f"{path}.evidence_id", "must be non-empty"))
                continue
            result[evidence_id] = record
            page = record.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(MechanismValidationIssue(f"{path}.page", "must be 1-based"))
            if not isinstance(record.get("element_type"), str) or not record["element_type"]:
                issues.append(MechanismValidationIssue(f"{path}.element_type", "must be non-empty"))
            if not record.get("source_reference"):
                issues.append(MechanismValidationIssue(f"{path}.source_reference", "must be present"))
        return result

    def _field(
        self, value: Any, path: str, evidence: dict[str, dict[str, Any]],
        issues: list[MechanismValidationIssue],
    ) -> None:
        if value is None:
            return
        if not isinstance(value, (dict, list)):
            issues.append(MechanismValidationIssue(path, "must be null, object, or list"))
            return
        entries = value if isinstance(value, list) else [value]
        for index, entry in enumerate(entries):
            entry_path = path if isinstance(value, dict) else f"{path}[{index}]"
            if not isinstance(entry, dict):
                issues.append(MechanismValidationIssue(entry_path, "must be a mapping"))
                continue
            for key in self._REQUIRED:
                if key not in entry:
                    issues.append(MechanismValidationIssue(
                        f"{entry_path}.{key}", "required observation field is missing"
                    ))
            if not isinstance(entry.get("value"), str) or not entry.get("value", "").strip():
                issues.append(MechanismValidationIssue(f"{entry_path}.value", "must be non-empty text"))
            confidence = entry.get("confidence")
            if (
                not isinstance(confidence, (int, float)) or isinstance(confidence, bool)
                or not 0 <= confidence <= 1
            ):
                issues.append(MechanismValidationIssue(
                    f"{entry_path}.confidence", "must be a number from 0 to 1"
                ))
            if entry.get("review_status") not in self._STATUSES:
                issues.append(MechanismValidationIssue(
                    f"{entry_path}.review_status", "must be unreviewed or review_required"
                ))
            evidence_id = entry.get("evidence_id")
            record = evidence.get(evidence_id) if isinstance(evidence_id, str) else None
            if record is None:
                issues.append(MechanismValidationIssue(
                    f"{entry_path}.evidence_id", "references missing or unsupported Evidence"
                ))
                continue
            page = entry.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(MechanismValidationIssue(f"{entry_path}.page", "must be 1-based"))
            elif page != record.get("page"):
                issues.append(MechanismValidationIssue(f"{entry_path}.page", "does not match Evidence"))
            source_type = entry.get("source_type")
            if not isinstance(source_type, str) or not source_type:
                issues.append(MechanismValidationIssue(f"{entry_path}.source_type", "must be non-empty"))
            elif source_type != record.get("element_type"):
                issues.append(MechanismValidationIssue(
                    f"{entry_path}.source_type", "does not match Evidence"
                ))
