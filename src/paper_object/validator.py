"""Validate Paper Object structure and Evidence traceability."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Iterable
from .schema import PaperObjectSchema, REQUIRED_SECTIONS

@dataclass(frozen=True)
class PaperObjectValidationIssue:
    path: str
    message: str

@dataclass(frozen=True)
class PaperObjectValidationResult:
    issues: tuple[PaperObjectValidationIssue, ...]
    @property
    def valid(self) -> bool:
        return not self.issues
    def raise_if_invalid(self) -> None:
        if self.issues:
            raise PaperObjectValidationError(self.issues)

class PaperObjectValidationError(ValueError):
    def __init__(self, issues: Iterable[PaperObjectValidationIssue]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(f"{i.path}: {i.message}" for i in self.issues))

class PaperObjectValidator:
    def __init__(self, schema: PaperObjectSchema) -> None:
        self.schema = schema

    def validate(self, payload: Any) -> PaperObjectValidationResult:
        issues: list[PaperObjectValidationIssue] = []
        if not isinstance(payload, dict):
            return PaperObjectValidationResult((PaperObjectValidationIssue("$", "must be a mapping"),))
        if payload.get("schema_version") != self.schema.schema_version:
            issues.append(PaperObjectValidationIssue("schema_version", "does not match schema"))
        if payload.get("object_type") != self.schema.object_type:
            issues.append(PaperObjectValidationIssue("object_type", "does not match schema"))
        for section, fields in REQUIRED_SECTIONS.items():
            value = payload.get(section)
            if not isinstance(value, dict):
                issues.append(PaperObjectValidationIssue(section, "must be a mapping"))
                continue
            for field in fields:
                if field not in value:
                    issues.append(PaperObjectValidationIssue(f"{section}.{field}", "required field is missing"))
        identity = payload.get("paper_identity", {})
        if isinstance(identity, dict) and not isinstance(identity.get("paper_id"), str):
            issues.append(PaperObjectValidationIssue("paper_identity.paper_id", "must be a string"))
        knowledge = payload.get("knowledge", {})
        if isinstance(knowledge, dict):
            if not isinstance(knowledge.get("summary"), str):
                issues.append(PaperObjectValidationIssue("knowledge.summary", "must be Markdown text"))
            for field in ("parameters", "performance", "mechanism"):
                if not isinstance(knowledge.get(field), dict):
                    issues.append(PaperObjectValidationIssue(f"knowledge.{field}", "must be a mapping"))
        evidence_ids = self._validate_evidence(payload.get("source", {}), issues)
        for evidence_id in sorted(self.collect_references(knowledge) - evidence_ids):
            issues.append(PaperObjectValidationIssue("source.evidence_index",
                                                     f"missing referenced Evidence {evidence_id}"))
        validation = payload.get("validation", {})
        if isinstance(validation, dict):
            coverage = validation.get("evidence_coverage")
            if not isinstance(coverage, (int, float)) or isinstance(coverage, bool) or not 0 <= coverage <= 1:
                issues.append(PaperObjectValidationIssue("validation.evidence_coverage", "must be 0 to 1"))
            if not isinstance(validation.get("warnings"), list):
                issues.append(PaperObjectValidationIssue("validation.warnings", "must be a list"))
            if validation.get("review_status") not in self.schema.review_status_values:
                issues.append(PaperObjectValidationIssue("validation.review_status", "is not allowed"))
        return PaperObjectValidationResult(tuple(issues))

    @staticmethod
    def _validate_evidence(source: Any, issues: list[PaperObjectValidationIssue]) -> set[str]:
        if not isinstance(source, dict):
            return set()
        records = source.get("evidence_index")
        if not isinstance(records, list):
            issues.append(PaperObjectValidationIssue("source.evidence_index", "must be a list"))
            return set()
        ids: set[str] = set()
        for index, record in enumerate(records):
            path = f"source.evidence_index[{index}]"
            if not isinstance(record, dict):
                issues.append(PaperObjectValidationIssue(path, "must be a mapping")); continue
            for field in ("evidence_id", "page", "element_type", "source_reference", "quote"):
                if field not in record:
                    issues.append(PaperObjectValidationIssue(f"{path}.{field}", "required field is missing"))
            evidence_id = record.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                issues.append(PaperObjectValidationIssue(f"{path}.evidence_id", "must be non-empty"))
            elif evidence_id in ids:
                issues.append(PaperObjectValidationIssue(f"{path}.evidence_id", "must be unique"))
            else:
                ids.add(evidence_id)
            page = record.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(PaperObjectValidationIssue(f"{path}.page", "must be 1-based"))
            if not isinstance(record.get("element_type"), str) or not record.get("element_type"):
                issues.append(PaperObjectValidationIssue(f"{path}.element_type", "must be non-empty"))
            if not record.get("source_reference"):
                issues.append(PaperObjectValidationIssue(f"{path}.source_reference", "must be present"))
        return ids

    @classmethod
    def collect_references(cls, value: Any) -> set[str]:
        refs: set[str] = set()
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "evidence_id" and isinstance(item, str): refs.add(item)
                elif key == "evidence_refs" and isinstance(item, list):
                    refs.update(ref for ref in item if isinstance(ref, str))
                else: refs.update(cls.collect_references(item))
        elif isinstance(value, list):
            for item in value: refs.update(cls.collect_references(item))
        elif isinstance(value, str): refs.update(re.findall(r"\bE\d{5}\b", value))
        return refs
