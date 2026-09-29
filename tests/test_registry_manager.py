from pathlib import Path

import pytest
import yaml

from src.registry import (
    RegistryManager,
    RegistryPaperNotFound,
    RegistrySchemaError,
    validate_registry,
)


def _registry(path: Path) -> Path:
    payload = {
        "registry_version": "2.0",
        "paper_record_fields": [],
        "lifecycle_status_values": [
            "pending", "in_progress", "completed", "failed", "skipped"
        ],
        "lifecycle_status_template": {},
        "processing_status_values": [],
        "processing_status_template": {},
        "papers": [{
            "paper_id": "P001",
            "title": "Paper",
            "authors": None,
            "year": 2025,
            "journal": "Journal",
            "DOI": None,
            "source_pdf": "data/papers/P001.pdf",
            "metadata_path": "data/metadata/P001.yaml",
            "parsed_path": "data/parsed/P001",
            "processing_status": "completed",
            "metadata_status": "completed",
            "knowledge_status": "pending",
            "object_status": "pending",
            "embedding_status": "pending",
            "rag_status": "pending",
        }],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_registry_loads_and_validates_v2_schema(tmp_path: Path) -> None:
    manager = RegistryManager(_registry(tmp_path / "registry.yaml"))
    assert manager.require_paper("P001")["metadata_status"] == "completed"
    assert validate_registry(manager.payload)["registry_version"] == "2.0"


def test_registry_updates_status_atomically_and_persists(tmp_path: Path) -> None:
    path = _registry(tmp_path / "registry.yaml")
    manager = RegistryManager(path)
    manager.update_status("P001", "knowledge_status", "completed")
    reloaded = RegistryManager(path)
    assert reloaded.require_paper("P001")["knowledge_status"] == "completed"
    assert not path.with_suffix(".yaml.tmp").exists()


def test_registry_rejects_unknown_stage_status_and_paper(tmp_path: Path) -> None:
    manager = RegistryManager(_registry(tmp_path / "registry.yaml"))
    with pytest.raises(RegistrySchemaError, match="unknown lifecycle stage"):
        manager.update_status("P001", "unknown", "completed")
    with pytest.raises(RegistrySchemaError, match="invalid lifecycle status"):
        manager.update_status("P001", "knowledge_status", "done")
    with pytest.raises(RegistryPaperNotFound):
        manager.update_status("P999", "knowledge_status", "completed")


def test_registry_queries_pending_tasks_and_completed_papers(tmp_path: Path) -> None:
    manager = RegistryManager(_registry(tmp_path / "registry.yaml"))
    pending = manager.pending_tasks("P001")
    assert {item["stage"] for item in pending} == {
        "knowledge_status", "object_status", "embedding_status", "rag_status"
    }
    assert manager.completed_papers(stage="metadata_status")[0]["paper_id"] == "P001"
    assert manager.completed_papers(stage="object_status") == []
