import json
from pathlib import Path

from src.benchmark.table_recovery_evaluator import evaluate_table_recovery
from src.parser.table_recovery import (
    SpatialTableReconstructor,
    load_ocr_tokens,
    load_recovery_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
GT = ROOT / "data" / "benchmark" / "B02" / "B02_GROUND_TRUTH.yaml"
BASELINE = ROOT / "data" / "benchmark" / "B02" / "B02_BENCHMARK_RESULT.json"
MANIFEST = ROOT / "data" / "parsed" / "B02" / "light_ocr" / "B02_LIGHT_OCR_MANIFEST.yaml"


def recovered_tables():
    paper_id, specs = load_recovery_manifest(MANIFEST)
    tables = [
        SpatialTableReconstructor().reconstruct(load_ocr_tokens(spec), spec)
        for spec in specs
    ]
    return paper_id, tables


def test_b02_table_i_fixture_reconstructs_ten_by_three() -> None:
    _, tables = recovered_tables()
    table = tables[0]
    assert len(table.body_rows) == 10
    assert table.column_count == 3
    assert [cell.normalized_text for cell in table.rows[0]] == [
        "Test", "P-value", "Pass?"
    ]
    assert [cell.normalized_text for cell in table.body_rows[0]] == [
        "Frequency", "0.8343", "Yes"
    ]
    assert [cell.normalized_text for cell in table.body_rows[-1]] == [
        "AppEN", "0.1388", "Yes"
    ]


def test_b02_table_ii_fixture_reconstructs_fourteen_by_seven() -> None:
    _, tables = recovered_tables()
    table = tables[1]
    assert len(table.body_rows) == 14
    assert table.column_count == 7
    assert [cell.normalized_text for cell in table.rows[0]][1:] == [
        "D-Wave[7]", "JSSC'16[19]", "JSSC'21[35]",
        "JSSC'22[21]", "JSSC'22[22]", "This Work",
    ]
    rows = [[cell.normalized_text for cell in row] for row in table.body_rows]
    assert rows[1][1] == "Ultra-Low Temp. (15mK)"
    assert rows[8][1] == "Chimera (6×Spins)"
    assert rows[9][4] == "216μm2 B (1.54x)"
    assert rows[-1][-1] == "Max-cut & Image Segmentation"
    assert [footnote.marker for footnote in table.footnotes] == ["A", "B", "C", "D"]


def test_b02_unified_table_evidence_reaches_tokens_and_raw_artifact() -> None:
    paper_id, tables = recovered_tables()
    unified = tables[1].to_unified_table(paper_id=paper_id)
    evidence = unified.evidence
    payload = json.loads(unified.content)
    assert evidence.parser_name == "lightweight_ocr"
    assert evidence.page == 11
    assert evidence.details["coordinate_space"] == "crop_pixels"
    assert evidence.details["table_region"] == [45.0, 55.0, 1960.0, 1205.0]
    assert evidence.details["token_locators"][0].startswith("rec_texts[")
    first_cell_evidence = payload["rows"][1][0]["evidence"]
    assert first_cell_evidence["source_file"].endswith("B02_table_II_ocr.json")
    assert first_cell_evidence["token_indices"]
    assert first_cell_evidence["bbox"] is not None


def test_layer_c_metrics_and_structure_are_computed_from_fixtures() -> None:
    result = evaluate_table_recovery(GT, BASELINE, MANIFEST)
    layer_c = result["layer_c"]
    assert (layer_c["tables"]["tp"], layer_c["tables"]["fp"], layer_c["tables"]["fn"]) == (2, 0, 0)
    assert layer_c["runtime_ocr_invoked"] is False
    table_i, table_ii = layer_c["structure"]["per_table"]
    assert table_i["structure"]["predicted_logical_rows"] == 10
    assert table_i["structure"]["predicted_logical_columns"] == 3
    assert table_i["exact_normalized_cells"] == {"matched": 30, "total": 30, "rate": 1.0}
    assert table_ii["structure"]["predicted_logical_rows"] == 14
    assert table_ii["structure"]["predicted_logical_columns"] == 7
    assert table_ii["cell_occupancy"]["rate"] == 1.0
    assert table_ii["exact_normalized_cells"]["matched"] == 97
    assert table_ii["semantic_normalized_cells"]["matched"] == 98


def test_layer_a_and_b_are_byte_independent_from_layer_c() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    result = evaluate_table_recovery(GT, BASELINE, MANIFEST)
    assert result["layer_a"]["metrics"] == baseline["metrics"]
    assert result["layer_b"] == baseline["layer_b"]
    assert result["layer_c"]["evaluation_layer"] == (
        "Layer C: Lightweight OCR Table Recovery"
    )


def test_layer_c_does_not_invoke_mineru_adapter(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Layer C must not invoke MinerUAdapter")

    monkeypatch.setattr(
        "src.parser.adapters.MinerUAdapter.convert", fail_if_called
    )
    result = evaluate_table_recovery(GT, BASELINE, MANIFEST)
    assert result["layer_c"]["tables"]["tp"] == 2
