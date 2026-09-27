import json
from pathlib import Path

import pytest

from src.parser.adapters import MinerUAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
B01_RAW = PROJECT_ROOT / "data" / "parsed" / "B01" / "mineru" / "raw"
P001_RAW = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _payload() -> dict:
    return {
        "schema": "docvortex.middle",
        "schema_version": "2.0",
        "is_full_document": True,
        "metadata": {
            "producer": {"name": "mineru", "version": "4.0.7"},
            "document": {"page_count": 2},
        },
        "extensions": {},
        "pages": [
            {
                "page_idx": 0,
                "blocks": [
                    {"type": "header", "index": 0, "bbox": [0, 0, 1, 0.05], "content": [{"type": "text", "content": "HEADER"}]},
                    {"type": "doc_title", "index": 1, "bbox": [0, 0.1, 1, 0.2], "content": [{"type": "text", "content": "Paper title"}]},
                    {"type": "paragraph_title", "index": 2, "level": 2, "bbox": [0, 0.2, 1, 0.25], "content": [{"type": "text", "content": "1. Introduction"}]},
                    {"type": "text", "index": 3, "bbox": [0, 0.3, 1, 0.4], "content": [{"type": "text", "content": "See Figure 1."}]},
                    {"type": "image", "index": 4, "bbox": [0, 0.4, 1, 0.7], "content": [
                        {"type": "image_body", "index": 4, "content": ""},
                        {"type": "image_caption", "index": 5, "bbox": [0, 0.7, 1, 0.75], "content": [{"type": "text", "content": "Figure 1. A result."}]},
                    ]},
                    {"type": "equation", "index": 6, "bbox": [0.2, 0.8, 0.8, 0.85], "content": "x=1"},
                    {"type": "table", "index": 7, "bbox": [0.1, 0.86, 0.9, 0.95], "content": [{"type": "text", "content": "A | B"}]},
                    {"type": "footer", "index": 8, "bbox": [0, 0.96, 1, 1], "content": [{"type": "text", "content": "FOOTER"}]},
                ],
            },
            {
                "page_idx": 1,
                "blocks": [
                    {"type": "page_footnote", "index": 0, "bbox": [0, 0.9, 1, 1], "content": [{"type": "text", "content": "NOTE"}]},
                    {"type": "equation", "index": 1, "bbox": [0.8, 0.01, 0.95, 0.06], "content": ""},
                ],
            },
        ],
    }


def _write_middle(tmp_path: Path, payload: dict) -> Path:
    raw_root = tmp_path / "raw"
    middle_dir = raw_root / "middle_json"
    middle_dir.mkdir(parents=True)
    (middle_dir / "T01.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return raw_root


def test_middle_json_schema_and_version_are_required(tmp_path: Path) -> None:
    wrong_schema = _payload()
    wrong_schema["schema"] = "other"
    with pytest.raises(ValueError, match="Unsupported middle_json schema"):
        MinerUAdapter().convert(_write_middle(tmp_path / "schema", wrong_schema))

    wrong_version = _payload()
    wrong_version["schema_version"] = "1.0"
    with pytest.raises(ValueError, match="Unsupported docvortex.middle"):
        MinerUAdapter().convert(_write_middle(tmp_path / "version", wrong_version))


def test_middle_json_converts_typed_blocks_and_evidence(tmp_path: Path) -> None:
    document = MinerUAdapter().convert(_write_middle(tmp_path, _payload()))

    assert document.document_id == "T01"
    assert [page.page_number for page in document.pages] == [1, 2]
    assert [section.content for section in document.sections] == ["1. Introduction"]
    assert [block.content for block in document.text_blocks] == ["See Figure 1."]
    assert len(document.figures) == 1
    assert json.loads(document.figures[0].content)["caption"] == "Figure 1. A result."
    assert len(document.equations) == 1
    assert document.equations[0].content == "x=1"
    assert len(document.tables) == 1
    assert document.tables[0].content == "A | B"
    assert all(
        marker not in [block.content for block in document.text_blocks]
        for marker in ("HEADER", "FOOTER", "NOTE")
    )

    evidence = document.figures[0].evidence
    assert evidence.page == 1
    assert evidence.mineru_locator == "/pages/0/blocks/4"
    assert evidence.details["json_locator"] == evidence.mineru_locator
    assert evidence.details["raw_block_index"] == 4
    assert evidence.details["bbox"] == [0, 0.4, 1, 0.7]
    assert evidence.details["raw_type"] == "image"
    assert evidence.details["schema"] == "docvortex.middle"
    assert evidence.details["schema_version"] == "2.0"


def test_b01_middle_json_conversion_counts() -> None:
    document = MinerUAdapter().convert(B01_RAW)
    assert (
        len(document.pages),
        len(document.sections),
        len(document.text_blocks),
        len(document.figures),
        len(document.equations),
        len(document.tables),
    ) == (10, 9, 114, 5, 6, 0)


def test_legacy_fallback_regression() -> None:
    document = MinerUAdapter().convert(P001_RAW)
    assert document.document_id == "P001"
    assert (
        len(document.pages),
        len(document.sections),
        len(document.text_blocks),
        len(document.figures),
        len(document.equations),
        len(document.tables),
    ) == (12, 10, 156, 6, 6, 0)
    assert len(document.figure_text_relations) == 40
