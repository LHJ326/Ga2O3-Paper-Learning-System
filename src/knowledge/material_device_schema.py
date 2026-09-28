"""Load the narrow Material/Device extraction view."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .parameter_schema import PROJECT_ROOT


DEFAULT_MATERIAL_DEVICE_SCHEMA = (
    PROJECT_ROOT / "data" / "domains" / "semiconductor" / "ga2o3"
    / "material_device_schema.yaml"
)


class MaterialDeviceSchemaError(ValueError):
    """Raised when the B1 extraction schema is absent or malformed."""


@dataclass(frozen=True)
class MaterialDeviceSchema:
    schema_version: str
    domain_id: str
    output_schema: str
    sections: dict[str, dict[str, dict[str, Any]]]
    evidence_contract: dict[str, Any]
    source_path: Path


def load_material_device_schema(
    path: str | Path = DEFAULT_MATERIAL_DEVICE_SCHEMA,
) -> MaterialDeviceSchema:
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MaterialDeviceSchemaError("material/device schema must be a mapping")
    for name in ("schema_version", "domain_id", "output_schema"):
        if not isinstance(payload.get(name), str) or not payload[name].strip():
            raise MaterialDeviceSchemaError(f"{name} must be a non-empty string")
    sections = payload.get("sections")
    if not isinstance(sections, dict) or set(sections) != {"material", "device"}:
        raise MaterialDeviceSchemaError("sections must contain only material and device")
    expected = {
        "material": {"semiconductor", "crystal_phase", "doping", "composite_material"},
        "device": {"structure", "substrate", "electrode", "fabrication_method"},
    }
    for section, fields in expected.items():
        value = sections.get(section)
        if not isinstance(value, dict) or set(value) != fields:
            raise MaterialDeviceSchemaError(
                f"{section} fields must be exactly {sorted(fields)}"
            )
        if any(not isinstance(definition, dict) for definition in value.values()):
            raise MaterialDeviceSchemaError(f"{section} field definitions must be mappings")
    contract = payload.get("evidence_contract")
    if not isinstance(contract, dict):
        raise MaterialDeviceSchemaError("evidence_contract must be a mapping")
    return MaterialDeviceSchema(
        payload["schema_version"], payload["domain_id"], payload["output_schema"],
        sections, contract, source,
    )
