from pathlib import Path

import pytest
import yaml

from src.knowledge import (
    KnowledgeDraft,
    KnowledgeValidationError,
    KnowledgeValidator,
    KnowledgeWriter,
    load_knowledge_schema,
)


def valid_draft() -> KnowledgeDraft:
    evidence = {
        "evidence_id": "E1",
        "element_id": "P101-text-1",
        "element_type": "TextBlock",
        "page": 2,
        "source_reference": '{"page": 2}',
        "quote": "Measured under 254 nm illumination.",
    }
    core = {
        "schema_version": "1.0",
        "paper_identity": {
            "paper_id": "P101",
            "title": "A Device Study",
            "doi": None,
            "metadata_path": "data/metadata/P101.yaml",
        },
        "research_problem": [{
            "statement": "Improve solar-blind detection.",
            "evidence_refs": ["E1"],
        }],
        "methodology": [{
            "name": "Device measurement",
            "description": "Measure photoresponse under UV illumination.",
            "evidence_refs": ["E1"],
        }],
        "results": [{
            "claim": "The device responds under 254 nm illumination.",
            "metric": "wavelength",
            "value": 254,
            "unit": "nm",
            "conditions": None,
            "evidence_refs": ["E1"],
        }],
        "innovation": [{
            "claim": "Uses a tested device structure.",
            "evidence_refs": ["E1"],
        }],
        "limitations": [{
            "statement": "Only one illumination wavelength is reported.",
            "scope": "measurement",
            "evidence_refs": ["E1"],
        }],
        "evidence_traceability": {
            "source_document": "data/papers/P101/parsed/document.yaml",
            "evidence_index": [evidence],
        },
    }
    domain = {
        "schema_version": "1.0",
        "paper_id": "P101",
        "domain_id": "semiconductor.ga2o3.photodetector",
        "schema_path": "data/domains/semiconductor/ga2o3/schema.yaml",
        "fields": {
            "material": {
                "composition": "Ga2O3",
                "evidence_refs": ["E1"],
            },
            "optical_performance": [{
                "metric": "wavelength",
                "value": 254,
                "unit": "nm",
                "evidence_refs": ["E1"],
            }],
        },
    }
    return KnowledgeDraft(
        paper_id="P101",
        core=core,
        domain=domain,
        summary="# Summary\n\nEvidence-grounded summary [E1].",
        key_points="# Key Points\n\n- Tested at 254 nm [E1].",
    )


def test_schema_loader_combines_core_and_domain_extension() -> None:
    schema = load_knowledge_schema()
    assert "research_problem" in schema.core
    assert schema.domain_id == "semiconductor.ga2o3.photodetector"
    assert {
        "material", "crystal_phase", "doping", "substrate",
        "device_structure", "fabrication", "optical_performance",
        "electrical_performance", "mechanism", "comparison",
    } == set(schema.domain_fields)
    clone = schema.new_core()
    clone["research_problem"].append({"draft": True})
    assert schema.core["research_problem"] == []


def test_schema_loader_supports_core_without_domain() -> None:
    schema = load_knowledge_schema(domain_path=None)
    assert schema.domain is None
    assert schema.domain_fields == {}


def test_validator_accepts_closed_evidence_graph() -> None:
    validator = KnowledgeValidator(load_knowledge_schema())
    result = validator.validate(valid_draft())
    assert result.valid
    assert result.issues == ()


def test_validator_rejects_missing_evidence_reference() -> None:
    draft = valid_draft()
    draft.core["results"][0]["evidence_refs"] = ["MISSING"]
    result = KnowledgeValidator(load_knowledge_schema()).validate(draft)
    assert not result.valid
    assert any("missing evidence" in issue.message for issue in result.issues)
    with pytest.raises(KnowledgeValidationError):
        result.raise_if_invalid()


def test_validator_rejects_wrong_core_and_domain_types() -> None:
    draft = valid_draft()
    draft.core["methodology"] = "not-a-list"
    draft.domain["fields"]["optical_performance"] = {"value": 1}
    draft.domain["fields"]["invented_field"] = []
    issues = KnowledgeValidator(load_knowledge_schema()).validate(draft).issues
    paths = {issue.path for issue in issues}
    assert "core.methodology" in paths
    assert "domain.fields.optical_performance" in paths
    assert "domain.fields.invented_field" in paths


def test_writer_generates_validated_knowledge_artifacts(tmp_path: Path) -> None:
    paper = tmp_path / "papers" / "P101"
    paper.mkdir(parents=True)
    writer = KnowledgeWriter(
        validator=KnowledgeValidator(load_knowledge_schema()),
        papers_root=tmp_path / "papers",
    )
    paths = writer.write(valid_draft())
    assert set(paths) == {
        "core", "domain", "summary", "key_points", "device_parameters"
    }
    assert all(path.is_file() for path in paths.values())
    parameters = yaml.safe_load(paths["device_parameters"].read_text(encoding="utf-8"))
    assert parameters["paper_id"] == "P101"
    assert parameters["parameters"]["material"]["composition"] == "Ga2O3"
    assert paths["summary"].read_text(encoding="utf-8").endswith("\n")


def test_writer_refuses_invalid_draft_before_creating_files(tmp_path: Path) -> None:
    paper = tmp_path / "papers" / "P101"
    paper.mkdir(parents=True)
    draft = valid_draft()
    draft.core["innovation"][0]["evidence_refs"] = []
    writer = KnowledgeWriter(
        validator=KnowledgeValidator(load_knowledge_schema()),
        papers_root=tmp_path / "papers",
    )
    with pytest.raises(KnowledgeValidationError):
        writer.write(draft)
    assert not (paper / "knowledge").exists()
