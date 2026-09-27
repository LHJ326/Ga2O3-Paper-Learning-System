"""Evaluate independent lightweight OCR Table recovery as benchmark Layer C."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import yaml

from .evaluator import calculate_metrics
from ..parser.table_recovery import (
    ReconstructedTable,
    SpatialTableReconstructor,
    load_ocr_tokens,
    load_recovery_manifest,
    normalize_ocr_text,
)


_SEMANTIC_TRANSLATION = str.maketrans(
    {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
     "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
)


def _read_mapping(path: Path) -> dict[str, Any]:
    if path.suffix.casefold() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping: {path}")
    return value


def _semantic_key(value: Any) -> str:
    return normalize_ocr_text(str(value)).translate(_SEMANTIC_TRANSLATION).casefold()


def _exact_key(value: Any) -> str:
    return normalize_ocr_text(str(value))


def _expected_grid(table: dict[str, Any]) -> tuple[list[str], list[list[str]]]:
    if "logical_rows" in table:
        headers = [str(value) for value in table.get("logical_column_headers", [])]
        rows = [
            [str(value) for value in row.values()]
            for row in table.get("logical_rows", [])
        ]
        return headers, rows
    headers = [str(value) for value in table.get("column_headers", [])]
    rows = [
        [str(row.get("parameter", "")), *map(str, row.get("values", []))]
        for row in table.get("rows", [])
    ]
    return headers, rows


def _alignment_score(expected: int, predicted: int) -> float:
    if expected == predicted == 0:
        return 1.0
    return min(expected, predicted) / max(expected, predicted)


def _evaluate_one_table(
    ground_truth: dict[str, Any], recovered: ReconstructedTable
) -> dict[str, Any]:
    expected_headers, expected_rows = _expected_grid(ground_truth)
    predicted_headers = [cell.normalized_text for cell in recovered.rows[0]]
    predicted_rows = [
        [cell.normalized_text for cell in row] for row in recovered.body_rows
    ]
    expected_cells = sum(len(row) for row in expected_rows)
    occupied_cells = sum(bool(value) for row in predicted_rows for value in row)
    aligned_pairs = [
        (expected, predicted)
        for expected_row, predicted_row in zip(expected_rows, predicted_rows)
        for expected, predicted in zip(expected_row, predicted_row)
    ]
    exact_matches = sum(
        _exact_key(expected) == _exact_key(predicted)
        for expected, predicted in aligned_pairs
    )
    semantic_matches = sum(
        _semantic_key(expected) == _semantic_key(predicted)
        for expected, predicted in aligned_pairs
    )
    header_pairs = list(zip(expected_headers, predicted_headers))
    header_exact_matches = sum(
        _exact_key(expected) == _exact_key(predicted)
        for expected, predicted in header_pairs
    )
    expected_footnotes = {
        str(item["marker"]): str(item["text"])
        for item in ground_truth.get("footnotes", [])
        if isinstance(item, dict)
    }
    predicted_footnotes = {
        item.marker: item.normalized_text for item in recovered.footnotes
    }
    detected_markers = sorted(expected_footnotes.keys() & predicted_footnotes.keys())
    exact_footnotes = [
        marker
        for marker in detected_markers
        if _exact_key(expected_footnotes[marker])
        == _exact_key(predicted_footnotes[marker])
    ]
    return {
        "table_id": recovered.table_id,
        "page": recovered.page,
        "structure": {
            "expected_logical_rows": len(expected_rows),
            "predicted_logical_rows": len(predicted_rows),
            "expected_logical_columns": len(expected_headers),
            "predicted_logical_columns": recovered.column_count,
            "row_alignment": _alignment_score(len(expected_rows), len(predicted_rows)),
            "column_alignment": _alignment_score(len(expected_headers), recovered.column_count),
        },
        "cell_occupancy": {
            "expected_cells": expected_cells,
            "occupied_cells": occupied_cells,
            "rate": 1.0 if expected_cells == 0 else occupied_cells / expected_cells,
        },
        "exact_normalized_cells": {
            "matched": exact_matches,
            "total": expected_cells,
            "rate": 1.0 if expected_cells == 0 else exact_matches / expected_cells,
        },
        "semantic_normalized_cells": {
            "matched": semantic_matches,
            "total": expected_cells,
            "rate": 1.0 if expected_cells == 0 else semantic_matches / expected_cells,
        },
        "headers": {
            "expected": expected_headers,
            "predicted": predicted_headers,
            "exact_matches": header_exact_matches,
            "total": len(expected_headers),
        },
        "footnotes": {
            "expected_count": len(expected_footnotes),
            "predicted_count": len(predicted_footnotes),
            "detected_markers": detected_markers,
            "exact_markers": exact_footnotes,
            "predicted": predicted_footnotes,
        },
        "confidence": recovered.confidence_summary,
    }


def evaluate_table_recovery(
    ground_truth_path: str | Path,
    baseline_result_path: str | Path,
    recovery_manifest_path: str | Path,
) -> dict[str, Any]:
    """Evaluate Layer C while preserving the frozen Layer A/B payloads."""
    ground_truth_path = Path(ground_truth_path)
    baseline_result_path = Path(baseline_result_path)
    recovery_manifest_path = Path(recovery_manifest_path)
    ground_truth = _read_mapping(ground_truth_path)
    baseline = _read_mapping(baseline_result_path)
    paper_id, specs = load_recovery_manifest(recovery_manifest_path)
    reconstructor = SpatialTableReconstructor()
    recovered = [
        reconstructor.reconstruct(load_ocr_tokens(spec), spec)
        for spec in specs
    ]

    gt_tables = {
        str(table["table_number"]): table
        for table in ground_truth.get("tables", [])
    }
    recovered_by_id = {table.table_id: table for table in recovered}
    matched_ids = sorted(gt_tables.keys() & recovered_by_id.keys())
    detection = calculate_metrics(
        len(gt_tables), len(recovered_by_id), len(matched_ids)
    )
    per_table = [
        _evaluate_one_table(gt_tables[table_id], recovered_by_id[table_id])
        for table_id in matched_ids
    ]
    expected_cells = sum(
        item["exact_normalized_cells"]["total"] for item in per_table
    )
    exact_matches = sum(
        item["exact_normalized_cells"]["matched"] for item in per_table
    )
    semantic_matches = sum(
        item["semantic_normalized_cells"]["matched"] for item in per_table
    )
    unified_tables = [
        table.to_unified_table(paper_id=paper_id) for table in recovered
    ]
    layer_c = {
        "status": "EVALUATED",
        "evaluation_layer": "Layer C: Lightweight OCR Table Recovery",
        "method": "PyMuPDF crop + PP-OCR result + deterministic spatial reconstruction",
        "runtime_ocr_invoked": False,
        "tables": detection,
        "structure": {
            "per_table": per_table,
            "aggregate_exact_normalized_cells": {
                "matched": exact_matches,
                "total": expected_cells,
                "rate": exact_matches / expected_cells if expected_cells else 1.0,
            },
            "aggregate_semantic_normalized_cells": {
                "matched": semantic_matches,
                "total": expected_cells,
                "rate": semantic_matches / expected_cells if expected_cells else 1.0,
            },
        },
        "unified_tables": [
            {
                "id": table.id,
                "page": table.page_number,
                "content": json.loads(table.content),
                "evidence": json.loads(table.source_reference),
            }
            for table in unified_tables
        ],
    }
    return {
        "benchmark_id": baseline["benchmark_id"],
        "baseline_result": baseline_result_path.as_posix(),
        "inputs": {
            "ground_truth": ground_truth_path.as_posix(),
            "recovery_manifest": recovery_manifest_path.as_posix(),
        },
        "layer_a": {
            "evaluation_layer": baseline["evaluation_layer"],
            "metrics": copy.deepcopy(baseline["metrics"]),
        },
        "layer_b": copy.deepcopy(baseline["layer_b"]),
        "layer_c": layer_c,
    }


def write_result(result: dict[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("baseline_result", type=Path)
    parser.add_argument("recovery_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_result(
        evaluate_table_recovery(
            args.ground_truth,
            args.baseline_result,
            args.recovery_manifest,
        ),
        args.output,
    )


if __name__ == "__main__":
    main()
