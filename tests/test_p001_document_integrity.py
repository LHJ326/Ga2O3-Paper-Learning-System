import hashlib
import json
from collections import Counter
from pathlib import Path

from src.parser.adapters import MinerUAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"
RAW_OUTPUT_SHA256 = "284c94c19cb634a3c17b592137a482603f213248b9178d6c6a7a1fd827358bb8"
REQUIRED_EVIDENCE = {
    "paper_id",
    "parser_name",
    "parser_version",
    "source_file",
    "page",
}


def _document():
    return MinerUAdapter().convert(P001_RAW_OUTPUT)


def _collections(document):
    return {
        "pages": document.pages,
        "sections": document.sections,
        "text_blocks": document.text_blocks,
        "figures": document.figures,
        "equations": document.equations,
        "tables": document.tables,
    }


def test_document_structure_and_ids_are_complete_unique_and_stable() -> None:
    document = _document()
    repeated = _document()
    collections = _collections(document)

    assert document.document_id == "P001"
    assert document.metadata is not None
    assert {name: len(items) for name, items in collections.items()} == {
        "pages": 12,
        "sections": 10,
        "text_blocks": 156,
        "figures": 6,
        "equations": 6,
        "tables": 0,
    }

    all_ids = [item.id for items in collections.values() for item in items]
    assert all(all_ids)
    assert len(all_ids) == 190
    assert len(set(all_ids)) == len(all_ids)
    for name, items in collections.items():
        assert [item.id for item in items] == [
            item.id for item in getattr(repeated, name)
        ]


def test_pages_are_continuous_and_all_element_pages_are_valid() -> None:
    document = _document()
    collections = _collections(document)

    assert [page.page_number for page in document.pages] == list(range(1, 13))
    for items in collections.values():
        for item in items:
            assert item.page_number is not None
            assert 1 <= item.page_number <= 12


def test_evidence_references_are_complete() -> None:
    document = _document()

    for element in [
        *document.figures,
        *document.equations,
        *document.text_blocks,
    ]:
        reference = json.loads(element.source_reference)
        assert REQUIRED_EVIDENCE <= reference.keys()
        assert reference["paper_id"] == document.document_id

    for element in [*document.figures, *document.equations]:
        assert json.loads(element.source_reference)["mineru_locator"]


def test_figure_and_equation_relationships_have_no_dangling_ids() -> None:
    document = _document()
    collections = _collections(document)
    all_ids = {
        item.id for items in collections.values() for item in items
    }
    figures = {figure.id: figure for figure in document.figures}
    text_blocks = {block.id: block for block in document.text_blocks}

    for figure in document.figures:
        payload = json.loads(figure.content)
        source = json.loads(figure.source_reference)
        assert source["related_ids"] == payload["related_text_block_ids"]
        for text_block_id in payload["related_text_block_ids"]:
            assert text_block_id in text_blocks
            text_source = json.loads(text_blocks[text_block_id].source_reference)
            assert figure.id in text_source["related_ids"]

    for equation in document.equations:
        source = json.loads(equation.source_reference)
        for text_block_id in source["related_ids"]:
            assert text_block_id in text_blocks
            assert equation.id in json.loads(
                text_blocks[text_block_id].source_reference
            )["related_ids"]

    for text_block in document.text_blocks:
        source = json.loads(text_block.source_reference)
        assert set(source.get("related_ids", [])) <= all_ids
        for reference in source.get("figure_references", []):
            if reference["reference_type"] == "supplementary_figure":
                assert reference["figure_id"] is None
            elif reference["status"] == "resolved":
                assert reference["figure_id"] in figures


def test_duplicates_and_asset_types_do_not_pollute_document_semantics() -> None:
    document = _document()
    figure_sources = [
        json.loads(figure.source_reference) for figure in document.figures
    ]
    equation_sources = [
        json.loads(equation.source_reference) for equation in document.equations
    ]

    assert len(
        {json.loads(figure.content)["figure_number"] for figure in document.figures}
    ) == len(document.figures)
    assert len({source["mineru_locator"] for source in figure_sources}) == 6
    assert len({section.content for section in document.sections}) == 10
    assert {
        source["mineru_locator"] for source in figure_sources
    }.isdisjoint(
        source["mineru_locator"] for source in equation_sources
    )
    assert document.tables == []

    duplicate_blocks = {
        content
        for content, count in Counter(
            block.content.strip() for block in document.text_blocks
        ).items()
        if content and count > 1
    }
    assert duplicate_blocks == set()


def test_raw_output_snapshot_is_unchanged() -> None:
    digest = hashlib.sha256()
    files = sorted(path for path in P001_RAW_OUTPUT.rglob("*") if path.is_file())
    assert len(files) == 24
    for path in files:
        digest.update(path.relative_to(P001_RAW_OUTPUT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())

    assert digest.hexdigest() == RAW_OUTPUT_SHA256
