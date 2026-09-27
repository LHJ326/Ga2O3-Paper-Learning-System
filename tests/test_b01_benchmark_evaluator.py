from pathlib import Path

import pytest

from src.benchmark.evaluator import calculate_metrics, evaluate_benchmark


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH = PROJECT_ROOT / "data" / "benchmark" / "B01" / "B01_GROUND_TRUTH.yaml"
MIDDLE_JSON = (
    PROJECT_ROOT
    / "data"
    / "parsed"
    / "B01"
    / "mineru"
    / "raw"
    / "middle_json"
    / "B01.json"
)
RAW_REVIEW = PROJECT_ROOT / "data" / "benchmark" / "B01" / "B01_RAW_REVIEW.yaml"


@pytest.fixture(scope="module")
def result() -> dict:
    return evaluate_benchmark(GROUND_TRUTH, MIDDLE_JSON, RAW_REVIEW)


def test_b01_pages(result: dict) -> None:
    pages = result["metrics"]["pages"]
    assert pages["ground_truth_count"] == 10
    assert pages["predicted_count"] == 10
    assert pages["page_count_match"] is True
    assert pages["page_coverage"] == 1.0


def test_b01_raw_figure_metrics(result: dict) -> None:
    figures = result["metrics"]["figures"]
    assert figures["tp"] == 5
    assert figures["fp"] == 1
    assert figures["fn"] == 0
    assert figures["precision"] == pytest.approx(5 / 6)
    assert figures["recall"] == 1.0


def test_b01_raw_equation_metrics(result: dict) -> None:
    equations = result["metrics"]["equations"]
    assert equations["ground_truth_count"] == 7
    assert equations["predicted_count"] == 8
    assert equations["tp"] == 6
    assert equations["fp"] == 2
    assert equations["fn"] == 1
    assert equations["precision"] == pytest.approx(6 / 8)
    assert equations["recall"] == pytest.approx(6 / 7)


def test_b01_has_no_main_text_tables(result: dict) -> None:
    tables = result["metrics"]["tables"]
    assert tables["ground_truth_count"] == 0
    assert tables["predicted_count"] == 0
    assert tables["true_negative_no_table"] is True


def test_metric_calculation_handles_empty_collections() -> None:
    metrics = calculate_metrics(0, 0, 0)
    assert metrics["fp"] == 0
    assert metrics["fn"] == 0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_layer_b_is_an_explicit_placeholder(result: dict) -> None:
    assert result["evaluation_layer"] == "Layer A: MinerU Raw Output"
    assert result["layer_b"]["status"] == "NOT_EVALUATED"
