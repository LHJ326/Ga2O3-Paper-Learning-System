"""Strict validation for B1 Material/Device extraction output."""

from __future__ import annotations

from .parameter_extractor import ParameterDraft
from .parameter_schema import ParameterSchema
from .parameter_validator import (
    ParameterValidationIssue,
    ParameterValidationResult,
    ParameterValidator,
)


class MaterialDeviceValidator:
    def __init__(self, parameter_schema: ParameterSchema) -> None:
        self.parameter_validator = ParameterValidator(parameter_schema)

    def validate(self, draft: ParameterDraft) -> ParameterValidationResult:
        issues = list(self.parameter_validator.validate(draft).issues)
        for section in ("performance", "mechanism", "comparison"):
            value = draft.parameters.get(section, {})
            if isinstance(value, dict):
                for field, item in value.items():
                    if item is not None:
                        issues.append(ParameterValidationIssue(
                            f"parameters.{section}.{field}",
                            "must remain null during Material/Device extraction",
                        ))
        for position, item in enumerate(draft.evidence_index):
            if not isinstance(item, dict):
                continue
            path = f"evidence_index[{position}]"
            if not isinstance(item.get("element_type"), str) or not item["element_type"]:
                issues.append(ParameterValidationIssue(
                    f"{path}.element_type", "must identify the source element type"
                ))
            if not isinstance(item.get("quote"), str) or not item["quote"].strip():
                issues.append(ParameterValidationIssue(
                    f"{path}.quote", "must preserve source evidence text"
                ))
        return ParameterValidationResult(tuple(issues))
