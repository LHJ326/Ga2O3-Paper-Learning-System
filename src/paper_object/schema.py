"""Load the standard Paper Object schema."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = PROJECT_ROOT / "data" / "paper_object" / "schema.yaml"
REQUIRED_SECTIONS = {
    "paper_identity": ("paper_id", "title", "authors", "year", "journal", "doi"),
    "source": ("pdf_path", "parsed_path", "evidence_index"),
    "knowledge": ("summary", "parameters", "performance", "mechanism"),
    "validation": ("evidence_coverage", "warnings", "review_status"),
}

class PaperObjectSchemaError(ValueError):
    pass

@dataclass(frozen=True)
class PaperObjectSchema:
    schema_version: str
    object_type: str
    sections: dict[str, dict[str, Any]]
    evidence_contract: dict[str, Any]
    review_status_values: tuple[str, ...]
    source_path: Path

def load_paper_object_schema(path: str | Path = DEFAULT_SCHEMA) -> PaperObjectSchema:
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperObjectSchemaError("Paper Object schema must be a mapping")
    for key in ("schema_version", "object_type"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise PaperObjectSchemaError(f"{key} must be a non-empty string")
    sections = payload.get("sections")
    if not isinstance(sections, dict) or set(sections) != set(REQUIRED_SECTIONS):
        raise PaperObjectSchemaError("Paper Object sections do not match the contract")
    for section, required in REQUIRED_SECTIONS.items():
        definition = sections.get(section)
        if not isinstance(definition, dict) or tuple(definition.get("required", ())) != required:
            raise PaperObjectSchemaError(f"invalid required fields for {section}")
    evidence = payload.get("evidence_contract")
    statuses = payload.get("review_status_values")
    if not isinstance(evidence, dict):
        raise PaperObjectSchemaError("evidence_contract must be a mapping")
    if not isinstance(statuses, list) or not all(isinstance(item, str) for item in statuses):
        raise PaperObjectSchemaError("review_status_values must be strings")
    return PaperObjectSchema(payload["schema_version"], payload["object_type"], sections,
                             evidence, tuple(statuses), source)
