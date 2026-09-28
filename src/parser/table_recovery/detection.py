"""Generic MinerU table-fallback detection from structural evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from .models import BoundingBox


class FallbackStatus(str, Enum):
    NOT_NEEDED = "not_needed"
    CANDIDATE = "candidate"
    TRIGGERED = "triggered"
    RECOVERED = "recovered"
    FAILED = "failed"
    FALLBACK_UNAVAILABLE = "fallback_unavailable"


class TriggerReason(str, Enum):
    TABLE_BODY_MISSING = "TABLE_BODY_MISSING"
    TABLE_MISCLASSIFIED_AS_IMAGE = "TABLE_MISCLASSIFIED_AS_IMAGE"


_TABLE_ANCHOR_RE = re.compile(
    r"^\s*table\s+(?:[ivxlcdm]+|\d+[a-z]?)\s*[.:]?\s*$", re.IGNORECASE
)


def block_text(block: dict[str, Any]) -> str:
    """Flatten DocVortex content without assuming a paper-specific shape."""
    values: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            if isinstance(value.get("text"), str):
                values.append(value["text"])
            content = value.get("content")
            if isinstance(content, str):
                values.append(content)
            elif content is not None:
                visit(content)

    visit(block.get("content"))
    return " ".join(part.strip() for part in values if part.strip()).strip()


def block_bbox(block: dict[str, Any]) -> BoundingBox | None:
    bbox = block.get("bbox")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    try:
        return BoundingBox.from_sequence(bbox)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class SourceAnchor:
    block_index: int
    raw_type: str
    text: str
    bbox: BoundingBox


@dataclass(frozen=True)
class TableFallbackCandidate:
    page: int
    designator: str
    status: FallbackStatus
    reason: TriggerReason
    confidence: float
    anchor: SourceAnchor
    title: SourceAnchor | None
    suspected_image: SourceAnchor | None


class TableFailureDetector:
    """Detect missing or image-misclassified tables in DocVortex middle JSON."""

    def detect(self, payload: dict[str, Any]) -> list[TableFallbackCandidate]:
        pages = payload.get("pages")
        if not isinstance(pages, list):
            return []
        candidates: list[TableFallbackCandidate] = []
        for list_index, page in enumerate(pages):
            if not isinstance(page, dict):
                continue
            page_index = int(page.get("page_idx", list_index))
            blocks = page.get("blocks", [])
            if not isinstance(blocks, list):
                continue
            valid_tables = [
                item for item in blocks
                if isinstance(item, dict) and item.get("type") == "table"
                and self._valid_table(item)
            ]
            for position, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                text = block_text(block)
                bbox = block_bbox(block)
                if bbox is None or _TABLE_ANCHOR_RE.fullmatch(text) is None:
                    continue
                if self._near_existing_table(bbox, valid_tables):
                    continue
                anchor = self._source_anchor(block, position, text, bbox)
                title = self._following_title(blocks, position, bbox)
                image = self._nearby_uncaptioned_image(blocks, position, bbox, title)
                reason = (
                    TriggerReason.TABLE_MISCLASSIFIED_AS_IMAGE
                    if image is not None
                    else TriggerReason.TABLE_BODY_MISSING
                )
                confidence = 0.96 if image is not None else (0.9 if title else 0.72)
                candidates.append(
                    TableFallbackCandidate(
                        page=page_index + 1,
                        designator=text.rstrip(".:").strip(),
                        status=FallbackStatus.CANDIDATE,
                        reason=reason,
                        confidence=confidence,
                        anchor=anchor,
                        title=title,
                        suspected_image=image,
                    )
                )
        return candidates

    @staticmethod
    def _valid_table(block: dict[str, Any]) -> bool:
        content = block.get("content")
        if isinstance(content, str):
            return bool(content.strip())
        return bool(content)

    @staticmethod
    def _near_existing_table(anchor: BoundingBox, tables: Iterable[dict[str, Any]]) -> bool:
        for table in tables:
            bbox = block_bbox(table)
            if bbox is not None and abs(bbox.center_y - anchor.center_y) <= 0.45:
                return True
        return False

    @staticmethod
    def _source_anchor(
        block: dict[str, Any], position: int, text: str, bbox: BoundingBox
    ) -> SourceAnchor:
        return SourceAnchor(
            block_index=int(block.get("index", position)),
            raw_type=str(block.get("type", "unknown")),
            text=text,
            bbox=bbox,
        )

    def _following_title(
        self, blocks: list[Any], position: int, anchor_bbox: BoundingBox
    ) -> SourceAnchor | None:
        for offset, item in enumerate(blocks[position + 1 : position + 4], start=position + 1):
            if not isinstance(item, dict):
                continue
            bbox = block_bbox(item)
            text = block_text(item)
            if bbox is None or not text:
                continue
            if item.get("type") not in {"paragraph_title", "text", "table_caption"}:
                continue
            if bbox.y0 < anchor_bbox.y0 - 0.02 or bbox.y0 > anchor_bbox.y1 + 0.12:
                continue
            return self._source_anchor(item, offset, text, bbox)
        return None

    def _nearby_uncaptioned_image(
        self,
        blocks: list[Any],
        position: int,
        anchor_bbox: BoundingBox,
        title: SourceAnchor | None,
    ) -> SourceAnchor | None:
        search_bottom = (title.bbox.y1 if title else anchor_bbox.y1) + 0.42
        for offset, item in enumerate(blocks[position + 1 : position + 7], start=position + 1):
            if not isinstance(item, dict) or item.get("type") != "image":
                continue
            bbox = block_bbox(item)
            if bbox is None or bbox.y0 > search_bottom or bbox.width * bbox.height < 0.03:
                continue
            text = block_text(item)
            has_figure_caption = bool(
                re.search(r"(?:^|\s)(?:fig(?:ure)?\.?)[\s\u00a0]*\d+", text, re.IGNORECASE)
            )
            if has_figure_caption:
                continue
            return self._source_anchor(item, offset, text, bbox)
        return None
