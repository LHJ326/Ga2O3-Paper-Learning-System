"""Validation constants and checks for Registry v2."""

from __future__ import annotations

from typing import Any


LIFECYCLE_FIELDS = (
    "metadata_status",
    "knowledge_status",
    "object_status",
    "embedding_status",
    "rag_status",
)
LIFECYCLE_STATUS_VALUES = frozenset(
    {"pending", "in_progress", "completed", "failed", "skipped"}
)
REQUIRED_PAPER_FIELDS = (
    "paper_id", "title", "authors", "year", "journal", "DOI", "source_pdf",
    "metadata_path", "parsed_path", "processing_status", *LIFECYCLE_FIELDS,
)


class RegistrySchemaError(ValueError):
    pass


def validate_registry(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RegistrySchemaError("registry must be a mapping")
    version = payload.get("registry_version")
    if version != "2.0":
        raise RegistrySchemaError("registry_version must be 2.0")
    declared = payload.get("lifecycle_status_values")
    if not isinstance(declared, list) or set(declared) != set(LIFECYCLE_STATUS_VALUES):
        raise RegistrySchemaError("lifecycle_status_values do not match Registry v2")
    papers = payload.get("papers")
    if not isinstance(papers, list):
        raise RegistrySchemaError("papers must be a list")
    seen: set[str] = set()
    for index, paper in enumerate(papers):
        if not isinstance(paper, dict):
            raise RegistrySchemaError(f"papers[{index}] must be a mapping")
        missing = [field for field in REQUIRED_PAPER_FIELDS if field not in paper]
        if missing:
            raise RegistrySchemaError(f"papers[{index}] is missing fields: {missing}")
        paper_id = paper.get("paper_id")
        if not isinstance(paper_id, str) or not paper_id:
            raise RegistrySchemaError(f"papers[{index}].paper_id must be non-empty")
        if paper_id in seen:
            raise RegistrySchemaError(f"duplicate paper_id: {paper_id}")
        seen.add(paper_id)
        for field in LIFECYCLE_FIELDS:
            if paper.get(field) not in LIFECYCLE_STATUS_VALUES:
                raise RegistrySchemaError(
                    f"papers[{index}].{field} has invalid status: {paper.get(field)!r}"
                )
    return payload
