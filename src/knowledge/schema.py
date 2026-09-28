"""Load Core Knowledge templates and optional Domain Extensions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORE_SCHEMA = PROJECT_ROOT / "data" / "papers" / "TEMPLATE" / "knowledge" / "core.yaml"
DEFAULT_DOMAIN_SCHEMA = PROJECT_ROOT / "data" / "domains" / "semiconductor" / "ga2o3" / "schema.yaml"

CORE_FIELDS = (
    "paper_identity",
    "research_problem",
    "methodology",
    "results",
    "innovation",
    "limitations",
    "evidence_traceability",
)


class SchemaLoadError(ValueError):
    """Raised when a knowledge schema file is missing or malformed."""


@dataclass(frozen=True)
class KnowledgeSchema:
    core: dict[str, Any]
    domain: dict[str, Any] | None
    core_path: Path
    domain_path: Path | None

    @property
    def domain_id(self) -> str | None:
        if self.domain is None:
            return None
        value = self.domain.get("domain_id")
        return str(value) if value is not None else None

    @property
    def domain_fields(self) -> dict[str, dict[str, Any]]:
        if self.domain is None:
            return {}
        return dict(self.domain.get("field_definitions", {}))

    def new_core(self) -> dict[str, Any]:
        return deepcopy(self.core)


def _load_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SchemaLoadError(f"Knowledge schema does not exist: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SchemaLoadError(f"Knowledge schema must be a mapping: {path}")
    return payload


def load_knowledge_schema(
    *,
    core_path: str | Path = DEFAULT_CORE_SCHEMA,
    domain_path: str | Path | None = DEFAULT_DOMAIN_SCHEMA,
) -> KnowledgeSchema:
    """Load and minimally validate Core plus an optional Domain Extension."""
    core_file = Path(core_path)
    core = _load_mapping(core_file)
    missing = [field for field in CORE_FIELDS if field not in core]
    if missing:
        raise SchemaLoadError(f"Core Knowledge schema is missing fields: {missing}")

    domain_file = Path(domain_path) if domain_path is not None else None
    domain = _load_mapping(domain_file) if domain_file is not None else None
    if domain is not None:
        if not domain.get("domain_id"):
            raise SchemaLoadError("Domain Extension must define domain_id")
        if not isinstance(domain.get("field_definitions"), dict):
            raise SchemaLoadError("Domain Extension must define field_definitions")

    return KnowledgeSchema(
        core=core,
        domain=domain,
        core_path=core_file,
        domain_path=domain_file,
    )
