import json
import re
from pathlib import Path

from src.parser.adapters import MinerUAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _raw_image_manifest() -> dict[str, object]:
    path = P001_RAW_OUTPUT / "json" / "image_exports.json"
    with path.open(encoding="utf-8-sig") as manifest_file:
        return json.load(manifest_file)


def _formula_locators() -> set[str]:
    markdown = (P001_RAW_OUTPUT / "markdown" / "P001.md").read_text(
        encoding="utf-8-sig"
    )
    return set(
        re.findall(r"!\[Formula block\]\((doc:[^)]+)\)", markdown)
    )


def test_raw_assets_are_preserved_while_document_figures_are_filtered() -> None:
    manifest = _raw_image_manifest()
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)

    assert manifest["count"] == 17
    assert len(manifest["images"]) == 17
    assert len(document.figures) == 6
    assert len(document.figures) < len(manifest["images"])


def test_confirmed_figure_numbers_and_evidence_are_preserved() -> None:
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    payloads = [json.loads(figure.content) for figure in document.figures]

    assert [payload["figure_number"] for payload in payloads] == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    ]
    for figure, payload in zip(document.figures, payloads, strict=True):
        reference = json.loads(figure.source_reference)
        assert payload["caption_status"] == "matched"
        assert payload["caption"]
        assert payload["image_path"]
        assert payload["mineru_block_type"] == "Image block"
        assert reference["page"] == figure.page_number
        assert reference["mineru_locator"]


def test_formula_and_uncaptioned_assets_do_not_become_figures() -> None:
    manifest = _raw_image_manifest()
    raw_locators = {image["locator"] for image in manifest["images"]}
    formula_locators = _formula_locators()
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    figure_locators = {
        json.loads(figure.source_reference)["mineru_locator"]
        for figure in document.figures
    }

    assert len(formula_locators) == 6
    assert formula_locators.isdisjoint(figure_locators)
    assert len(raw_locators - figure_locators) == 11
    assert all(
        json.loads(figure.content)["caption"] is not None
        for figure in document.figures
    )
