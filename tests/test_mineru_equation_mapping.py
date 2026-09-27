import json
import re
from pathlib import Path

from src.parser.adapters import MinerUAdapter
from src.schema.document import TextBlock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _raw_formula_locators() -> set[str]:
    markdown = (P001_RAW_OUTPUT / "markdown" / "P001.md").read_text(
        encoding="utf-8-sig"
    )
    return set(
        re.findall(r"!\[Formula block\]\((doc:[^)]+)\)", markdown)
    )


def test_p001_formula_assets_map_to_equations_not_figures() -> None:
    raw_formula_locators = _raw_formula_locators()
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    figure_locators = {
        json.loads(figure.source_reference)["mineru_locator"]
        for figure in document.figures
    }
    equation_locators = {
        json.loads(equation.source_reference)["mineru_locator"]
        for equation in document.equations
    }

    assert len(raw_formula_locators) == 6
    assert len(document.figures) == 6
    assert len(document.equations) == 6
    assert raw_formula_locators == equation_locators
    assert raw_formula_locators.isdisjoint(figure_locators)


def test_p001_image_only_equations_preserve_evidence_without_fake_content() -> None:
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    required = {
        "paper_id",
        "parser_name",
        "parser_version",
        "source_file",
        "page",
        "mineru_locator",
        "formula_image_path",
        "representation_type",
        "equation_number",
        "related_ids",
    }

    for equation in document.equations:
        source = json.loads(equation.source_reference)
        assert equation.page_number is not None
        assert required <= source.keys()
        assert source["page"] == equation.page_number
        assert source["representation_type"] == "image_only"
        assert source["equation_number"] is None
        assert source["formula_image_path"].startswith("images/")
        assert equation.content == ""


def test_equation_and_adjacent_text_evidence_is_bidirectional() -> None:
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    text_blocks = {block.id: block for block in document.text_blocks}

    assert any(
        json.loads(equation.source_reference)["related_ids"]
        for equation in document.equations
    )
    for equation in document.equations:
        source = json.loads(equation.source_reference)
        for text_block_id in source["related_ids"]:
            text_source = json.loads(text_blocks[text_block_id].source_reference)
            assert equation.id in text_source["related_ids"]
            assert any(
                reference["equation_id"] == equation.id
                and reference["mineru_locator"] == source["mineru_locator"]
                for reference in text_source["equation_references"]
            )


def test_markdown_math_is_preserved_when_reliably_available(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    image_dir = raw_root / "images"
    image_dir.mkdir(parents=True)
    (image_dir / "formula.jpg").write_bytes(b"formula")
    locator = "doc:test/tier:flash/page:1/block:2"
    math = r"$$x = 1 \tag{7}$$"
    text_block = TextBlock(
        id="P-test-text-0001",
        page_number=1,
        content="The following equation defines x.",
        source_reference=json.dumps({"related_ids": []}),
    )

    equations = MinerUAdapter()._convert_equations(
        {
            "images": [
                {
                    "locator": locator,
                    "file": "formula.jpg",
                }
            ]
        },
        raw_root,
        {
            "paper_id": "P-test",
            "parser_name": "MinerU",
            "parser_version": "4.0.7",
        },
        formula_contexts={
            locator: {
                "page": 1,
                "block_type": "Formula block",
                "markdown_math": math,
                "related_text_block_ids": [text_block.id],
            }
        },
        text_blocks=[text_block],
    )

    assert len(equations) == 1
    assert equations[0].content == math
    source = json.loads(equations[0].source_reference)
    assert source["representation_type"] == "markdown_math"
    assert source["equation_number"] == "7"
