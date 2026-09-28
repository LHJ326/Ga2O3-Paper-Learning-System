"""Validate Knowledge drafts, types, and closed Evidence references."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .extractor import KnowledgeDraft
from .schema import CORE_FIELDS, KnowledgeSchema


_CLAIM_FIELDS = {
    "research_problem": "statement",
    "methodology": "description",
    "results": "claim",
    "innovation": "claim",
    "limitations": "statement",
}
_ELEMENT_TYPES = {"Section", "TextBlock", "Figure", "Table", "Equation"}


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def raise_if_invalid(self) -> None:
        if self.issues:
            raise KnowledgeValidationError(self.issues)


class KnowledgeValidationError(ValueError):
    def __init__(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        message = "; ".join(f"{item.path}: {item.message}" for item in self.issues)
        super().__init__(message)


class KnowledgeValidator:
    def __init__(self, schema: KnowledgeSchema) -> None:
        self.schema = schema

    def validate(self, draft: KnowledgeDraft) -> ValidationResult:
        issues: list[ValidationIssue] = []
        core = draft.core
        if not isinstance(core, dict):
            return ValidationResult((ValidationIssue("core", "must be a mapping"),))
        for field in CORE_FIELDS:
            if field not in core:
                issues.append(ValidationIssue(f"core.{field}", "required field is missing"))

        identity = core.get("paper_identity")
        if not isinstance(identity, dict):
            issues.append(ValidationIssue("core.paper_identity", "must be a mapping"))
        elif identity.get("paper_id") != draft.paper_id:
            issues.append(ValidationIssue("core.paper_identity.paper_id", "must match draft paper_id"))

        evidence_ids = self._validate_evidence(core, issues)
        for section, required_text in _CLAIM_FIELDS.items():
            self._validate_claim_list(
                core.get(section), f"core.{section}", required_text, evidence_ids, issues
            )
        self._validate_domain(draft, evidence_ids, issues)
        return ValidationResult(tuple(issues))

    @staticmethod
    def _validate_evidence(
        core: dict[str, Any], issues: list[ValidationIssue]
    ) -> set[str]:
        traceability = core.get("evidence_traceability")
        if not isinstance(traceability, dict):
            issues.append(ValidationIssue("core.evidence_traceability", "must be a mapping"))
            return set()
        index = traceability.get("evidence_index")
        if not isinstance(index, list):
            issues.append(ValidationIssue("core.evidence_traceability.evidence_index", "must be a list"))
            return set()
        evidence_ids: set[str] = set()
        for position, item in enumerate(index):
            path = f"core.evidence_traceability.evidence_index[{position}]"
            if not isinstance(item, dict):
                issues.append(ValidationIssue(path, "must be a mapping"))
                continue
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                issues.append(ValidationIssue(f"{path}.evidence_id", "must be a non-empty string"))
            elif evidence_id in evidence_ids:
                issues.append(ValidationIssue(f"{path}.evidence_id", "must be unique"))
            else:
                evidence_ids.add(evidence_id)
            if not isinstance(item.get("element_id"), str) or not item.get("element_id"):
                issues.append(ValidationIssue(f"{path}.element_id", "must be a non-empty string"))
            if item.get("element_type") not in _ELEMENT_TYPES:
                issues.append(ValidationIssue(f"{path}.element_type", "is not a supported element type"))
            page = item.get("page")
            if not isinstance(page, int) or isinstance(page, bool) or page < 1:
                issues.append(ValidationIssue(f"{path}.page", "must be a positive 1-based integer"))
            if not isinstance(item.get("source_reference"), (str, dict)):
                issues.append(ValidationIssue(f"{path}.source_reference", "must be a string or mapping"))
        return evidence_ids

    @staticmethod
    def _validate_refs(
        refs: Any, path: str, evidence_ids: set[str], issues: list[ValidationIssue]
    ) -> None:
        if not isinstance(refs, list) or not refs:
            issues.append(ValidationIssue(path, "must be a non-empty list"))
            return
        for position, ref in enumerate(refs):
            if not isinstance(ref, str) or ref not in evidence_ids:
                issues.append(ValidationIssue(f"{path}[{position}]", "references missing evidence"))

    def _validate_claim_list(
        self, value: Any, path: str, text_field: str, evidence_ids: set[str],
        issues: list[ValidationIssue],
    ) -> None:
        if not isinstance(value, list):
            issues.append(ValidationIssue(path, "must be a list"))
            return
        for position, item in enumerate(value):
            item_path = f"{path}[{position}]"
            if not isinstance(item, dict):
                issues.append(ValidationIssue(item_path, "must be a mapping"))
                continue
            if not isinstance(item.get(text_field), str) or not item.get(text_field, "").strip():
                issues.append(ValidationIssue(f"{item_path}.{text_field}", "must be a non-empty string"))
            self._validate_refs(
                item.get("evidence_refs"), f"{item_path}.evidence_refs", evidence_ids, issues
            )

    def _validate_domain(
        self, draft: KnowledgeDraft, evidence_ids: set[str], issues: list[ValidationIssue]
    ) -> None:
        domain = draft.domain
        if not isinstance(domain, dict):
            issues.append(ValidationIssue("domain", "must be a mapping"))
            return
        if domain.get("paper_id") != draft.paper_id:
            issues.append(ValidationIssue("domain.paper_id", "must match draft paper_id"))
        if self.schema.domain_id is not None and domain.get("domain_id") != self.schema.domain_id:
            issues.append(ValidationIssue("domain.domain_id", "does not match loaded extension"))
        fields = domain.get("fields")
        if not isinstance(fields, dict):
            issues.append(ValidationIssue("domain.fields", "must be a mapping"))
            return
        definitions = self.schema.domain_fields
        for name, value in fields.items():
            path = f"domain.fields.{name}"
            definition = definitions.get(name)
            if definition is None:
                issues.append(ValidationIssue(path, "is not defined by the Domain Extension"))
                continue
            if value is None:
                continue
            expected = definition.get("type")
            if expected == "structured" and not isinstance(value, dict):
                issues.append(ValidationIssue(path, "must be a mapping or null"))
            elif expected in {"list", "measurements", "claims"} and not isinstance(value, list):
                issues.append(ValidationIssue(path, "must be a list or null"))
            self._validate_nested_refs(value, path, evidence_ids, issues)

    def _validate_nested_refs(
        self, value: Any, path: str, evidence_ids: set[str], issues: list[ValidationIssue]
    ) -> None:
        if isinstance(value, dict):
            if "evidence_refs" in value:
                self._validate_refs(
                    value["evidence_refs"], f"{path}.evidence_refs", evidence_ids, issues
                )
            for key, nested in value.items():
                if key != "evidence_refs":
                    self._validate_nested_refs(nested, f"{path}.{key}", evidence_ids, issues)
        elif isinstance(value, list):
            for position, nested in enumerate(value):
                self._validate_nested_refs(nested, f"{path}[{position}]", evidence_ids, issues)
