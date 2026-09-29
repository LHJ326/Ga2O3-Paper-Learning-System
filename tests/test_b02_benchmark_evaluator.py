import hashlib
from pathlib import Path

import pytest

from src.benchmark.evaluator import calculate_metrics, evaluate_benchmark


PROJECT_ROOT = Path(__file__).resolve().parents[1]
B02_ROOT = PROJECT_ROOT / "data" / "benchmark" / "B02"
RAW_ROOT = PROJECT_ROOT / "data" / "parsed" / "B02" / "mineru" / "raw"
GROUND_TRUTH = B02_ROOT / "B02_GROUND_TRUTH.yaml"
MIDDLE_JSON = RAW_ROOT / "middle_json" / "B02.json"
RAW_REVIEW = B02_ROOT / "B02_RAW_REVIEW.yaml"


@pytest.fixture(scope="module")
def result() -> dict:
    return evaluate_benchmark(GROUND_TRUTH, MIDDLE_JSON, RAW_REVIEW)


def test_b02_frozen_raw_hashes() -> None:
    expected = {
        RAW_ROOT / "markdown" / "B02.md": (
            "BD29EE13FD294D8011F951AEB6FC4B7686ABF1030C396B49CB11FB56D3E2DF29"
        ),
        MIDDLE_JSON: (
            "E1A2E3F8E2BD2D295FC95F536BAB69CBA196376D85FF0706212C5A59A78C9E1D"
        ),
        RAW_ROOT / "zip" / "B02.zip": (
            "A01FAAC480C30811D39B3468525DE6851422644A7EC40D046F3DA5420815B9E3"
        ),
    }
    for path, digest in expected.items():
        if path.suffix == ".zip" and not path.exists():
            # Public clones intentionally exclude third-party MinerU archives.
            # A locally supplied frozen archive is still hash-checked below.
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == digest


def test_zero_prediction_precision_is_not_applicable() -> None:
    metrics = calculate_metrics(2, 0, 0)
    assert metrics == {
        "ground_truth_count": 2,
        "predicted_count": 0,
        "tp": 0,
        "fp": 0,
        "fn": 2,
        "precision": None,
        "recall": 0.0,
        "f1": 0.0,
    }


def test_b02_zero_predicted_tables_and_error_cases(result: dict) -> None:
    tables = result["metrics"]["tables"]
    assert (tables["tp"], tables["fp"], tables["fn"]) == (0, 0, 2)
    assert tables["precision"] is None
    assert tables["precision_policy"] == "not_applicable_no_predictions"
    assert tables["recall"] == 0.0
    assert [case["error_type"] for case in tables["error_cases"]] == [
        "TABLE_BODY_MISSING",
        "TABLE_MISCLASSIFIED_AS_IMAGE",
    ]


def test_b02_layer_a_and_layer_b_are_independent(result: dict) -> None:
    layer_a = result["metrics"]
    layer_b = result["layer_b"]
    assert result["evaluation_layer"] == "Layer A: MinerU Raw Output"
    assert layer_b["evaluation_layer"] == (
        "Layer B: MinerUAdapter v2 / Unified Document"
    )
    assert layer_a is not layer_b["metrics"]
    assert layer_a["figures"]["predicted_count"] == 26
    assert layer_b["metrics"]["figures"]["predicted_count"] == 16
    assert layer_b["document_counts"] == {
        "pages": 12,
        "sections": 27,
        "text_blocks": 133,
        "figures": 16,
        "equations": 10,
        "tables": 0,
    }
    assert layer_a["tables"]["error_cases"] is not layer_b["metrics"]["tables"]["error_cases"]


def test_b02_equation_metrics(result: dict) -> None:
    for equations in (
        result["metrics"]["equations"],
        result["layer_b"]["metrics"]["equations"],
    ):
        assert (equations["tp"], equations["fp"], equations["fn"]) == (9, 1, 0)
        assert equations["precision"] == pytest.approx(0.9)
        assert equations["recall"] == 1.0
        assert equations["f1"] == pytest.approx(18 / 19)


def test_b02_figure_and_caption_metrics(result: dict) -> None:
    raw_figures = result["metrics"]["figures"]
    assert (raw_figures["tp"], raw_figures["fp"], raw_figures["fn"]) == (20, 6, 0)
    raw_captions = result["metrics"]["captions"]
    assert raw_captions["predicted_count"] == 17
    assert (raw_captions["tp"], raw_captions["fp"], raw_captions["fn"]) == (17, 0, 3)

    adapter_figures = result["layer_b"]["metrics"]["figures"]
    assert (adapter_figures["tp"], adapter_figures["fp"], adapter_figures["fn"]) == (16, 0, 4)
    adapter_captions = result["layer_b"]["metrics"]["captions"]
    assert (adapter_captions["tp"], adapter_captions["fp"], adapter_captions["fn"]) == (16, 0, 4)


def test_b02_main_sections_and_subsections(result: dict) -> None:
    for layer in (result["metrics"], result["layer_b"]["metrics"]):
        sections = layer["sections"]
        assert (sections["tp"], sections["fp"], sections["fn"]) == (5, 0, 0)
        subsections = sections["subsections"]
        assert (subsections["tp"], subsections["fp"], subsections["fn"]) == (15, 0, 0)


def test_b02_reading_order_issue_is_preserved(result: dict) -> None:
    assert any(
        error["type"] == "READING_ORDER_ERROR_PAGE_11"
        for error in result["known_errors"]
    )
