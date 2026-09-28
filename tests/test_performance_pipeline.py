import json
from pathlib import Path

import pytest
import yaml

from src.knowledge import (
    PerformanceDraft,
    PerformanceEvidenceSelector,
    PerformanceExtractionPipeline,
    PerformanceExtractor,
    PerformanceResponseParser,
    PerformanceValidationError,
    PerformanceValidator,
    PerformanceWriter,
    load_performance_schema,
)
from src.knowledge.prompt_builder import PromptEvidence
from src.llm import MockLLMAdapter
from src.schema import Document, Metadata, Section, TextBlock


def _document() -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "Paper", "metadata.json"),
        sections=[Section("section-1", 1, "Results", "doc.json#/sections/1")],
        text_blocks=[
            TextBlock(
                "text-1", 2,
                "At 254 nm and 5 V bias, responsivity was 2.5 A/W and dark current was 1 nA.",
                "doc.json#/text/1",
            ),
            TextBlock(
                "text-2", 3, "Device fabrication used mechanical exfoliation.",
                "doc.json#/text/2",
            ),
        ],
    )


def _response() -> str:
    schema = load_performance_schema()
    result = schema.new_performance()
    result["optical_performance"]["detection_wavelength"] = {
        "value": 254, "unit": "nm", "evidence_id": "E00002",
        "page": 2, "source_type": "TextBlock",
    }
    result["optical_performance"]["responsivity"] = {
        "value": 2.5, "unit": "A/W", "evidence_id": "E00002",
        "page": 2, "source_type": "TextBlock",
    }
    result["electrical_performance"]["dark_current"] = {
        "value": 1, "unit": "nA", "evidence_id": "E00002",
        "page": 2, "source_type": "TextBlock",
    }
    result["electrical_performance"]["bias_voltage"] = {
        "value": 5, "unit": "V", "evidence_id": "E00002",
        "page": 2, "source_type": "TextBlock",
    }
    return json.dumps(result)


def test_performance_schema_has_all_groups_and_nullable_fields() -> None:
    schema = load_performance_schema()
    data = schema.new_performance()
    assert data["optical_performance"]["external_quantum_efficiency"] is None
    assert data["dynamic_performance"]["decay_time"] is None
    assert data["stability"]["environmental_stability"] is None


def test_performance_selector_prefers_metrics_and_drops_fabrication_only() -> None:
    selector = PerformanceEvidenceSelector()
    evidence = [
        PromptEvidence("E1", "a", "TextBlock", 1, "x", "Responsivity is 2 A/W."),
        PromptEvidence("E2", "b", "TextBlock", 1, "x", "Mechanical exfoliation fabrication."),
    ]
    assert [item.evidence_id for item in selector.select(evidence)] == ["E1"]


def test_performance_parser_rejects_material_group() -> None:
    with pytest.raises(Exception, match="forbidden groups"):
        PerformanceResponseParser.parse(json.dumps({"material": {}}))


def test_validator_checks_unit_page_and_source_type() -> None:
    schema = load_performance_schema()
    performance = schema.new_performance()
    performance["optical_performance"]["responsivity"] = {
        "value": 2.5, "unit": None, "evidence_id": "E1",
        "page": 3, "source_type": "Figure",
    }
    draft = PerformanceDraft(
        schema.schema_version, "P001", schema.domain_id, performance,
        [{
            "evidence_id": "E1", "page": 2, "element_type": "TextBlock",
            "source_reference": "doc.json#/text/1", "quote": "2.5 A/W",
        }],
    )
    result = PerformanceValidator(schema).validate(draft)
    paths = {item.path for item in result.issues}
    assert "performance.optical_performance.responsivity.unit" in paths
    assert "performance.optical_performance.responsivity.page" in paths
    assert "performance.optical_performance.responsivity.source_type" in paths
    with pytest.raises(PerformanceValidationError):
        result.raise_if_invalid()


def test_validator_warns_when_value_context_conflicts_with_field() -> None:
    schema = load_performance_schema()
    performance = schema.new_performance()
    performance["electrical_performance"]["on_off_ratio"] = {
        "value": 81, "unit": "%", "evidence_id": "E1",
        "page": 4, "source_type": "Figure",
    }
    draft = PerformanceDraft(
        schema.schema_version, "P001", schema.domain_id, performance,
        [{
            "evidence_id": "E1", "page": 4, "element_type": "Figure",
            "source_reference": "doc.json#/figures/3",
            "quote": (
                "The maximum storage window ratio reaches 81%. " + "detail " * 40 +
                "Later panels show "
                "switching ratios at different pulse widths."
            ),
        }],
    )
    result = PerformanceValidator(schema).validate(draft)
    assert result.valid
    assert result.review_required
    assert result.warnings[0].field == "on_off_ratio"
    assert result.warnings[0].evidence_id == "E1"


def test_performance_pipeline_writes_yaml_and_provenance(tmp_path: Path) -> None:
    schema = load_performance_schema()
    papers_root = tmp_path / "papers"
    output = papers_root / "P001" / "knowledge"
    output.mkdir(parents=True)
    extractor = PerformanceExtractor(MockLLMAdapter(default_response=_response()))
    validator = PerformanceValidator(schema)
    result = PerformanceExtractionPipeline(
        extractor=extractor,
        validator=validator,
        writer=PerformanceWriter(validator=validator, papers_root=papers_root),
    ).run(document=_document(), schema=schema, output_dir=output)
    payload = yaml.safe_load(result.performance_path.read_text(encoding="utf-8"))
    assert payload["performance"]["optical_performance"]["responsivity"]["unit"] == "A/W"
    assert payload["evidence_index"][0]["element_type"] == "TextBlock"
    assert result.performance_path.name == "performance.yaml"
    assert result.prompts_path.name == "performance_extraction_prompts.jsonl"
    assert result.responses_path.name == "performance_extraction_responses.jsonl"
    assert result.api_calls == 1
