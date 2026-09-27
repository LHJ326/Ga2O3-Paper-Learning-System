import json
import re
from pathlib import Path

from src.parser.adapters import MinerUAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _raw_markdown() -> str:
    return (P001_RAW_OUTPUT / "markdown" / "P001.md").read_text(
        encoding="utf-8-sig"
    )


def test_p001_has_only_a_supplementary_textual_table_reference() -> None:
    markdown = _raw_markdown()
    references = re.findall(
        r"\bTable\s+(?:S?\d+|[IVXLCDM]+)\b",
        markdown,
        flags=re.IGNORECASE,
    )

    assert references == ["Table S1"]
    assert "Table S1 (Supporting Information)" in markdown


def test_p001_raw_output_contains_no_structured_or_image_table() -> None:
    markdown = _raw_markdown()
    manifest_path = P001_RAW_OUTPUT / "json" / "image_exports.json"
    with manifest_path.open(encoding="utf-8-sig") as manifest_file:
        manifest = json.load(manifest_file)

    assert re.search(r"<table\b", markdown, flags=re.IGNORECASE) is None
    assert re.search(r"!\[Table block\]\(doc:[^)]+\)", markdown) is None
    assert not any(
        re.match(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+", line)
        for line in markdown.splitlines()
    )
    assert len(manifest["images"]) == 17


def test_convert_keeps_tables_empty_without_misclassifying_assets() -> None:
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)

    assert document.tables == []
    assert len(document.figures) == 6
    assert len(document.equations) == 6

    figure_locators = {
        json.loads(figure.source_reference)["mineru_locator"]
        for figure in document.figures
    }
    equation_locators = {
        json.loads(equation.source_reference)["mineru_locator"]
        for equation in document.equations
    }
    assert figure_locators.isdisjoint(equation_locators)
    assert len(figure_locators | equation_locators) == 12
