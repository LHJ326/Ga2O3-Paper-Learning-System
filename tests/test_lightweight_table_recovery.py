from pathlib import Path

import pytest

from src.parser.table_recovery import (
    BoundingBox,
    OCRToken,
    SpatialTableReconstructor,
    TableRecoverySpec,
    normalize_footnote_suffix_spacing,
    normalize_ocr_text,
    split_footnote_suffix,
)


def token(
    index: int,
    text: str,
    x: float,
    y: float,
    *,
    confidence: float = 0.9,
    width: float = 20,
    height: float = 10,
) -> OCRToken:
    return OCRToken.create(
        index=index,
        text=text,
        confidence=confidence,
        bbox=[x, y, x + width, y + height],
        page=1,
        source="synthetic.json",
        coordinate_space="crop_pixels",
    )


def spec(*, columns: int = 3, header_rows: int = 1) -> TableRecoverySpec:
    return TableRecoverySpec(
        table_id="synthetic",
        page=1,
        raw_artifact=Path("synthetic.json"),
        sha256="unused",
        table_region=BoundingBox(0, 0, columns * 100, 500),
        coordinate_space="crop_pixels",
        header_rows=header_rows,
        producer={"name": "synthetic", "version": "1"},
    )


def test_ocr_token_bbox_parsing_and_geometry() -> None:
    item = token(3, " raw ", 10, 20, width=30, height=12)
    assert item.raw_text == " raw "
    assert item.normalized_text == "raw"
    assert item.bbox == BoundingBox(10, 20, 40, 32)
    assert item.bbox.center_x == 25
    assert item.bbox.center_y == 26
    assert item.bbox.width == 30
    assert item.bbox.height == 12


def test_row_clustering_uses_y_centers() -> None:
    tokens = [
        token(0, "H1", 10, 10), token(1, "H2", 110, 10),
        token(2, "A", 10, 50), token(3, "1", 110, 50),
        token(4, "B", 10, 90), token(5, "2", 110, 90),
    ]
    table = SpatialTableReconstructor().reconstruct(tokens, spec(columns=2))
    assert [[cell.normalized_text for cell in row] for row in table.body_rows] == [
        ["A", "1"], ["B", "2"]
    ]


def test_column_clustering_uses_x_anchors_and_preserves_empty_cells() -> None:
    tokens = [
        token(0, "H1", 10, 10), token(1, "H2", 110, 10), token(2, "H3", 210, 10),
        token(3, "A", 10, 50), token(4, "C", 210, 50),
    ]
    table = SpatialTableReconstructor().reconstruct(tokens, spec())
    row = table.body_rows[0]
    assert table.column_count == 3
    assert [cell.normalized_text for cell in row] == ["A", "", "C"]
    assert row[1].confidence is None
    assert row[1].token_indices == ()


def test_multiline_cells_are_joined_in_reading_order() -> None:
    tokens = [
        token(0, "Label", 10, 10), token(1, "Value", 110, 10),
        token(2, "Room Temp.", 110, 50),
        token(3, "Temperature", 10, 70), token(4, "(300K)", 110, 70),
    ]
    table = SpatialTableReconstructor().reconstruct(tokens, spec(columns=2))
    assert len(table.body_rows) == 1
    assert [cell.normalized_text for cell in table.body_rows[0]] == [
        "Temperature", "Room Temp. (300K)"
    ]


def test_repeated_header_unfolds_side_by_side_column_groups() -> None:
    xs = [10, 70, 130, 210, 270, 330]
    tokens = [
        token(index, text, x, 10)
        for index, (text, x) in enumerate(
            zip(["Name", "Value", "Pass", "Name", "Value", "Pass"], xs)
        )
    ]
    values = ["A", "1", "Yes", "C", "3", "Yes", "B", "2", "Yes", "D", "4", "Yes"]
    for offset, text in enumerate(values):
        row = offset // 6
        column = offset % 6
        tokens.append(token(6 + offset, text, xs[column], 50 + row * 40))
    table = SpatialTableReconstructor().reconstruct(tokens, spec(columns=4))
    assert table.column_count == 3
    assert [[cell.normalized_text for cell in row] for row in table.body_rows] == [
        ["A", "1", "Yes"], ["B", "2", "Yes"],
        ["C", "3", "Yes"], ["D", "4", "Yes"],
    ]


def test_confidence_aggregation_is_mean_and_raw_text_is_preserved() -> None:
    tokens = [
        token(0, "H1", 10, 10), token(1, "H2", 110, 10),
        token(2, "raw  one", 10, 50, confidence=0.8),
        token(3, "two", 10, 62, confidence=1.0),
        token(4, "V", 110, 50, confidence=0.9),
    ]
    table = SpatialTableReconstructor(row_tolerance_height_ratio=2).reconstruct(
        tokens, spec(columns=2)
    )
    cell = table.body_rows[0][0]
    assert cell.raw_text == "raw  one two"
    assert cell.normalized_text == "raw one two"
    assert cell.confidence == pytest.approx(0.9)


def test_normalization_preserves_scientific_numeric_meaning() -> None:
    assert normalize_ocr_text(" 0.5～200MHz  ") == "0.5~200MHz"
    assert normalize_ocr_text("13,888µm²") == "13,888μm²"
    assert normalize_ocr_text("2.85fJ") == "2.85fJ"
    assert normalize_ocr_text("216μm2") == "216μm2"


def test_footnote_suffix_handling_preserves_marker() -> None:
    assert split_footnote_suffix("0.18μWc") == ("0.18μW", "C")
    assert normalize_footnote_suffix_spacing("216μm2B (1.54x)") == (
        "216μm2 B (1.54x)"
    )
    assert normalize_footnote_suffix_spacing("2.85fJ C") == "2.85fJ C"
