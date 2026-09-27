"""Domain-generic deterministic table reconstruction from OCR tokens and bbox."""

from __future__ import annotations

import re
from statistics import mean, median
from typing import Callable

from .models import (
    BoundingBox,
    OCRToken,
    ReconstructedTable,
    TableCell,
    TableFootnote,
    TableRecoverySpec,
)
from .normalizer import normalize_footnote_suffix_spacing, normalize_ocr_text


_FOOTNOTE_SIGNAL_RE = re.compile(
    r"(?:^[A-D](?:\s|[A-Z])|©|[.!?]\s*[A-D][A-Z])"
)
_FOOTNOTE_BOUNDARY_RE = re.compile(
    r"(^|[.!?]\s+)([A-D])(?=[A-Z])"
)


def _cluster_by_coordinate(
    tokens: list[OCRToken],
    coordinate: Callable[[OCRToken], float],
    tolerance: float,
) -> list[list[OCRToken]]:
    clusters: list[list[OCRToken]] = []
    for token in sorted(tokens, key=coordinate):
        if not clusters:
            clusters.append([token])
            continue
        anchor = mean(coordinate(item) for item in clusters[-1])
        if abs(coordinate(token) - anchor) <= tolerance:
            clusters[-1].append(token)
        else:
            clusters.append([token])
    return clusters


class SpatialTableReconstructor:
    """Reconstruct a logical grid from token centers and repeated headers."""

    def __init__(
        self,
        *,
        row_tolerance_height_ratio: float = 0.65,
        column_tolerance_height_ratio: float = 1.6,
        spanning_footnote_width_ratio: float = 0.55,
    ) -> None:
        self.row_tolerance_height_ratio = row_tolerance_height_ratio
        self.column_tolerance_height_ratio = column_tolerance_height_ratio
        self.spanning_footnote_width_ratio = spanning_footnote_width_ratio

    def reconstruct(
        self,
        tokens: list[OCRToken],
        spec: TableRecoverySpec,
    ) -> ReconstructedTable:
        scoped = [
            token for token in tokens if spec.table_region.contains_center(token.bbox)
        ]
        if not scoped:
            raise ValueError(f"No OCR tokens inside table region {spec.table_id}")

        footnote_tokens = [
            token
            for token in scoped
            if token.bbox.width / spec.table_region.width
            >= self.spanning_footnote_width_ratio
            and _FOOTNOTE_SIGNAL_RE.search(token.normalized_text)
        ]
        grid_tokens = [token for token in scoped if token not in footnote_tokens]
        if not grid_tokens:
            raise ValueError(f"No grid tokens inside table region {spec.table_id}")

        typical_height = median(
            token.bbox.height for token in grid_tokens if token.bbox.height > 0
        )
        column_clusters = _cluster_by_coordinate(
            grid_tokens,
            lambda token: token.bbox.center_x,
            max(1.0, typical_height * self.column_tolerance_height_ratio),
        )
        row_clusters = _cluster_by_coordinate(
            grid_tokens,
            lambda token: token.bbox.center_y,
            max(1.0, typical_height * self.row_tolerance_height_ratio),
        )
        column_anchors = [
            mean(token.bbox.center_x for token in cluster)
            for cluster in column_clusters
        ]

        physical_rows: list[list[list[OCRToken]]] = []
        for row_cluster in row_clusters:
            cells: list[list[OCRToken]] = [[] for _ in column_anchors]
            for token in row_cluster:
                column = min(
                    range(len(column_anchors)),
                    key=lambda index: abs(
                        token.bbox.center_x - column_anchors[index]
                    ),
                )
                cells[column].append(token)
            physical_rows.append(cells)

        header = physical_rows[: spec.header_rows]
        body = self._merge_multiline_rows(physical_rows[spec.header_rows :])
        rows = header + body
        rows = self._unfold_repeated_column_groups(rows, spec.header_rows)
        table_cells = self._materialize_cells(rows)
        footnotes = self._extract_footnotes(footnote_tokens)
        return ReconstructedTable(
            table_id=spec.table_id,
            page=spec.page,
            source=spec.raw_artifact.as_posix(),
            coordinate_space=spec.coordinate_space,
            region=spec.table_region,
            header_rows=spec.header_rows,
            rows=table_cells,
            footnotes=footnotes,
            producer=dict(spec.producer),
        )

    @staticmethod
    def _occupancy(row: list[list[OCRToken]]) -> set[int]:
        return {index for index, cell in enumerate(row) if cell}

    @staticmethod
    def _first_text(row: list[list[OCRToken]]) -> str:
        if not row or not row[0]:
            return ""
        return " ".join(
            token.normalized_text
            for token in sorted(row[0], key=lambda token: token.bbox.center_y)
        )

    def _merge_multiline_rows(
        self, rows: list[list[list[OCRToken]]]
    ) -> list[list[list[OCRToken]]]:
        merged: list[list[list[OCRToken]]] = []
        for row in rows:
            if not merged:
                merged.append(row)
                continue
            previous = merged[-1]
            current_occupancy = self._occupancy(row)
            previous_occupancy = self._occupancy(previous)
            current_first = self._first_text(row)
            previous_first = self._first_text(previous)
            continuation = False
            if current_first.startswith("("):
                continuation = True
            elif not previous_first and current_first:
                continuation = True
            elif (
                not current_first
                and previous_first
                and current_occupancy
                and not (current_occupancy & previous_occupancy)
            ):
                continuation = True
            elif (
                not current_first
                and current_occupancy
                and len(current_occupancy) <= 1
                and bool(current_occupancy & previous_occupancy)
            ):
                continuation = True
            if continuation:
                for column, tokens in enumerate(row):
                    previous[column].extend(tokens)
            else:
                merged.append(row)
        return merged

    @staticmethod
    def _header_period(header: list[list[OCRToken]]) -> int | None:
        texts = [
            normalize_ocr_text(" ".join(token.raw_text for token in cell)).casefold()
            for cell in header
        ]
        for period in range(1, len(texts) // 2 + 1):
            if len(texts) % period:
                continue
            if all(texts[index] == texts[index % period] for index in range(len(texts))):
                return period
        return None

    def _unfold_repeated_column_groups(
        self,
        rows: list[list[list[OCRToken]]],
        header_rows: int,
    ) -> list[list[list[OCRToken]]]:
        if not rows or header_rows != 1:
            return rows
        period = self._header_period(rows[0])
        if period is None or period == len(rows[0]):
            return rows
        group_count = len(rows[0]) // period
        unfolded = [rows[0][:period]]
        for group in range(group_count):
            start = group * period
            stop = start + period
            for row in rows[1:]:
                logical_row = row[start:stop]
                if any(logical_row):
                    unfolded.append(logical_row)
        return unfolded

    @staticmethod
    def _materialize_cells(
        rows: list[list[list[OCRToken]]],
    ) -> tuple[tuple[TableCell, ...], ...]:
        materialized: list[tuple[TableCell, ...]] = []
        for row_index, row in enumerate(rows):
            cells: list[TableCell] = []
            for column_index, tokens in enumerate(row):
                ordered = sorted(
                    tokens,
                    key=lambda token: (
                        token.bbox.center_y,
                        token.bbox.x0,
                    ),
                )
                normalized_text = " ".join(
                    token.normalized_text for token in ordered
                )
                normalized_text = normalize_footnote_suffix_spacing(
                    normalized_text
                )
                cells.append(
                    TableCell(
                        row_index=row_index,
                        column_index=column_index,
                        raw_text=" ".join(token.raw_text for token in ordered),
                        normalized_text=normalized_text,
                        token_indices=tuple(token.index for token in ordered),
                        confidence=(
                            mean(token.confidence for token in ordered)
                            if ordered
                            else None
                        ),
                        bbox=BoundingBox.union(
                            [token.bbox for token in ordered]
                        ),
                    )
                )
            materialized.append(tuple(cells))
        return tuple(materialized)

    @staticmethod
    def _extract_footnotes(
        tokens: list[OCRToken],
    ) -> tuple[TableFootnote, ...]:
        footnotes: list[TableFootnote] = []
        for token in sorted(tokens, key=lambda item: item.bbox.center_y):
            prepared = token.normalized_text.replace("©", "\nC ")
            prepared = _FOOTNOTE_BOUNDARY_RE.sub(
                lambda match: f"{match.group(1)}\n{match.group(2)} ",
                prepared,
            )
            for part in prepared.splitlines():
                match = re.match(r"^\s*([A-D])\s*(.+)$", part)
                if match is None:
                    continue
                footnotes.append(
                    TableFootnote(
                        marker=match.group(1),
                        raw_text=part.strip(),
                        normalized_text=normalize_ocr_text(match.group(2)),
                        token_indices=(token.index,),
                    )
                )
        deduplicated = {footnote.marker: footnote for footnote in footnotes}
        return tuple(deduplicated[marker] for marker in sorted(deduplicated))
