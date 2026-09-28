import json
from pathlib import Path

import pytest
import yaml

from src.paper_object import (
    PaperObjectBuilder,
    PaperObjectExporter,
    PaperObjectValidationError,
    PaperObjectValidator,
    load_paper_object_schema,
)


def _evidence(evidence_id: str, page: int) -> dict[str, object]:
    return {
        "evidence_id": evidence_id,
        "page": page,
        "element_id": f"text-{page}",
        "element_type": "TextBlock",
        "source_reference": f"doc.json#/text/{page}",
        "quote": f"Evidence text {page}",
    }


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    knowledge = root / "data" / "papers" / "P001" / "knowledge"
    knowledge.mkdir(parents=True)
    (root / "data" / "parsed" / "P001" / "mineru" / "raw").mkdir(parents=True)
    metadata = root / "data" / "metadata"
    metadata.mkdir(parents=True)
    (metadata / "P001.yaml").write_text(
        "paper_id: P001\ntitle: Test paper\nsource_pdf: data/papers/P001.pdf\n",
        encoding="utf-8",
    )
    (knowledge / "summary.md").write_text("# Summary\n\nClaim [E00001].\n", encoding="utf-8")
    parameter = {
        "schema_version": "1.0", "paper_id": "P001", "domain_id": "parameters",
        "parameters": {"material": {"semiconductor": {
            "value": "Ga2O3", "evidence_refs": ["E00001"]
        }}}, "evidence_index": [_evidence("E00001", 1)],
    }
    performance = {
        "schema_version": "1.0", "paper_id": "P001", "domain_id": "performance",
        "performance": {"optical_performance": {"responsivity": {
            "value": 1, "unit": "A/W", "evidence_id": "E00002", "page": 2,
            "source_type": "TextBlock"
        }}}, "evidence_index": [_evidence("E00002", 2)],
    }
    mechanism = {
        "schema_version": "1.0", "paper_id": "P001", "domain_id": "mechanism",
        "mechanisms": {"carrier_transport": {
            "value": "Carriers transfer.", "evidence_id": "E00003", "page": 3,
            "source_type": "TextBlock", "confidence": 0.9,
            "review_status": "unreviewed"
        }}, "evidence_index": [_evidence("E00003", 3)],
    }
    for name, payload in (
        ("device_parameters.yaml", parameter), ("performance.yaml", performance),
        ("mechanism.yaml", mechanism),
    ):
        (knowledge / name).write_text(
            yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
        )
    summary_item = _evidence("E00001", 1)
    summary_item["content"] = summary_item.pop("quote")
    prompt = "Contract\n\nExtraction task:\n" + json.dumps({"evidence": [summary_item]})
    (knowledge / "summary_extraction_prompts.jsonl").write_text(
        json.dumps({"call_index": 1, "prompt": prompt}) + "\n", encoding="utf-8"
    )
    return root


def test_paper_object_schema_loads_required_sections() -> None:
    schema = load_paper_object_schema()
    assert schema.schema_version == "1.0"
    assert set(schema.sections) == {"paper_identity", "source", "knowledge", "validation"}


def test_builder_preserves_complete_knowledge_and_evidence(tmp_path: Path) -> None:
    payload = PaperObjectBuilder(project_root=_project(tmp_path)).build("P001")
    assert payload["knowledge"]["summary"].startswith("# Summary")
    assert "parameters" in payload["knowledge"]["parameters"]
    assert "performance" in payload["knowledge"]["performance"]
    assert "mechanisms" in payload["knowledge"]["mechanism"]
    assert {item["evidence_id"] for item in payload["source"]["evidence_index"]} == {
        "E00001", "E00002", "E00003"
    }
    assert payload["validation"]["evidence_coverage"] == 1.0


def test_missing_identity_fields_remain_null(tmp_path: Path) -> None:
    payload = PaperObjectBuilder(project_root=_project(tmp_path)).build("P001")
    assert payload["paper_identity"]["authors"] is None
    assert payload["paper_identity"]["year"] is None
    assert payload["paper_identity"]["journal"] is None
    assert payload["paper_identity"]["doi"] is None


def test_validator_rejects_unresolved_evidence(tmp_path: Path) -> None:
    root = _project(tmp_path)
    payload = PaperObjectBuilder(project_root=root).build("P001")
    payload["knowledge"]["summary"] += "Unsupported [E99999].\n"
    result = PaperObjectValidator(load_paper_object_schema()).validate(payload)
    assert not result.valid
    with pytest.raises(PaperObjectValidationError, match="E99999"):
        result.raise_if_invalid()


def test_builder_requires_every_knowledge_file(tmp_path: Path) -> None:
    root = _project(tmp_path)
    (root / "data" / "papers" / "P001" / "knowledge" / "mechanism.yaml").unlink()
    with pytest.raises(FileNotFoundError, match="mechanism.yaml"):
        PaperObjectBuilder(project_root=root).build("P001")


def test_exporter_writes_valid_yaml_atomically(tmp_path: Path) -> None:
    root = _project(tmp_path)
    schema = load_paper_object_schema()
    payload = PaperObjectBuilder(project_root=root, schema=schema).build("P001")
    output = PaperObjectExporter(validator=PaperObjectValidator(schema)).export(
        payload, root / "data" / "papers" / "P001" / "paper_object.yaml"
    )
    loaded = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert loaded == payload
    assert not output.with_suffix(".yaml.tmp").exists()
