import json
from pathlib import Path

from src.parser.adapters import MinerUAdapter
from src.schema.document import Figure, TextBlock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _converted_evidence():
    document = MinerUAdapter().convert(P001_RAW_OUTPUT)
    figures = {
        json.loads(figure.content)["figure_number"]: figure
        for figure in document.figures
    }
    text_blocks = {block.id: block for block in document.text_blocks}
    return document, figures, text_blocks


def test_figures_one_through_six_remain_available() -> None:
    document, figures, _ = _converted_evidence()

    assert len(document.figures) == 6
    assert set(figures) == {"1", "2", "3", "4", "5", "6"}


def test_explicit_body_references_create_bidirectional_links() -> None:
    _, figures, text_blocks = _converted_evidence()

    assert any(json.loads(figure.content)["related_text_block_ids"] for figure in figures.values())
    for figure in figures.values():
        payload = json.loads(figure.content)
        figure_source = json.loads(figure.source_reference)
        assert figure_source["related_ids"] == payload["related_text_block_ids"]
        for text_block_id in payload["related_text_block_ids"]:
            text_source = json.loads(text_blocks[text_block_id].source_reference)
            assert figure.id in text_source["related_ids"]
            assert any(
                reference["figure_id"] == figure.id
                and reference["status"] == "resolved"
                for reference in text_source["figure_references"]
            )


def test_subfigure_references_link_to_parent_without_fake_figures() -> None:
    adapter = MinerUAdapter()
    references = adapter._detect_figure_references(
        "Figure 2(a), Fig. 3b, and Figs. 4 and 5 show the result."
    )

    assert [reference["figure_number"] for reference in references] == [
        "2",
        "3",
        "4",
        "5",
    ]
    assert references[0]["subfigure_hint"] == "a"
    assert references[1]["subfigure_hint"] == "b"
    assert all(
        reference["reference_type"] == "main_figure"
        for reference in references
    )
    assert references[0]["normalized_reference"] == "Figure 2a"

    document, figures, _ = _converted_evidence()
    assert set(figures) == {"1", "2", "3", "4", "5", "6"}
    assert all("2a" not in figure.id for figure in document.figures)


def test_supplementary_references_are_classified_without_fake_figures() -> None:
    document, figures, _ = _converted_evidence()
    supplementary = []
    for text_block in document.text_blocks:
        supplementary.extend(
            reference
            for reference in json.loads(text_block.source_reference)[
                "figure_references"
            ]
            if reference["status"] == "supplementary"
        )

    assert len(supplementary) == 23
    assert all(reference["supplementary"] for reference in supplementary)
    assert all(
        reference["reference_type"] == "supplementary_figure"
        for reference in supplementary
    )
    assert all(
        reference["normalized_reference"].startswith("Figure S")
        for reference in supplementary
    )
    assert set(figures) == {"1", "2", "3", "4", "5", "6"}
    assert all(reference["figure_id"] is None for reference in supplementary)

    detected = MinerUAdapter()._detect_figure_references(
        "Fig.S1, Figure S2a, and Figure S4b–d are in Supporting Information."
    )
    assert [reference["normalized_reference"] for reference in detected] == [
        "Figure S1",
        "Figure S2a",
        "Figure S4b-d",
    ]


def test_truly_unresolved_is_distinct_from_supplementary() -> None:

    synthetic_figure = Figure(
        id="P-test-figure-001",
        page_number=1,
        content=json.dumps({"figure_number": "1"}),
        source_reference=json.dumps({"page": 1}),
    )
    synthetic_text = TextBlock(
        id="P-test-text-0001",
        page_number=1,
        content="As shown in Figure 99, the target is intentionally absent.",
        source_reference=json.dumps({"page": 1}),
    )
    MinerUAdapter()._link_figure_text_evidence(
        [synthetic_figure], [synthetic_text]
    )
    synthetic_reference = json.loads(synthetic_text.source_reference)[
        "figure_references"
    ][0]
    assert synthetic_reference["status"] == "unresolved"
    assert synthetic_reference["reference_type"] == "unresolved"
    assert synthetic_reference["normalized_reference"] == "Figure 99"
    assert synthetic_reference["supplementary"] is False
    assert synthetic_reference["figure_id"] is None
    assert json.loads(synthetic_figure.content)["related_text_block_ids"] == []


def test_source_references_preserve_evidence_fields() -> None:
    document, _, _ = _converted_evidence()
    required = {
        "paper_id",
        "parser_name",
        "parser_version",
        "source_file",
        "page",
        "mineru_locator",
    }

    for figure in document.figures:
        assert required <= json.loads(figure.source_reference).keys()
    for text_block in document.text_blocks:
        assert required <= json.loads(text_block.source_reference).keys()
