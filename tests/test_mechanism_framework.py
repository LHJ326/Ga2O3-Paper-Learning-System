import json
from pathlib import Path

import pytest
import yaml

from src.knowledge import (
    MechanismDraft,
    MechanismEvidenceSelector,
    MechanismExtractionPipeline,
    MechanismExtractor,
    MechanismValidationError,
    MechanismValidator,
    MechanismWriter,
    load_mechanism_schema,
)
from src.knowledge.prompt_builder import PromptEvidence
from src.llm import MockLLMAdapter
from src.schema import Document, Metadata, Section, TextBlock


def _document() -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "Paper", "metadata.json"),
        sections=[Section("section-1", 1, "Mechanism", "doc.json#/sections/1")],
        text_blocks=[TextBlock(
            "text-1", 2,
            "Photogenerated carriers tunnel through Ga2O3 and transfer to the floating gate.",
            "doc.json#/text/1",
        )],
    )


def _response() -> str:
    schema = load_mechanism_schema()
    result = schema.new_mechanisms()
    result["carrier_transport"] = {
        "value": "Photogenerated carriers tunnel through Ga2O3 to the floating gate.",
        "evidence_id": "E00002", "page": 2, "source_type": "TextBlock",
        "confidence": 0.95, "review_status": "unreviewed",
    }
    return json.dumps(result)


def test_mechanism_schema_loads_all_nullable_fields() -> None:
    schema = load_mechanism_schema()
    values = schema.new_mechanisms()
    assert len(values) == 8
    assert values["photogeneration"] is None
    assert values["device_working_principle"] is None


def test_mechanism_selector_keeps_mechanism_and_drops_performance_only() -> None:
    selector = MechanismEvidenceSelector()
    evidence = [
        PromptEvidence("E1", "a", "TextBlock", 1, "x", "Carrier tunneling mechanism."),
        PromptEvidence("E2", "b", "TextBlock", 1, "x", "Responsivity is 2 A/W."),
    ]
    assert [item.evidence_id for item in selector.select(evidence)] == ["E1"]


def test_mechanism_validator_detects_unsupported_evidence() -> None:
    schema = load_mechanism_schema()
    mechanisms = schema.new_mechanisms()
    mechanisms["carrier_transport"] = {
        "value": "Carriers tunnel.", "evidence_id": "MISSING", "page": 2,
        "source_type": "TextBlock", "confidence": 0.8,
        "review_status": "unreviewed",
    }
    draft = MechanismDraft(schema.schema_version, "P001", schema.domain_id, mechanisms, [])
    result = MechanismValidator(schema).validate(draft)
    assert any("unsupported Evidence" in issue.message for issue in result.issues)
    with pytest.raises(MechanismValidationError):
        result.raise_if_invalid()


def test_mechanism_validator_checks_page_source_confidence_and_status() -> None:
    schema = load_mechanism_schema()
    mechanisms = schema.new_mechanisms()
    mechanisms["defect_mechanism"] = {
        "value": "Traps affect transport.", "evidence_id": "E1", "page": 0,
        "source_type": "Figure", "confidence": 2,
        "review_status": "verified",
    }
    draft = MechanismDraft(
        schema.schema_version, "P001", schema.domain_id, mechanisms,
        [{"evidence_id": "E1", "page": 2, "element_type": "TextBlock",
          "source_reference": "doc.json#/text/1", "quote": "Traps affect transport."}],
    )
    paths = {issue.path for issue in MechanismValidator(schema).validate(draft).issues}
    assert "mechanisms.defect_mechanism.page" in paths
    assert "mechanisms.defect_mechanism.source_type" in paths
    assert "mechanisms.defect_mechanism.confidence" in paths
    assert "mechanisms.defect_mechanism.review_status" in paths


def test_mechanism_pipeline_writes_evidence_bound_yaml(tmp_path: Path) -> None:
    schema = load_mechanism_schema()
    papers_root = tmp_path / "papers"
    output = papers_root / "P001" / "knowledge"
    output.mkdir(parents=True)
    extractor = MechanismExtractor(MockLLMAdapter(default_response=_response()))
    validator = MechanismValidator(schema)
    result = MechanismExtractionPipeline(
        extractor=extractor, validator=validator,
        writer=MechanismWriter(validator=validator, papers_root=papers_root),
    ).run(document=_document(), schema=schema, output_dir=output)
    payload = yaml.safe_load(result.mechanism_path.read_text(encoding="utf-8"))
    item = payload["mechanisms"]["carrier_transport"]
    assert item["evidence_id"] == "E00002"
    assert item["page"] == 2
    assert item["source_type"] == "TextBlock"
    assert payload["evidence_index"][0]["source_reference"] == "doc.json#/text/1"
