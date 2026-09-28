"""Validate performance structure, units, and Evidence location closure."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from .performance_schema import PERFORMANCE_FIELDS, PerformanceDraft, PerformanceSchema


@dataclass(frozen=True)
class PerformanceValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class PerformanceValidationWarning:
    field: str
    issue: str
    evidence_id: str


@dataclass(frozen=True)
class PerformanceValidationResult:
    issues: tuple[PerformanceValidationIssue, ...]
    warnings: tuple[PerformanceValidationWarning, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.issues

    @property
    def review_required(self) -> bool:
        return bool(self.warnings)

    def raise_if_invalid(self) -> None:
        if self.issues:
            raise PerformanceValidationError(self.issues)


class PerformanceValidationError(ValueError):
    def __init__(self, issues: tuple[PerformanceValidationIssue, ...]) -> None:
        self.issues = issues
        super().__init__("; ".join(f"{item.path}: {item.message}" for item in issues))


class PerformanceValidator:
    _REQUIRED = ("value", "unit", "evidence_id", "page", "source_type")
    _KEYWORDS = {
        "on_off_ratio": ("on/off ratio", "on off ratio", "switching ratio"),
        "responsivity": ("responsivity", "a/w"),
        "detectivity": ("detectivity", "jones"),
        "response_time": (
            "response time", "rise time", "decay time", "fall time", "temporal response"
        ),
    }

    def __init__(self, schema: PerformanceSchema) -> None:
        self.schema = schema

    def validate(self, draft: PerformanceDraft) -> PerformanceValidationResult:
        issues: list[PerformanceValidationIssue] = []
        warnings: list[PerformanceValidationWarning] = []
        if draft.schema_version != self.schema.schema_version:
            issues.append(PerformanceValidationIssue("schema_version", "does not match schema"))
        if draft.domain_id != self.schema.domain_id:
            issues.append(PerformanceValidationIssue("domain_id", "does not match schema"))
        if not isinstance(draft.paper_id, str) or not draft.paper_id.strip():
            issues.append(PerformanceValidationIssue("paper_id", "must be non-empty"))
        evidence = self._evidence_map(draft.evidence_index, issues)
        self._performance(draft.performance, evidence, issues, warnings)
        return PerformanceValidationResult(tuple(issues), tuple(warnings))

    @staticmethod
    def _evidence_map(
        records: Any, issues: list[PerformanceValidationIssue]
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(records, list):
            issues.append(PerformanceValidationIssue("evidence_index", "must be a list"))
            return {}
        result: dict[str, dict[str, Any]] = {}
        for index, record in enumerate(records):
            path = f"evidence_index[{index}]"
            if not isinstance(record, dict):
                issues.append(PerformanceValidationIssue(path, "must be a mapping"))
                continue
            evidence_id = record.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                issues.append(PerformanceValidationIssue(f"{path}.evidence_id", "must be non-empty"))
                continue
            if evidence_id in result:
                issues.append(PerformanceValidationIssue(f"{path}.evidence_id", "must be unique"))
            result[evidence_id] = record
            page = record.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(PerformanceValidationIssue(f"{path}.page", "must be 1-based"))
            if not isinstance(record.get("element_type"), str) or not record["element_type"]:
                issues.append(PerformanceValidationIssue(f"{path}.element_type", "must be non-empty"))
            if not record.get("source_reference"):
                issues.append(PerformanceValidationIssue(f"{path}.source_reference", "must be present"))
        return result

    def _performance(
        self,
        performance: Any,
        evidence: dict[str, dict[str, Any]],
        issues: list[PerformanceValidationIssue],
        warnings: list[PerformanceValidationWarning],
    ) -> None:
        if not isinstance(performance, dict):
            issues.append(PerformanceValidationIssue("performance", "must be a mapping"))
            return
        for unknown in set(performance) - set(PERFORMANCE_FIELDS):
            issues.append(PerformanceValidationIssue(f"performance.{unknown}", "unknown group"))
        for group, fields in PERFORMANCE_FIELDS.items():
            group_value = performance.get(group)
            group_path = f"performance.{group}"
            if not isinstance(group_value, dict):
                issues.append(PerformanceValidationIssue(group_path, "must be a mapping"))
                continue
            for unknown in set(group_value) - set(fields):
                issues.append(PerformanceValidationIssue(f"{group_path}.{unknown}", "unknown field"))
            for field in fields:
                path = f"{group_path}.{field}"
                if field not in group_value:
                    issues.append(PerformanceValidationIssue(path, "required field is missing"))
                    continue
                self._field(group_value[field], field, path, evidence, issues, warnings)

    def _field(
        self,
        value: Any,
        field: str,
        path: str,
        evidence: dict[str, dict[str, Any]],
        issues: list[PerformanceValidationIssue],
        warnings: list[PerformanceValidationWarning],
    ) -> None:
        if value is None:
            return
        entries = value if isinstance(value, list) else [value]
        if not isinstance(value, (dict, list)):
            issues.append(PerformanceValidationIssue(path, "must be null, object, or list"))
            return
        for index, entry in enumerate(entries):
            entry_path = path if isinstance(value, dict) else f"{path}[{index}]"
            if not isinstance(entry, dict):
                issues.append(PerformanceValidationIssue(entry_path, "must be a mapping"))
                continue
            for required in self._REQUIRED:
                if required not in entry:
                    issues.append(PerformanceValidationIssue(
                        f"{entry_path}.{required}", "required observation field is missing"
                    ))
            raw_value = entry.get("value")
            unit = entry.get("unit")
            if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                if not isinstance(unit, str) or not unit.strip():
                    issues.append(PerformanceValidationIssue(
                        f"{entry_path}.unit", "numeric value requires a unit"
                    ))
            elif unit is not None and not isinstance(unit, str):
                issues.append(PerformanceValidationIssue(f"{entry_path}.unit", "must be string or null"))
            evidence_id = entry.get("evidence_id")
            record = evidence.get(evidence_id) if isinstance(evidence_id, str) else None
            if record is None:
                issues.append(PerformanceValidationIssue(
                    f"{entry_path}.evidence_id", "references missing Evidence"
                ))
                continue
            page = entry.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(PerformanceValidationIssue(f"{entry_path}.page", "must be 1-based"))
            elif page != record.get("page"):
                issues.append(PerformanceValidationIssue(f"{entry_path}.page", "does not match Evidence"))
            source_type = entry.get("source_type")
            if not isinstance(source_type, str) or not source_type:
                issues.append(PerformanceValidationIssue(f"{entry_path}.source_type", "must be non-empty"))
            elif source_type != record.get("element_type"):
                issues.append(PerformanceValidationIssue(
                    f"{entry_path}.source_type", "does not match Evidence"
                ))
            warning = self._keyword_warning(field, entry, record)
            if warning is not None:
                warnings.append(warning)

    @classmethod
    def _keyword_warning(
        cls, field: str, entry: dict[str, Any], evidence: dict[str, Any]
    ) -> PerformanceValidationWarning | None:
        keywords = cls._KEYWORDS.get(field)
        if keywords is None:
            return None
        quote = evidence.get("quote")
        evidence_id = entry.get("evidence_id")
        if not isinstance(quote, str) or not isinstance(evidence_id, str):
            return PerformanceValidationWarning(
                field, "Evidence text is unavailable for keyword consistency check",
                str(evidence_id or ""),
            )
        normalized = re.sub(r"<[^>]+>", "", quote.casefold())
        normalized = re.sub(r"\s+", " ", normalized)
        context = normalized
        if field == "on_off_ratio" and entry.get("unit") == "%":
            context = cls._value_context(entry.get("value"), normalized, radius=80)
        if not any(keyword in context for keyword in keywords):
            return PerformanceValidationWarning(
                field,
                "Evidence keywords are inconsistent with the extracted field",
                evidence_id,
            )
        return None

    @staticmethod
    def _value_context(value: Any, quote: str, *, radius: int = 80) -> str:
        # A distinctive numeric token ties a value to its nearby caption/text
        # clause. This catches a metric appearing elsewhere in a long figure
        # caption without pretending to understand or rewrite the observation.
        tokens = re.findall(r"\d+(?:\.\d+)?", str(value))
        distinctive = [token for token in tokens if len(token) >= 2 or "." in token]
        if len(distinctive) == 1:
            position = quote.find(distinctive[0])
            if position >= 0:
                return quote[max(0, position - radius):position + len(distinctive[0]) + radius]
        return quote
