"""Evaluate Raw MinerU and Unified Document output against Ground Truth.

Layer A evaluates MinerU ``docvortex.middle`` output. Layer B independently
evaluates the Evidence-preserving MinerUAdapter v2 output.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..parser.adapters import MinerUAdapter
from ..schema.document import Document, DocumentElement


FIGURE_CAPTION_RE = re.compile(r"^\s*(?:figure|fig\.)\s*(\d+)\b", re.IGNORECASE)
LEADING_SECTION_NUMBER_RE = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s*")


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def calculate_metrics(
    ground_truth_count: int,
    predicted_count: int,
    true_positive: int,
) -> dict[str, int | float]:
    """Build count metrics with defined behavior for empty collections.

    An empty Ground Truth and empty prediction is treated as a correct absence
    and receives 1.0 precision, recall, and F1. Other zero denominators resolve
    to 0.0 without raising division errors.
    """

    if min(ground_truth_count, predicted_count, true_positive) < 0:
        raise ValueError("Metric counts must be non-negative")
    if true_positive > ground_truth_count or true_positive > predicted_count:
        raise ValueError("True positives cannot exceed either collection count")

    false_positive = predicted_count - true_positive
    false_negative = ground_truth_count - true_positive

    if predicted_count == 0:
        precision = 1.0 if ground_truth_count == 0 else 0.0
    else:
        precision = true_positive / predicted_count

    if ground_truth_count == 0:
        recall = 1.0 if predicted_count == 0 else 0.0
    else:
        recall = true_positive / ground_truth_count

    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "ground_truth_count": ground_truth_count,
        "predicted_count": predicted_count,
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _content_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_content_text(item) for item in value)
    if isinstance(value, dict):
        return _content_text(value.get("content", ""))
    return ""


def _iter_blocks(raw: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for page in raw.get("pages", []):
        page_number = int(page.get("page_idx", -1)) + 1
        for position, block in enumerate(page.get("blocks", [])):
            if not isinstance(block, dict):
                continue
            yield {
                "page": page_number,
                "position": position,
                "index": block.get("index"),
                "type": block.get("type"),
                "text": _content_text(block.get("content", "")),
                "block": block,
            }
            for nested_position, nested in enumerate(block.get("content", [])):
                if isinstance(nested, dict) and nested.get("type"):
                    yield {
                        "page": page_number,
                        "position": position,
                        "nested_position": nested_position,
                        "index": nested.get("index"),
                        "type": nested.get("type"),
                        "text": _content_text(nested.get("content", "")),
                        "block": nested,
                    }


def _normalize_title(title: str) -> str:
    without_number = LEADING_SECTION_NUMBER_RE.sub("", title)
    return " ".join(without_number.casefold().split())


def _review_metric(
    review_section: dict[str, Any],
    raw_blocks: list[dict[str, Any]],
    raw_type: str,
) -> tuple[dict[str, int | float], list[dict[str, Any]]]:
    reviewed = review_section.get("predictions", [])
    actual = [block for block in raw_blocks if block["type"] == raw_type]
    actual_locators = {(block["page"], block["index"]) for block in actual}
    reviewed_locators = {(item["page"], item["block_index"]) for item in reviewed}
    if actual_locators != reviewed_locators:
        missing = sorted(actual_locators - reviewed_locators)
        unknown = sorted(reviewed_locators - actual_locators)
        raise ValueError(
            f"Raw review annotations do not match {raw_type} blocks; "
            f"unreviewed={missing}, unknown={unknown}"
        )

    ground_truth_numbers = review_section.get("ground_truth_numbers", [])
    true_positives = [item for item in reviewed if item.get("classification") == "true_positive"]
    return (
        calculate_metrics(len(ground_truth_numbers), len(actual), len(true_positives)),
        reviewed,
    )


def _adapter_review_metric(
    review_section: dict[str, Any], elements: list[DocumentElement]
) -> dict[str, Any]:
    reviewed = review_section.get("predictions", [])
    classifications = {
        (int(item["page"]), int(item["block_index"])): item.get("classification")
        for item in reviewed
    }
    predicted_locators: list[tuple[int, int]] = []
    for element in elements:
        evidence = element.evidence
        raw_index = evidence.details.get("raw_block_index")
        if evidence.page is None or not isinstance(raw_index, int):
            raise ValueError(f"Adapter element lacks a raw block locator: {element.id}")
        locator = (evidence.page, raw_index)
        if locator not in classifications:
            raise ValueError(f"Adapter element has an unreviewed raw locator: {locator}")
        predicted_locators.append(locator)
    true_positive = sum(
        classifications[locator] == "true_positive"
        for locator in predicted_locators
    )
    metric = calculate_metrics(
        len(review_section.get("ground_truth_numbers", [])),
        len(elements),
        true_positive,
    )
    metric["adapter_locators"] = [
        {"page": page, "block_index": block_index}
        for page, block_index in predicted_locators
    ]
    return metric


def _evaluate_adapter_layer(
    ground_truth: dict[str, Any],
    review: dict[str, Any],
    document: Document,
) -> dict[str, Any]:
    """Evaluate Unified Document output separately from MinerU Raw output."""
    gt_pages = {int(item["page_number"]) for item in ground_truth.get("pages", [])}
    predicted_pages = {
        page.page_number for page in document.pages if page.page_number is not None
    }
    page_metric = calculate_metrics(
        len(gt_pages), len(predicted_pages), len(gt_pages & predicted_pages)
    )
    page_metric.update(
        {
            "page_count_match": len(gt_pages) == len(predicted_pages),
            "page_coverage": 1.0 if not gt_pages else len(gt_pages & predicted_pages) / len(gt_pages),
            "missing_pages": sorted(gt_pages - predicted_pages),
            "extra_pages": sorted(predicted_pages - gt_pages),
        }
    )

    figure_metric = _adapter_review_metric(review["figures"], document.figures)
    equation_metric = _adapter_review_metric(review["equations"], document.equations)

    figure_numbers = set(review["figures"].get("ground_truth_numbers", []))
    detected_caption_numbers: list[int] = []
    unnumbered_caption_count = 0
    for figure in document.figures:
        payload = json.loads(figure.content)
        caption = str(payload.get("caption") or "")
        match = FIGURE_CAPTION_RE.match(caption)
        if match:
            detected_caption_numbers.append(int(match.group(1)))
        else:
            unnumbered_caption_count += 1
    matched_caption_numbers = sorted(figure_numbers & set(detected_caption_numbers))
    caption_metric = calculate_metrics(
        len(figure_numbers), len(document.figures), len(matched_caption_numbers)
    )
    caption_metric.update(
        {
            "caption_coverage": 1.0 if not figure_numbers else len(matched_caption_numbers) / len(figure_numbers),
            "matched_figure_numbers": matched_caption_numbers,
            "detected_figure_numbers": detected_caption_numbers,
            "unnumbered_caption_count": unnumbered_caption_count,
        }
    )

    gt_sections = ground_truth.get("sections", [])
    gt_main_titles = {
        str(item["title"]): _normalize_title(str(item["title"]))
        for item in gt_sections
    }
    predicted_titles = [section.content.strip() for section in document.sections]
    predicted_normalized = {_normalize_title(title): title for title in predicted_titles}
    matched_titles = [
        title for title, normalized in gt_main_titles.items()
        if normalized in predicted_normalized
    ]
    main_normalized = set(gt_main_titles.values())
    section_metric = calculate_metrics(
        len(gt_main_titles), len(predicted_titles), len(matched_titles)
    )
    section_metric.update(
        {
            "matched_titles": matched_titles,
            "missing_titles": [title for title in gt_main_titles if title not in matched_titles],
            "extra_titles": [title for title in predicted_titles if _normalize_title(title) not in main_normalized],
        }
    )
    gt_subsections = [
        str(subsection["title"])
        for section in gt_sections
        for subsection in section.get("subsections", [])
    ]
    matched_subsections = [
        title for title in gt_subsections
        if any(
            block.content.casefold().startswith(f"{title}:".casefold())
            for block in document.text_blocks
        )
    ]
    section_metric["experimental_subsections"] = {
        "ground_truth_count": len(gt_subsections),
        "matched_count": len(matched_subsections),
        "matched_titles": matched_subsections,
        "missing_titles": [title for title in gt_subsections if title not in matched_subsections],
    }

    gt_tables = ground_truth.get("tables", [])
    table_metric = calculate_metrics(len(gt_tables), len(document.tables), 0)
    table_metric.update(
        {
            "true_negative_no_table": not gt_tables and not document.tables,
            "supplementary_references_excluded": True,
        }
    )
    return {
        "status": "EVALUATED",
        "evaluation_layer": "Layer B: MinerUAdapter v2 / Unified Document",
        "document_counts": {
            "pages": len(document.pages),
            "sections": len(document.sections),
            "text_blocks": len(document.text_blocks),
            "figures": len(document.figures),
            "equations": len(document.equations),
            "tables": len(document.tables),
        },
        "metrics": {
            "pages": page_metric,
            "figures": figure_metric,
            "equations": equation_metric,
            "captions": caption_metric,
            "sections": section_metric,
            "tables": table_metric,
        },
    }


def evaluate_benchmark(
    ground_truth_path: str | Path,
    middle_json_path: str | Path,
    review_annotations_path: str | Path,
) -> dict[str, Any]:
    """Evaluate a reviewed MinerU raw result without changing either input."""

    ground_truth_path = Path(ground_truth_path)
    middle_json_path = Path(middle_json_path)
    review_annotations_path = Path(review_annotations_path)
    ground_truth = _read_yaml(ground_truth_path)
    raw = _read_json(middle_json_path)
    review = _read_yaml(review_annotations_path)

    if raw.get("schema") != "docvortex.middle":
        raise ValueError(f"Unsupported raw schema: {raw.get('schema')!r}")

    blocks = list(_iter_blocks(raw))

    gt_pages = {int(item["page_number"]) for item in ground_truth.get("pages", [])}
    predicted_pages = {int(page["page_idx"]) + 1 for page in raw.get("pages", [])}
    page_metric = calculate_metrics(
        len(gt_pages), len(predicted_pages), len(gt_pages & predicted_pages)
    )
    page_metric.update(
        {
            "page_count_match": len(gt_pages) == len(predicted_pages),
            "page_coverage": 1.0 if not gt_pages else len(gt_pages & predicted_pages) / len(gt_pages),
            "missing_pages": sorted(gt_pages - predicted_pages),
            "extra_pages": sorted(predicted_pages - gt_pages),
        }
    )

    figure_metric, figure_review = _review_metric(review["figures"], blocks, "image")
    figure_metric.update(
        {
            "raw_block_count": figure_metric["predicted_count"],
            "reviewed_predictions": figure_review,
        }
    )

    equation_metric, equation_review = _review_metric(review["equations"], blocks, "equation")
    equation_metric.update(
        {
            "raw_block_count": equation_metric["predicted_count"],
            "reviewed_predictions": equation_review,
        }
    )

    figure_numbers = set(review["figures"].get("ground_truth_numbers", []))
    caption_blocks = [block for block in blocks if block["type"] == "image_caption"]
    detected_caption_numbers: list[int] = []
    unnumbered_caption_count = 0
    for block in caption_blocks:
        match = FIGURE_CAPTION_RE.match(block["text"])
        if match:
            detected_caption_numbers.append(int(match.group(1)))
        else:
            unnumbered_caption_count += 1
    matched_caption_numbers = sorted(figure_numbers & set(detected_caption_numbers))
    caption_metric = calculate_metrics(
        len(figure_numbers), len(caption_blocks), len(matched_caption_numbers)
    )
    caption_metric.update(
        {
            "caption_coverage": (
                1.0 if not figure_numbers else len(matched_caption_numbers) / len(figure_numbers)
            ),
            "matched_figure_numbers": matched_caption_numbers,
            "detected_figure_numbers": detected_caption_numbers,
            "unnumbered_caption_count": unnumbered_caption_count,
        }
    )

    gt_sections = ground_truth.get("sections", [])
    gt_main_titles = {str(item["title"]): _normalize_title(str(item["title"])) for item in gt_sections}
    title_blocks = [block for block in blocks if block["type"] == "paragraph_title"]
    predicted_titles = [block["text"].strip() for block in title_blocks]
    predicted_normalized = {_normalize_title(title): title for title in predicted_titles}
    matched_titles = [
        title for title, normalized in gt_main_titles.items() if normalized in predicted_normalized
    ]
    missing_titles = [title for title in gt_main_titles if title not in matched_titles]
    main_normalized = set(gt_main_titles.values())
    extra_titles = [title for title in predicted_titles if _normalize_title(title) not in main_normalized]
    section_metric = calculate_metrics(
        len(gt_main_titles), len(predicted_titles), len(matched_titles)
    )
    section_metric.update(
        {
            "matched_titles": matched_titles,
            "missing_titles": missing_titles,
            "extra_titles": extra_titles,
        }
    )

    gt_subsections = [
        str(subsection["title"])
        for section in gt_sections
        for subsection in section.get("subsections", [])
    ]
    text_blocks = [block["text"].strip() for block in blocks if block["type"] == "text"]
    matched_subsections = [
        title
        for title in gt_subsections
        if any(text.casefold().startswith(f"{title}:".casefold()) for text in text_blocks)
    ]
    section_metric["experimental_subsections"] = {
        "ground_truth_count": len(gt_subsections),
        "matched_count": len(matched_subsections),
        "matched_titles": matched_subsections,
        "missing_titles": [title for title in gt_subsections if title not in matched_subsections],
    }

    gt_tables = ground_truth.get("tables", [])
    predicted_tables = [block for block in blocks if block["type"] == "table"]
    table_metric = calculate_metrics(len(gt_tables), len(predicted_tables), 0)
    table_metric.update(
        {
            "true_negative_no_table": not gt_tables and not predicted_tables,
            "supplementary_references_excluded": True,
        }
    )

    known_errors = list(review.get("known_errors", []))
    detailed_gt_figure_count = len(ground_truth.get("figures", []))
    reviewed_gt_figure_count = len(figure_numbers)
    if detailed_gt_figure_count != reviewed_gt_figure_count:
        known_errors.append(
            {
                "type": "ground_truth_detail_gap",
                "category": "figures",
                "message": (
                    "Ground Truth YAML contains "
                    f"{detailed_gt_figure_count} detailed Figure records while the manually "
                    f"reviewed benchmark summary confirms {reviewed_gt_figure_count}."
                ),
            }
        )

    adapter_document = MinerUAdapter().convert(middle_json_path.parent.parent)
    layer_b = _evaluate_adapter_layer(ground_truth, review, adapter_document)

    return {
        "benchmark_id": ground_truth.get("metadata", {}).get("benchmark_id", "B01"),
        "parser": review.get("parser", "MinerU"),
        "parser_version": str(review.get("parser_version", "unknown")),
        "raw_schema": raw.get("schema"),
        "raw_schema_version": str(raw.get("schema_version")),
        "evaluation_layer": "Layer A: MinerU Raw Output",
        "inputs": {
            "ground_truth": ground_truth_path.as_posix(),
            "middle_json": middle_json_path.as_posix(),
            "review_annotations": review_annotations_path.as_posix(),
        },
        "metrics": {
            "pages": page_metric,
            "figures": figure_metric,
            "equations": equation_metric,
            "captions": caption_metric,
            "sections": section_metric,
            "tables": table_metric,
        },
        "known_errors": known_errors,
        "layer_b": layer_b,
    }


def write_result(result: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("middle_json", type=Path)
    parser.add_argument("review_annotations", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = evaluate_benchmark(
        args.ground_truth,
        args.middle_json,
        args.review_annotations,
    )
    write_result(result, args.output)


if __name__ == "__main__":
    main()
