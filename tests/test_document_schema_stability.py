import json
from pathlib import Path

import yaml

from src.parser.adapters import MinerUAdapter
from src.schema import Evidence, EquationMetadata, FigureTextRelation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def test_evidence_round_trip_preserves_extensions() -> None:
    source_reference = json.dumps(
        {
            "paper_id": "P001",
            "parser_name": "MinerU",
            "parser_version": "4.0.7",
            "source_file": "json/image_exports.json",
            "page": 3,
            "mineru_locator": "doc:test/page:3/block:1",
            "representation_type": "image_only",
        }
    )

    evidence = Evidence.from_source_reference(source_reference)

    assert evidence.paper_id == "P001"
    assert evidence.page == 3
    assert evidence.details["representation_type"] == "image_only"
    assert json.loads(evidence.to_source_reference()) == json.loads(
        source_reference
    )


def test_p001_has_typed_figure_text_relations() -> None:
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    figure_ids = {figure.id for figure in document.figures}
    text_block_ids = {block.id for block in document.text_blocks}

    assert len(document.figure_text_relations) == 40
    assert all(
        isinstance(relation, FigureTextRelation)
        for relation in document.figure_text_relations
    )
    assert len({relation.id for relation in document.figure_text_relations}) == 40
    for relation in document.figure_text_relations:
        assert relation.figure_id in figure_ids
        assert relation.text_block_id in text_block_ids
        assert relation.relation_type == "explicit_figure_reference"
        assert relation.normalized_reference.startswith("Figure ")
        assert relation.evidence.paper_id == document.document_id
        assert relation.evidence.page is not None


def test_p001_equations_have_typed_metadata() -> None:
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)

    assert len(document.equations) == 6
    for equation in document.equations:
        assert isinstance(equation.metadata, EquationMetadata)
        assert equation.metadata.representation_type == "image_only"
        assert equation.metadata.formula_image_path
        assert equation.metadata.equation_number is None
        assert equation.metadata.related_text_block_ids

        evidence = equation.evidence
        assert evidence.paper_id == document.document_id
        assert evidence.details["representation_type"] == (
            equation.metadata.representation_type
        )
        assert evidence.details["formula_image_path"] == (
            equation.metadata.formula_image_path
        )


def test_schema_config_declares_stable_typed_extensions() -> None:
    with (PROJECT_ROOT / "configs" / "schema.yaml").open(
        encoding="utf-8"
    ) as config_file:
        schema = yaml.safe_load(config_file)["document_schema"]

    assert schema["version"] == "0.2"
    assert schema["document"]["fields"]["figure_text_relations"] == (
        "list[FigureTextRelation]"
    )
    assert "Evidence" in schema["objects"]
    assert "FigureTextRelation" in schema["objects"]
    assert "EquationMetadata" in schema["objects"]
