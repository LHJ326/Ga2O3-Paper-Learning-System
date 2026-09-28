import json
from pathlib import Path

import pytest
import yaml

from src.knowledge import (
    MaterialDeviceValidator,
    P001MaterialDeviceExtractor,
    ParameterDraft,
    ParameterValidationError,
    load_material_device_schema,
    load_parameter_schema,
)
from src.llm import MockLLMAdapter
from src.schema import Document, Metadata, Section, TextBlock


def _document() -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "Paper", "metadata.json"),
        sections=[Section("section-1", 1, "Experimental", "doc.json#/sections/1")],
        text_blocks=[TextBlock(
            "text-1", 2,
            "A MoS2/beta-Ga2O3/graphene heterostructure device was fabricated "
            "on a SiO2/Si substrate with Au electrodes.",
            "doc.json#/text/1",
        )],
    )


def _response() -> str:
    empty_material = {
        "semiconductor": None,
        "crystal_phase": None,
        "doping": None,
        "defect": None,
        "composite_material": None,
    }
    empty_device = {
        "structure": None,
        "electrode": None,
        "substrate": None,
        "fabrication_method": None,
    }
    empty_material["composite_material"] = {
        "value": "MoS2/beta-Ga2O3/graphene heterostructure",
        "evidence_refs": ["E00002"],
    }
    empty_device["substrate"] = {
        "value": "SiO2/Si", "evidence_refs": ["E00002"]
    }
    empty_device["electrode"] = {
        "value": "Au", "evidence_refs": ["E00002"]
    }
    return json.dumps({"material": empty_material, "device": empty_device})


def test_material_device_schema_supports_required_b1_concepts() -> None:
    schema = load_material_device_schema()
    assert schema.sections["material"]["semiconductor"]["label"] == "semiconductor material"
    assert schema.sections["material"]["composite_material"]["label"] == "heterostructure"
    attributes = schema.sections["device"]["structure"]["supported_attributes"]
    assert {"device_type", "architecture", "active_layer"} <= set(attributes)
    assert "fabrication_method" in schema.sections["device"]


def test_material_device_validator_requires_source_element_type() -> None:
    schema = load_parameter_schema()
    parameters = schema.new_parameters()
    parameters["device"]["electrode"] = {
        "value": "Au", "evidence_refs": ["E1"]
    }
    draft = ParameterDraft(
        schema.schema_version, "P001", schema.domain_id, parameters,
        [{
            "evidence_id": "E1", "page": 2,
            "source_reference": "doc.json#/text/1", "quote": "Au electrodes",
        }],
    )
    result = MaterialDeviceValidator(schema).validate(draft)
    assert "evidence_index[0].element_type" in {issue.path for issue in result.issues}
    with pytest.raises(ParameterValidationError):
        result.raise_if_invalid()


def test_material_device_pipeline_writes_yaml_and_jsonl_provenance(tmp_path: Path) -> None:
    papers_root = tmp_path / "papers"
    output = papers_root / "P001" / "knowledge"
    output.mkdir(parents=True)
    extractor = P001MaterialDeviceExtractor(MockLLMAdapter(default_response=_response()))
    result = extractor.run(
        document=_document(), schema=load_parameter_schema(),
        output_dir=output, papers_root=papers_root,
    )

    payload = yaml.safe_load(result.parameters_path.read_text(encoding="utf-8"))
    assert payload["parameters"]["device"]["electrode"]["value"] == "Au"
    assert payload["evidence_index"][0]["page"] == 2
    assert payload["evidence_index"][0]["element_type"] == "TextBlock"
    assert result.prompts_path.name == "device_extraction_prompts.jsonl"
    assert result.responses_path.name == "device_extraction_responses.jsonl"
    assert result.run_manifest_path.name == "device_extraction_run.yaml"
    assert len(result.prompts_path.read_text(encoding="utf-8").splitlines()) == 1
    assert len(result.responses_path.read_text(encoding="utf-8").splitlines()) == 1
    assert result.unsupported_fields == 0
