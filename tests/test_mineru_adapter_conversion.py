import json
from pathlib import Path

from src.parser.adapters import MinerUAdapter
from src.schema.document import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _converted_document() -> Document:
    return MinerUAdapter().convert(P001_RAW_OUTPUT)


def test_p001_raw_output_can_be_loaded() -> None:
    assert P001_RAW_OUTPUT.is_dir()
    assert (P001_RAW_OUTPUT / "json" / "P001_content.json").is_file()
    assert (P001_RAW_OUTPUT / "json" / "image_exports.json").is_file()


def test_convert_returns_document_with_expected_counts() -> None:
    document = _converted_document()

    assert isinstance(document, Document)
    assert document.document_id == "P001"
    assert len(document.pages) == 12
    assert len(document.figures) == 17
    assert document.sections
    assert document.text_blocks


def test_converted_elements_preserve_source_references() -> None:
    document = _converted_document()
    elements = [
        document.metadata,
        *document.pages,
        *document.sections,
        *document.figures,
        *document.text_blocks,
    ]

    for element in elements:
        reference = json.loads(element.source_reference)
        assert reference["paper_id"] == "P001"
        assert reference["parser_name"] == "MinerU"
        assert reference["parser_version"] == "4.0.7"
        assert "source_file" in reference
        assert "page" in reference
        assert "mineru_locator" in reference

    assert all(
        json.loads(figure.source_reference)["mineru_locator"]
        for figure in document.figures
    )
