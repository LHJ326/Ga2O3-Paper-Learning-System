import json
from pathlib import Path

import pytest
import yaml

from src.knowledge.material_device_extraction import (
    MaterialDeviceEvidenceFilter,
    MaterialDeviceResponseParser,
    P001MaterialDeviceExtractor,
)
from src.knowledge.parameter_extractor import ParameterResponseError
from src.knowledge.parameter_schema import load_parameter_schema
from src.knowledge.prompt_builder import PromptEvidence
from src.llm import MockLLMAdapter
from src.schema import Document, Figure, Metadata, Section, TextBlock


def document() -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "Paper", "metadata.json"),
        sections=[Section("section-1", 1, "Device structure", "section.json")],
        text_blocks=[
            TextBlock(
                "text-1", 1,
                "A MoS2/beta-Ga2O3/graphene heterostructure uses Au electrodes.",
                "doc.json#/text/1",
            ),
            TextBlock(
                "text-2", 2, "The response time was measured.", "doc.json#/text/2"
            ),
        ],
        figures=[Figure(
            "figure-1", 1, "Device layer structure and electrode layout.",
            "doc.json#/figures/1"
        )],
    )


def response() -> str:
    return json.dumps({
        "material": {
            "semiconductor": {
                "value": "MoS2/beta-Ga2O3",
                "evidence_refs": ["E00002"],
            },
            "crystal_phase": None,
            "doping": None,
            "defect": None,
            "composite_material": None,
        },
        "device": {
            "structure": None,
            "electrode": {"value": "Au", "evidence_refs": ["E00002"]},
            "substrate": None,
            "fabrication_method": None,
        },
    })


def test_b1_filter_keeps_material_device_and_excludes_performance_only() -> None:
    filter_ = MaterialDeviceEvidenceFilter()
    evidence = [
        PromptEvidence(
            "E1", "a", "TextBlock", 1, "x",
            "MoS2/Ga2O3 heterostructure device layer",
        ),
        PromptEvidence("E2", "b", "TextBlock", 1, "x", "response time is 2 ms"),
        PromptEvidence("E3", "c", "Equation", 1, "x", "Ga2O3"),
    ]
    assert [item.evidence_id for item in filter_.select(evidence)] == ["E1"]


def test_b1_filter_downranks_performance_figures_and_introduction() -> None:
    filter_ = MaterialDeviceEvidenceFilter()
    evidence = [
        PromptEvidence("S1", "intro", "Section", 1, "x", "Introduction"),
        PromptEvidence("S2", "experiment", "Section", 2, "x", "Experimental"),
        PromptEvidence(
            "E1", "a", "TextBlock", 1, "x",
            "Ga2O3 semiconductor device performance and stability.", "intro"
        ),
        PromptEvidence(
            "E2", "b", "TextBlock", 2, "x",
            "Device fabrication used a Ga2O3 layer and Au electrode.", "experiment"
        ),
        PromptEvidence(
            "E3", "c", "Figure", 2, "x",
            "Electrical performance and responsivity comparison figure.", "experiment"
        ),
    ]
    selected = {item.evidence_id for item in filter_.select(evidence)}
    assert "E1" not in selected
    assert "E2" in selected
    assert "E3" not in selected


def test_response_parser_rejects_unrelated_parameter_groups() -> None:
    with pytest.raises(ParameterResponseError):
        MaterialDeviceResponseParser.parse(json.dumps({
            "material": {}, "device": {}, "performance": {"responsivity": {}}
        }))


def test_response_parser_preserves_nulls_and_accepts_json_fence() -> None:
    parsed = MaterialDeviceResponseParser.parse(f"```json\n{response()}\n```")
    assert parsed["material"]["doping"] is None
    assert parsed["device"]["substrate"] is None


def test_b1_pipeline_binds_evidence_and_leaves_other_groups_null(tmp_path: Path) -> None:
    schema = load_parameter_schema()
    adapter = MockLLMAdapter(default_response=response())
    papers_root = tmp_path / "papers"
    output_dir = papers_root / "P001" / "knowledge"
    output_dir.mkdir(parents=True)
    extractor = P001MaterialDeviceExtractor(adapter)
    prepared = extractor.prepare(document=document(), schema=schema)

    result = extractor.run(
        document=document(), schema=schema, output_dir=output_dir,
        papers_root=papers_root, prepared=prepared,
    )

    payload = yaml.safe_load(result.parameters_path.read_text(encoding="utf-8"))
    assert payload["parameters"]["material"]["semiconductor"]["evidence_refs"] == ["E00002"]
    assert payload["parameters"]["device"]["electrode"]["value"] == "Au"
    assert all(value is None for value in payload["parameters"]["performance"].values())
    assert all(value is None for value in payload["parameters"]["mechanism"].values())
    assert all(value is None for value in payload["parameters"]["comparison"].values())
    assert payload["evidence_index"][0]["page"] == 1
    assert payload["evidence_index"][0]["element_type"] == "TextBlock"
    assert result.unsupported_fields == 0
    assert len(adapter.generate_calls) == result.chunk_count


def test_unknown_evidence_reference_is_rejected(tmp_path: Path) -> None:
    bad = json.loads(response())
    bad["material"]["semiconductor"]["evidence_refs"] = ["E99999"]
    adapter = MockLLMAdapter(default_response=json.dumps(bad))
    schema = load_parameter_schema()
    papers_root = tmp_path / "papers"
    output_dir = papers_root / "P001" / "knowledge"
    output_dir.mkdir(parents=True)
    extractor = P001MaterialDeviceExtractor(adapter)
    with pytest.raises(Exception, match="references missing Evidence"):
        extractor.run(
            document=document(), schema=schema, output_dir=output_dir,
            papers_root=papers_root,
        )
    assert not (output_dir / "device_parameters.yaml").exists()
