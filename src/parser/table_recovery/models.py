"""Typed OCR and reconstructed-table models with traceable Evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Callable

import yaml

from ...schema.document import Evidence, Table
from .normalizer import normalize_ocr_text


@dataclass(frozen=True)
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError(f"Invalid bounding box: {self}")

    @classmethod
    def from_sequence(cls, values: list[float] | tuple[float, ...]) -> BoundingBox:
        if len(values) != 4:
            raise ValueError("A bounding box must contain four coordinates")
        return cls(*(float(value) for value in values))

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def contains_center(self, other: BoundingBox) -> bool:
        return (
            self.x0 <= other.center_x <= self.x1
            and self.y0 <= other.center_y <= self.y1
        )

    def to_list(self) -> list[float]:
        return [self.x0, self.y0, self.x1, self.y1]

    @classmethod
    def union(cls, boxes: list[BoundingBox]) -> BoundingBox | None:
        if not boxes:
            return None
        return cls(
            min(box.x0 for box in boxes),
            min(box.y0 for box in boxes),
            max(box.x1 for box in boxes),
            max(box.y1 for box in boxes),
        )


@dataclass(frozen=True)
class OCRToken:
    index: int
    raw_text: str
    normalized_text: str
    confidence: float
    bbox: BoundingBox
    page: int
    source: str
    coordinate_space: str

    @classmethod
    def create(
        cls,
        *,
        index: int,
        text: str,
        confidence: float,
        bbox: list[float] | tuple[float, ...],
        page: int,
        source: str,
        coordinate_space: str,
        normalizer: Callable[[str], str] = normalize_ocr_text,
    ) -> OCRToken:
        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("OCR confidence must be between zero and one")
        return cls(
            index=int(index),
            raw_text=str(text),
            normalized_text=normalizer(str(text)),
            confidence=float(confidence),
            bbox=BoundingBox.from_sequence(bbox),
            page=int(page),
            source=str(source),
            coordinate_space=str(coordinate_space),
        )


@dataclass(frozen=True)
class TableCell:
    row_index: int
    column_index: int
    raw_text: str
    normalized_text: str
    token_indices: tuple[int, ...]
    confidence: float | None
    bbox: BoundingBox | None

    @property
    def occupied(self) -> bool:
        return bool(self.normalized_text)

    def to_mapping(
        self, *, source: str, page: int, coordinate_space: str
    ) -> dict[str, Any]:
        return {
            "row": self.row_index,
            "column": self.column_index,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "confidence": self.confidence,
            "evidence": {
                "source_file": source,
                "page": page,
                "coordinate_space": coordinate_space,
                "bbox": self.bbox.to_list() if self.bbox else None,
                "token_indices": list(self.token_indices),
                "token_locators": [
                    f"rec_texts[{index}]" for index in self.token_indices
                ],
            },
        }


@dataclass(frozen=True)
class TableFootnote:
    marker: str
    raw_text: str
    normalized_text: str
    token_indices: tuple[int, ...]


@dataclass(frozen=True)
class ReconstructedTable:
    table_id: str
    page: int
    source: str
    coordinate_space: str
    region: BoundingBox
    header_rows: int
    rows: tuple[tuple[TableCell, ...], ...]
    footnotes: tuple[TableFootnote, ...]
    producer: dict[str, Any]

    @property
    def column_count(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    @property
    def body_rows(self) -> tuple[tuple[TableCell, ...], ...]:
        return self.rows[self.header_rows :]

    @property
    def confidence_summary(self) -> dict[str, float | None]:
        values = [
            cell.confidence
            for row in self.rows
            for cell in row
            if cell.confidence is not None
        ]
        return {
            "minimum": min(values) if values else None,
            "mean": mean(values) if values else None,
            "maximum": max(values) if values else None,
        }

    def to_unified_table(self, *, paper_id: str) -> Table:
        token_indices = sorted(
            {
                index
                for row in self.rows
                for cell in row
                for index in cell.token_indices
            }
        )
        payload = {
            "table_id": self.table_id,
            "header_rows": self.header_rows,
            "logical_rows": len(self.body_rows),
            "logical_columns": self.column_count,
            "coordinate_space": self.coordinate_space,
            "region": self.region.to_list(),
            "rows": [
                [
                    cell.to_mapping(
                        source=self.source,
                        page=self.page,
                        coordinate_space=self.coordinate_space,
                    )
                    for cell in row
                ]
                for row in self.rows
            ],
            "footnotes": [
                {
                    "marker": footnote.marker,
                    "raw_text": footnote.raw_text,
                    "normalized_text": footnote.normalized_text,
                    "token_indices": list(footnote.token_indices),
                }
                for footnote in self.footnotes
            ],
        }
        evidence = Evidence(
            paper_id=paper_id,
            parser_name="lightweight_ocr",
            parser_version=str(self.producer.get("version", "unknown")),
            source_file=self.source,
            page=self.page,
            details={
                "source": "lightweight_ocr",
                "producer": dict(self.producer),
                "coordinate_space": self.coordinate_space,
                "table_region": self.region.to_list(),
                "token_indices": token_indices,
                "token_locators": [
                    f"rec_texts[{index}]" for index in token_indices
                ],
                "ocr_confidence_summary": self.confidence_summary,
            },
        )
        return Table(
            id=f"{paper_id}-table-{self.table_id}",
            page_number=self.page,
            content=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            source_reference=evidence.to_source_reference(),
        )


@dataclass(frozen=True)
class TableRecoverySpec:
    table_id: str
    page: int
    raw_artifact: Path
    sha256: str
    table_region: BoundingBox
    coordinate_space: str
    header_rows: int
    producer: dict[str, Any]


def load_ocr_tokens(spec: TableRecoverySpec) -> list[OCRToken]:
    payload = json.loads(spec.raw_artifact.read_text(encoding="utf-8"))
    texts = payload.get("rec_texts")
    scores = payload.get("rec_scores")
    boxes = payload.get("rec_boxes")
    if not all(isinstance(values, list) for values in (texts, scores, boxes)):
        raise ValueError(
            "OCR result must contain rec_texts, rec_scores, and rec_boxes arrays"
        )
    if not (len(texts) == len(scores) == len(boxes)):
        raise ValueError("OCR result arrays must have equal lengths")
    digest = hashlib.sha256(spec.raw_artifact.read_bytes()).hexdigest().upper()
    if digest != spec.sha256.upper():
        raise ValueError(f"OCR artifact checksum mismatch: {spec.raw_artifact}")
    return [
        OCRToken.create(
            index=index,
            text=text,
            confidence=score,
            bbox=box,
            page=spec.page,
            source=spec.raw_artifact.as_posix(),
            coordinate_space=spec.coordinate_space,
        )
        for index, (text, score, box) in enumerate(zip(texts, scores, boxes))
    ]


def load_recovery_manifest(
    path: str | Path,
) -> tuple[str, list[TableRecoverySpec]]:
    manifest_path = Path(path)
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Recovery manifest must be a mapping")
    candidates = [manifest_path.parent, *manifest_path.parents]
    project_root = next(
        (candidate for candidate in candidates if (candidate / "pyproject.toml").is_file()),
        Path.cwd(),
    )
    producer = dict(payload.get("producer", {}))
    coordinate_space = str(payload.get("coordinate_space", "crop_pixels"))
    specs: list[TableRecoverySpec] = []
    for item in payload.get("tables", []):
        artifact = Path(str(item["raw_artifact"]))
        if not artifact.is_absolute():
            artifact = project_root / artifact
        specs.append(
            TableRecoverySpec(
                table_id=str(item["table_id"]),
                page=int(item["page"]),
                raw_artifact=artifact,
                sha256=str(item["sha256"]),
                table_region=BoundingBox.from_sequence(item["table_region"]),
                coordinate_space=coordinate_space,
                header_rows=int(item.get("header_rows", 1)),
                producer=producer,
            )
        )
    return str(payload["paper_id"]), specs
