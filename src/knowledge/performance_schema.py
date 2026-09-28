"""Schema and draft contracts for performance extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .parameter_schema import PROJECT_ROOT


DEFAULT_PERFORMANCE_SCHEMA = (
    PROJECT_ROOT / "data" / "domains" / "semiconductor" / "ga2o3"
    / "performance_schema.yaml"
)
PERFORMANCE_FIELDS = {
    "optical_performance": (
        "detection_wavelength", "responsivity", "detectivity",
        "external_quantum_efficiency", "spectral_response_range",
    ),
    "electrical_performance": (
        "photocurrent", "dark_current", "on_off_ratio", "bias_voltage",
    ),
    "dynamic_performance": ("rise_time", "decay_time", "response_time"),
    "stability": (
        "operation_time", "cycle_stability", "environmental_stability",
    ),
}


class PerformanceSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class PerformanceSchema:
    schema_version: str
    domain_id: str
    groups: dict[str, dict[str, dict[str, Any]]]
    observation_contract: dict[str, Any]
    source_path: Path

    def new_performance(self) -> dict[str, dict[str, Any]]:
        return {
            group: {field: None for field in fields}
            for group, fields in PERFORMANCE_FIELDS.items()
        }


@dataclass(frozen=True)
class PerformanceDraft:
    schema_version: str
    paper_id: str
    domain_id: str
    performance: dict[str, dict[str, Any]]
    evidence_index: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "paper_id": self.paper_id,
            "domain_id": self.domain_id,
            "performance": self.performance,
            "evidence_index": self.evidence_index,
        }


def load_performance_schema(
    path: str | Path = DEFAULT_PERFORMANCE_SCHEMA,
) -> PerformanceSchema:
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PerformanceSchemaError("performance schema must be a mapping")
    for key in ("schema_version", "domain_id"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise PerformanceSchemaError(f"{key} must be a non-empty string")
    groups = payload.get("groups")
    if not isinstance(groups, dict) or set(groups) != set(PERFORMANCE_FIELDS):
        raise PerformanceSchemaError("performance groups do not match the contract")
    for group, fields in PERFORMANCE_FIELDS.items():
        if not isinstance(groups[group], dict) or set(groups[group]) != set(fields):
            raise PerformanceSchemaError(f"invalid fields for {group}")
    contract = payload.get("observation_contract")
    if not isinstance(contract, dict):
        raise PerformanceSchemaError("observation_contract must be a mapping")
    return PerformanceSchema(
        payload["schema_version"], payload["domain_id"], groups, contract, source
    )
