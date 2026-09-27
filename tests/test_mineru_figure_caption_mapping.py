import json
from pathlib import Path

from src.parser.adapters import MinerUAdapter
from src.schema.document import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _converted_document() -> Document:
    return MinerUAdapter().convert(P001_RAW_OUTPUT)


def _figure_payloads(document: Document) -> list[dict[str, object]]:
    return [json.loads(figure.content) for figure in document.figures]


def test_p001_conversion_preserves_figure_count() -> None:
    document = _converted_document()

    assert isinstance(document, Document)
    assert len(document.figures) == 17


def test_p001_matches_traceable_numbered_captions() -> None:
    document = _converted_document()
    matched = [
        (figure, payload)
        for figure, payload in zip(
            document.figures, _figure_payloads(document), strict=True
        )
        if payload["caption_status"] == "matched"
    ]

    assert len(matched) == 6
    assert [payload["figure_number"] for _, payload in matched] == [
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
    ]

    for figure, payload in matched:
        caption = payload["caption"]
        caption_source = payload["caption_source_reference"]
        assert isinstance(caption, str) and caption.startswith("Figure ")
        assert isinstance(caption_source, dict)
        assert caption_source["page"] == figure.page_number
        assert caption_source["source_file"] == "json/P001_content.json"
        assert caption_source["relation"] == "same_page_immediately_after_image"


def test_unmatched_images_do_not_receive_synthetic_captions() -> None:
    payloads = _figure_payloads(_converted_document())
    unmatched = [
        payload for payload in payloads if payload["caption_status"] == "unmatched"
    ]

    assert len(unmatched) == 11
    for payload in unmatched:
        assert payload["caption"] is None
        assert payload["figure_number"] is None
        assert payload["caption_source_reference"] is None
