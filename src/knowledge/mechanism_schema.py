"""Schema and draft contracts for mechanism extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .parameter_schema import PROJECT_ROOT


DEFAULT_MECHANISM_SCHEMA = (
    PROJECT_ROOT / "data" / "domains" / "semiconductor" / "ga2o3"
    / "mechanism_schema.yaml"
)
MECHANISM_FIELDS = (
    "photogeneration", "carrier_transport", "recombination", "defect_mechanism",
    "interface_effect", "band_alignment", "gain_mechanism",
    "device_working_principle",
)


class MechanismSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class MechanismSchema:
    schema_version: str
    domain_id: str
    fields: dict[str, dict[str, Any]]
    observation_contract: dict[str, Any]
    source_path: Path

    def new_mechanisms(self) -> dict[str, Any]:
        return {field: None for field in MECHANISM_FIELDS}


@dataclass(frozen=True)
class MechanismDraft:
    schema_version: str
    paper_id: str
    domain_id: str
    mechanisms: dict[str, Any]
    evidence_index: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "paper_id": self.paper_id,
            "domain_id": self.domain_id,
            "mechanisms": self.mechanisms,
            "evidence_index": self.evidence_index,
        }


def load_mechanism_schema(path: str | Path = DEFAULT_MECHANISM_SCHEMA) -> MechanismSchema:
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MechanismSchemaError("mechanism schema must be a mapping")
    for key in ("schema_version", "domain_id"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise MechanismSchemaError(f"{key} must be a non-empty string")
    fields = payload.get("fields")
    if not isinstance(fields, dict) or set(fields) != set(MECHANISM_FIELDS):
        raise MechanismSchemaError("mechanism fields do not match the contract")
    if any(not isinstance(value, dict) for value in fields.values()):
        raise MechanismSchemaError("mechanism field definitions must be mappings")
    contract = payload.get("observation_contract")
    if not isinstance(contract, dict):
        raise MechanismSchemaError("observation_contract must be a mapping")
    return MechanismSchema(
        payload["schema_version"], payload["domain_id"], fields, contract, source
    )
