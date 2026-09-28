import json
from pathlib import Path

import pytest
import yaml

from src.knowledge import (
    LLMParameterExtractor,
    ParameterDraft,
    ParameterExtractionContext,
    ParameterExtractionPipeline,
    ParameterValidationError,
    ParameterValidator,
    ParameterWriter,
    load_parameter_schema,
)
from src.llm import MockLLMAdapter


def valid_draft(paper_id: str = "P100") -> ParameterDraft:
    schema = load_parameter_schema()
    parameters = schema.new_parameters()
    parameters["material"]["semiconductor"] = {
        "value": "β-Ga2O3",
        "evidence_refs": ["E00001"],
    }
    parameters["performance"]["responsivity"] = [{
        "value": 2.5,
        "unit": "A/W",
        "conditions": {"wavelength": 254, "wavelength_unit": "nm"},
        "evidence_refs": ["E00001"],
    }]
    return ParameterDraft(
        schema_version=schema.schema_version,
        paper_id=paper_id,
        domain_id=schema.domain_id,
        parameters=parameters,
        evidence_index=[{
            "evidence_id": "E00001",
            "page": 2,
            "element_id": "P100-text-1",
            "source_reference": {"source_file": "document.json", "page": 2},
        }],
    )


def test_parameter_schema_loads_all_sections_and_nullable_template() -> None:
    schema = load_parameter_schema()
    assert schema.domain_id == "semiconductor.ga2o3.photodetector.parameters"
    assert set(schema.sections) == {
        "material", "device", "performance", "mechanism", "comparison"
    }
    parameters = schema.new_parameters()
    assert parameters["material"]["doping"] is None
    assert parameters["performance"]["detectivity"] is None


def test_parameter_validator_checks_types_evidence_pages_and_units() -> None:
    schema = load_parameter_schema()
    draft = valid_draft()
    draft.evidence_index[0]["page"] = 0
    draft.parameters["performance"]["responsivity"] = [
        {"value": 2.5, "unit": "A/W", "evidence_refs": ["MISSING"]},
        {"value": 2500, "unit": "mA/W", "evidence_refs": ["E00001"]},
    ]
    draft.parameters["device"]["structure"] = "MSM"

    result = ParameterValidator(schema).validate(draft)
    paths = {issue.path for issue in result.issues}
    assert "evidence_index[0].page" in paths
    assert "parameters.performance.responsivity[0].evidence_refs[0]" in paths
    assert "parameters.performance.responsivity" in paths
    assert "parameters.device.structure" in paths
    with pytest.raises(ParameterValidationError):
        result.raise_if_invalid()


def test_mock_parameter_extraction_uses_adapter_and_prompt_contract() -> None:
    schema = load_parameter_schema()
    expected = valid_draft().as_dict()
    adapter = MockLLMAdapter(generate_responses=[json.dumps(expected)])
    extractor = LLMParameterExtractor(adapter)
    context = ParameterExtractionContext(
        paper_id="P100",
        schema=schema,
        evidence=({
            "evidence_id": "E00001",
            "page": 2,
            "element_id": "P100-text-1",
            "source_reference": "document.json",
            "content": "Responsivity is 2.5 A/W at 254 nm.",
        },),
    )

    draft = extractor.extract(context)

    assert draft.parameters["performance"]["responsivity"][0]["unit"] == "A/W"
    assert len(adapter.generate_calls) == 1
    assert "Never infer" in adapter.generate_calls[0]
    assert "E00001" in adapter.generate_calls[0]


def test_validator_accepts_closed_parameter_evidence_graph() -> None:
    result = ParameterValidator(load_parameter_schema()).validate(valid_draft())
    assert result.valid
    assert result.issues == ()


def test_pipeline_validates_and_writer_preserves_output(tmp_path: Path) -> None:
    schema = load_parameter_schema()
    expected = valid_draft().as_dict()
    adapter = MockLLMAdapter(generate_responses=[json.dumps(expected)])
    validator = ParameterValidator(schema)
    papers_root = tmp_path / "papers"
    (papers_root / "P100").mkdir(parents=True)
    pipeline = ParameterExtractionPipeline(
        extractor=LLMParameterExtractor(adapter),
        validator=validator,
        writer=ParameterWriter(validator=validator, papers_root=papers_root),
    )
    context = ParameterExtractionContext(
        paper_id="P100",
        schema=schema,
        evidence=tuple(expected["evidence_index"]),
    )

    draft, output = pipeline.run(context)

    written = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert output == papers_root / "P100" / "knowledge" / "device_parameters.yaml"
    assert written == draft.as_dict()
    assert written["parameters"]["material"]["doping"] is None
