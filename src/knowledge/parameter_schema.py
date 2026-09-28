"""Load and validate the Ga2O3 photodetector parameter schema."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARAMETER_SCHEMA = (
    PROJECT_ROOT / "data" / "domains" / "semiconductor" / "ga2o3"
    / "parameter_schema.yaml"
)
REQUIRED_PARAMETER_FIELDS = {
    "material": (
        "semiconductor", "crystal_phase", "doping", "defect", "composite_material"
    ),
    "device": ("structure", "electrode", "substrate", "fabrication_method"),
    "performance": (
        "detection_wavelength", "responsivity", "detectivity", "quantum_efficiency",
        "response_time", "recovery_time", "on_off_ratio", "dark_current", "photocurrent",
    ),
    "mechanism": (
        "photo_generation", "carrier_transport", "defect_effect", "enhancement_mechanism"
    ),
    "comparison": ("baseline", "improvement_reason"),
}


class ParameterSchemaError(ValueError):
    """Raised when a parameter schema is missing or malformed."""


@dataclass(frozen=True)
class ParameterSchema:
    schema_version: str
    domain_id: str
    sections: dict[str, dict[str, dict[str, Any]]]
    source_path: Path

    def new_parameters(self) -> dict[str, dict[str, Any]]:
        return {
            section: {field: None for field in fields}
            for section, fields in REQUIRED_PARAMETER_FIELDS.items()
        }

    def field_definition(self, section: str, field: str) -> dict[str, Any] | None:
        definition = self.sections.get(section, {}).get(field)
        return deepcopy(definition) if definition is not None else None


def load_parameter_schema(
    path: str | Path = DEFAULT_PARAMETER_SCHEMA,
) -> ParameterSchema:
    schema_path = Path(path)
    if not schema_path.is_file():
        raise ParameterSchemaError(f"parameter schema does not exist: {schema_path}")
    payload = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ParameterSchemaError("parameter schema must be a mapping")
    schema_version = payload.get("schema_version")
    domain_id = payload.get("domain_id")
    sections = payload.get("sections")
    if not isinstance(schema_version, str) or not schema_version:
        raise ParameterSchemaError("parameter schema must define schema_version")
    if not isinstance(domain_id, str) or not domain_id:
        raise ParameterSchemaError("parameter schema must define domain_id")
    if not isinstance(sections, dict):
        raise ParameterSchemaError("parameter schema must define sections")
    for section, required_fields in REQUIRED_PARAMETER_FIELDS.items():
        fields = sections.get(section)
        if not isinstance(fields, dict):
            raise ParameterSchemaError(f"parameter schema section is missing: {section}")
        missing = [field for field in required_fields if field not in fields]
        if missing:
            raise ParameterSchemaError(
                f"parameter schema section {section} is missing fields: {missing}"
            )
        for field in required_fields:
            if not isinstance(fields[field], dict):
                raise ParameterSchemaError(f"{section}.{field} definition must be a mapping")
    return ParameterSchema(schema_version, domain_id, sections, schema_path)
