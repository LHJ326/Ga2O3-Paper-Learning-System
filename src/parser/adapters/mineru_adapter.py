"""Convert preserved MinerU raw output into the project Document schema."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ...schema.document import (
    Document,
    Equation,
    EquationMetadata,
    Evidence,
    Figure,
    FigureTextRelation,
    Metadata,
    Page,
    Section,
    Table,
    TextBlock,
)
from .base import ParserAdapter


_PAGE_MARKER = re.compile(r"<!--\s*page\s+(\d+)\s+of\s+(\d+)\s*-->")
_HEADING = re.compile(r"^(#{1,2})\s+(.+?)\s*$", re.MULTILINE)
_IMAGE_PARAGRAPH = re.compile(
    r"^(?:!\[[^\]]*\]\(doc:[^)]+\)\s*)+$",
    re.DOTALL,
)
_IMAGE_REFERENCE = re.compile(
    r"^!\[(?P<block_type>[^\]]*)\]\((?P<locator>doc:[^)]+)\)$",
    re.DOTALL,
)
_FIGURE_CAPTION = re.compile(
    r"^(?:Figure|Fig\.)\s+(?P<number>\d+[A-Za-z]?)"
    r"(?:\s*[.:]\s*|\s+)(?P<description>\S[\s\S]*)$",
    re.IGNORECASE,
)
_TABLE_CAPTION = re.compile(
    r"^(?:Table)\s+(?:S?\d+|[IVXLCDM]+)(?:\s*[.:]\s*|\s+)\S[\s\S]*$",
    re.IGNORECASE,
)
_REFERENCE_ENTRY = re.compile(r"^\[\d+\]\s+")
_LOCATOR_PAGE = re.compile(r"(?:^|/)page:(\d+)(?:/|$)")
_SUBFIGURE_BODY = (
    r"(?:\([a-z](?:\s*[,\-\u2013\u2014]\s*[a-z])*\)"
    r"|[a-z](?:(?:,[a-z])|(?:\s*[\-\u2013\u2014]\s*[a-z]))*)"
)
_FIGURE_REFERENCE_TOKEN_TEXT = rf"S?\d+(?:{_SUBFIGURE_BODY})?(?![a-z])"
_FIGURE_REFERENCE_GROUP = re.compile(
    rf"\b(?P<label>Figures?|Figs?\.)\s*"
    rf"(?P<body>{_FIGURE_REFERENCE_TOKEN_TEXT}"
    rf"(?:\s*(?:,\s*(?:and\s+)?|and\s+|&\s+)"
    rf"(?:(?:Figures?|Figs?\.)\s*)?{_FIGURE_REFERENCE_TOKEN_TEXT})*)",
    re.IGNORECASE,
)
_FIGURE_REFERENCE_TOKEN = re.compile(
    rf"(?P<number>S?\d+)(?P<subfigure>{_SUBFIGURE_BODY})?(?![a-z])",
    re.IGNORECASE,
)
_MARKDOWN_EMPHASIS = re.compile(r"\*\*|__")
_DISPLAY_MATH = re.compile(
    r"^(?:\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\])$"
)
_EQUATION_TAG = re.compile(r"\\tag\{(?P<number>[^{}]+)\}")
_TRAILING_EQUATION_NUMBER = re.compile(r"\(\s*(?P<number>\d+[A-Za-z]?)\s*\)\s*(?:\$\$|\\\])?$")


class MinerUAdapter(ParserAdapter):
    """Convert the first supported MinerU raw-output contract."""

    def parse(self, source: Path) -> object:
        """Run MinerU in a later integration phase."""
        raise NotImplementedError(
            "MinerU parsing is outside the adapter conversion phase."
        )

    def convert(self, raw_output: object) -> Document:
        """Convert a MinerU raw-output directory into a Document."""
        raw_root = self._raw_root(raw_output)
        middle_json_path = self._middle_json_path(raw_root)
        if middle_json_path is not None:
            return self._convert_middle_json(raw_root, middle_json_path)
        return self._convert_legacy(raw_root)

    def _convert_legacy(self, raw_root: Path) -> Document:
        """Convert the preserved Markdown/legacy raw-output contract."""
        run_metadata = self._load_json(raw_root / "metadata.json")
        content_path = self._content_json_path(raw_root)
        content_payload = self._load_json(content_path)
        image_manifest = self._load_json(
            raw_root / "json" / "image_exports.json"
        )

        parse_info = content_payload.get("parse")
        content_info = content_payload.get("content")
        if not isinstance(parse_info, dict) or not isinstance(content_info, dict):
            raise ValueError("MinerU content JSON must contain parse and content objects.")

        markdown = content_info.get("content")
        if not isinstance(markdown, str):
            raise ValueError("MinerU content.content must be a Markdown string.")

        paper_id = self._required_string(run_metadata, "paper_id")
        parser_name = self._required_string(run_metadata, "parser_name")
        parser_version = self._required_string(run_metadata, "parser_version")
        provenance = {
            "paper_id": paper_id,
            "parser_name": parser_name,
            "parser_version": parser_version,
        }

        page_chunks = self._split_pages(markdown)
        pages = self._convert_pages(page_chunks, content_path, raw_root, provenance)
        sections = self._convert_sections(
            page_chunks, content_path, raw_root, provenance
        )
        text_blocks, boilerplate_diagnostics = self._convert_text_blocks(
            page_chunks, content_path, raw_root, provenance
        )
        image_contexts = self._image_contexts(page_chunks)
        figures = self._convert_figures(
            image_manifest,
            raw_root,
            provenance,
            image_contexts=image_contexts,
            caption_source_file=content_path.relative_to(raw_root).as_posix(),
        )
        figure_text_relations = self._link_figure_text_evidence(
            figures, text_blocks
        )
        formula_contexts = self._formula_contexts(page_chunks, text_blocks)
        equations = self._convert_equations(
            image_manifest,
            raw_root,
            provenance,
            formula_contexts=formula_contexts,
            text_blocks=text_blocks,
        )

        metadata_content = json.dumps(
            {
                "paper_id": paper_id,
                "parser_name": parser_name,
                "parser_version": parser_version,
                "parser_tier": run_metadata.get("parser_tier"),
                "checksum": run_metadata.get("checksum"),
                "parse": parse_info,
                "boilerplate_filter": boilerplate_diagnostics,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        metadata = Metadata(
            id=f"{paper_id}-metadata",
            page_number=None,
            content=metadata_content,
            source_reference=self._source_reference(
                provenance,
                source_file="metadata.json",
                page=None,
                mineru_locator=None,
            ),
        )

        return Document(
            document_id=paper_id,
            metadata=metadata,
            pages=pages,
            sections=sections,
            figures=figures,
            equations=equations,
            text_blocks=text_blocks,
            figure_text_relations=figure_text_relations,
        )

    def validate(self, document: Document) -> bool:
        """Validate converted MinerU output in a later phase."""
        raise NotImplementedError(
            "MinerU document validation is not implemented in Phase 1.5D-1B-2B."
        )

    @staticmethod
    def _raw_root(raw_output: object) -> Path:
        if not isinstance(raw_output, (str, Path)):
            raise TypeError("raw_output must be a filesystem path.")
        raw_root = Path(raw_output)
        if not raw_root.is_dir():
            raise FileNotFoundError(f"MinerU raw-output directory not found: {raw_root}")
        return raw_root

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise FileNotFoundError(f"Required MinerU raw-output file not found: {path}")
        with path.open(encoding="utf-8-sig") as input_file:
            payload = json.load(input_file)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected a JSON object in {path}")
        return payload

    @staticmethod
    def _middle_json_path(raw_root: Path) -> Path | None:
        """Return the single preserved docvortex.middle file, when present."""
        middle_dir = raw_root / "middle_json"
        if not middle_dir.is_dir():
            return None
        candidates = sorted(middle_dir.glob("*.json"))
        if not candidates:
            return None
        if len(candidates) != 1:
            raise ValueError(
                "MinerU raw output must contain at most one middle_json file."
            )
        return candidates[0]

    def _convert_middle_json(
        self, raw_root: Path, middle_path: Path
    ) -> Document:
        """Convert docvortex.middle 2.0 into Unified Document Schema 0.2."""
        raw = self._load_json(middle_path)
        if raw.get("schema") != "docvortex.middle":
            raise ValueError(
                f"Unsupported middle_json schema: {raw.get('schema')!r}"
            )
        if str(raw.get("schema_version")) != "2.0":
            raise ValueError(
                "Unsupported docvortex.middle schema version: "
                f"{raw.get('schema_version')!r}"
            )

        raw_pages = raw.get("pages")
        if not isinstance(raw_pages, list):
            raise ValueError("docvortex.middle pages must be an array.")
        page_indices = [
            page.get("page_idx") if isinstance(page, dict) else None
            for page in raw_pages
        ]
        if page_indices != list(range(len(raw_pages))):
            raise ValueError(
                "docvortex.middle page_idx values must be continuous from zero."
            )

        producer = raw.get("metadata", {}).get("producer", {})
        if not isinstance(producer, dict):
            producer = {}
        parser_name = str(producer.get("name") or "MinerU")
        parser_version = str(producer.get("version") or "unknown")
        paper_id = middle_path.stem
        legacy_metadata_path = raw_root / "metadata.json"
        if legacy_metadata_path.is_file():
            legacy_metadata = self._load_json(legacy_metadata_path)
            candidate_id = legacy_metadata.get("paper_id")
            if isinstance(candidate_id, str) and candidate_id:
                paper_id = candidate_id
        provenance = {
            "paper_id": paper_id,
            "parser_name": parser_name,
            "parser_version": parser_version,
        }
        source_file = middle_path.relative_to(raw_root).as_posix()

        records: list[dict[str, Any]] = []
        pages: list[Page] = []
        diagnostic_counts: dict[str, int] = {}
        for page in raw_pages:
            if not isinstance(page, dict) or not isinstance(page.get("blocks"), list):
                raise ValueError("Each docvortex.middle page must contain blocks.")
            page_idx = int(page["page_idx"])
            page_number = page_idx + 1
            page_texts: list[str] = []
            for position, block in enumerate(page["blocks"]):
                if not isinstance(block, dict):
                    raise ValueError("Each docvortex.middle block must be an object.")
                raw_type = str(block.get("type") or "unknown")
                diagnostic_counts[raw_type] = diagnostic_counts.get(raw_type, 0) + 1
                text = self._middle_content_text(block.get("content", ""))
                if text:
                    page_texts.append(text)
                records.append(
                    {
                        "page_idx": page_idx,
                        "page_number": page_number,
                        "position": position,
                        "block": block,
                        "type": raw_type,
                        "text": text,
                    }
                )
            pages.append(
                Page(
                    id=f"{paper_id}-page-{page_number:03d}",
                    page_number=page_number,
                    content="\n\n".join(page_texts),
                    source_reference=self._middle_source_reference(
                        provenance,
                        source_file=source_file,
                        page=page_number,
                        locator=f"/pages/{page_idx}",
                        raw_type="page",
                        raw_index=page_idx,
                        position=None,
                        bbox=None,
                    ),
                )
            )

        doc_titles = [record["text"] for record in records if record["type"] == "doc_title"]
        metadata = Metadata(
            id=f"{paper_id}-metadata",
            page_number=None,
            content=json.dumps(
                {
                    "document": raw.get("metadata", {}).get("document", {}),
                    "doc_titles": doc_titles,
                    "extensions": raw.get("extensions", {}),
                    "raw_block_counts": diagnostic_counts,
                    "excluded_text_block_types": [
                        "header",
                        "footer",
                        "page_footnote",
                    ],
                    "schema": raw["schema"],
                    "schema_version": str(raw["schema_version"]),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            source_reference=self._middle_source_reference(
                provenance,
                source_file=source_file,
                page=None,
                locator="/",
                raw_type="document",
                raw_index=None,
                position=None,
                bbox=None,
            ),
        )

        sections: list[Section] = []
        text_blocks: list[TextBlock] = []
        text_by_position: dict[tuple[int, int], TextBlock] = {}
        for record in records:
            block = record["block"]
            evidence = self._middle_source_reference(
                provenance,
                source_file=source_file,
                page=record["page_number"],
                locator=(
                    f"/pages/{record['page_idx']}/blocks/{record['position']}"
                ),
                raw_type=record["type"],
                raw_index=block.get("index"),
                position=record["position"],
                bbox=block.get("bbox"),
            )
            if record["type"] == "paragraph_title" and record["text"]:
                sections.append(
                    Section(
                        id=f"{paper_id}-section-{len(sections) + 1:03d}",
                        page_number=record["page_number"],
                        content=record["text"],
                        source_reference=evidence,
                    )
                )
            elif record["type"] == "text" and record["text"]:
                text_block = TextBlock(
                    id=f"{paper_id}-text-{len(text_blocks) + 1:04d}",
                    page_number=record["page_number"],
                    content=record["text"],
                    source_reference=evidence,
                )
                text_blocks.append(text_block)
                text_by_position[(record["page_idx"], record["position"])] = text_block

        figures = self._convert_middle_figures(
            records, provenance, source_file
        )
        figure_text_relations = self._link_figure_text_evidence(
            figures, text_blocks
        )
        equations = self._convert_middle_equations(
            records,
            provenance,
            source_file,
            text_blocks,
            text_by_position,
        )
        tables = self._convert_middle_tables(records, provenance, source_file)

        return Document(
            document_id=paper_id,
            metadata=metadata,
            pages=pages,
            sections=sections,
            figures=figures,
            tables=tables,
            equations=equations,
            text_blocks=text_blocks,
            figure_text_relations=figure_text_relations,
        )

    @staticmethod
    def _middle_content_text(value: Any) -> str:
        """Flatten nested docvortex content without inventing formatting."""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(MinerUAdapter._middle_content_text(item) for item in value)
        if isinstance(value, dict):
            return MinerUAdapter._middle_content_text(value.get("content", ""))
        return ""

    @staticmethod
    def _middle_source_reference(
        provenance: dict[str, str],
        *,
        source_file: str,
        page: int | None,
        locator: str,
        raw_type: str,
        raw_index: object,
        position: int | None,
        bbox: object,
    ) -> str:
        """Build a parser-independent Evidence bridge with a JSON locator."""
        return json.dumps(
            {
                **provenance,
                "source_file": source_file,
                "page": page,
                "mineru_locator": locator,
                "json_locator": locator,
                "raw_block_index": raw_index,
                "raw_block_position": position,
                "bbox": bbox,
                "raw_type": raw_type,
                "schema": "docvortex.middle",
                "schema_version": "2.0",
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def _convert_middle_figures(
        self,
        records: list[dict[str, Any]],
        provenance: dict[str, str],
        source_file: str,
    ) -> list[Figure]:
        """Keep only image blocks carrying a numbered scientific caption."""
        figures: list[Figure] = []
        for record in records:
            if record["type"] != "image":
                continue
            block = record["block"]
            children = block.get("content", [])
            if not isinstance(children, list):
                continue
            caption_position = None
            caption_block = None
            for nested_position, child in enumerate(children):
                if isinstance(child, dict) and child.get("type") == "image_caption":
                    caption_position = nested_position
                    caption_block = child
                    break
            if caption_block is None or caption_position is None:
                continue
            caption = self._middle_content_text(
                caption_block.get("content", "")
            ).strip()
            match = _FIGURE_CAPTION.fullmatch(caption)
            if match is None:
                continue
            locator = f"/pages/{record['page_idx']}/blocks/{record['position']}"
            caption_locator = f"{locator}/content/{caption_position}"
            figures.append(
                Figure(
                    id=f"{provenance['paper_id']}-figure-{len(figures) + 1:03d}",
                    page_number=record["page_number"],
                    content=json.dumps(
                        {
                            "image_path": None,
                            "mineru_block_type": "image",
                            "caption_status": "matched",
                            "caption": caption,
                            "figure_number": match.group("number"),
                            "caption_source_reference": json.loads(
                                self._middle_source_reference(
                                    provenance,
                                    source_file=source_file,
                                    page=record["page_number"],
                                    locator=caption_locator,
                                    raw_type="image_caption",
                                    raw_index=caption_block.get("index"),
                                    position=caption_position,
                                    bbox=caption_block.get("bbox"),
                                )
                            ),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    source_reference=self._middle_source_reference(
                        provenance,
                        source_file=source_file,
                        page=record["page_number"],
                        locator=locator,
                        raw_type="image",
                        raw_index=block.get("index"),
                        position=record["position"],
                        bbox=block.get("bbox"),
                    ),
                )
            )
        return figures

    @staticmethod
    def _is_header_decoration(record: dict[str, Any]) -> bool:
        """Identify empty equation-shaped decoration wholly inside the header."""
        if record["text"].strip():
            return False
        bbox = record["block"].get("bbox")
        return (
            isinstance(bbox, list)
            and len(bbox) == 4
            and all(isinstance(value, (int, float)) for value in bbox)
            and float(bbox[3]) <= 0.08
        )

    def _convert_middle_equations(
        self,
        records: list[dict[str, Any]],
        provenance: dict[str, str],
        source_file: str,
        text_blocks: list[TextBlock],
        text_by_position: dict[tuple[int, int], TextBlock],
    ) -> list[Equation]:
        """Convert raw equations while rejecting only header decoration."""
        equations: list[Equation] = []
        page_positions: dict[int, list[int]] = {}
        for page_idx, position in text_by_position:
            page_positions.setdefault(page_idx, []).append(position)

        for record in records:
            if record["type"] != "equation" or self._is_header_decoration(record):
                continue
            block = record["block"]
            content = record["text"].strip()
            positions = sorted(page_positions.get(record["page_idx"], []))
            before = [p for p in positions if p < record["position"]]
            after = [p for p in positions if p > record["position"]]
            neighbors = ([before[-1]] if before else []) + ([after[0]] if after else [])
            related_ids = [
                text_by_position[(record["page_idx"], position)].id
                for position in neighbors
            ]
            representation_type = "text" if content else "raw_block_without_content"
            locator = f"/pages/{record['page_idx']}/blocks/{record['position']}"
            equation = Equation(
                id=f"{provenance['paper_id']}-equation-{len(equations) + 1:03d}",
                page_number=record["page_number"],
                content=content,
                source_reference=self._middle_source_reference(
                    provenance,
                    source_file=source_file,
                    page=record["page_number"],
                    locator=locator,
                    raw_type="equation",
                    raw_index=block.get("index"),
                    position=record["position"],
                    bbox=block.get("bbox"),
                ),
                metadata=EquationMetadata(
                    representation_type=representation_type,
                    formula_image_path=None,
                    equation_number=self._equation_number(content),
                    related_text_block_ids=tuple(related_ids),
                ),
            )
            source = json.loads(equation.source_reference)
            source.update(
                {
                    "representation_type": representation_type,
                    "formula_image_path": None,
                    "equation_number": equation.metadata.equation_number,
                    "related_ids": related_ids,
                }
            )
            equation.source_reference = json.dumps(
                source, ensure_ascii=False, sort_keys=True
            )
            equations.append(equation)

        text_by_id = {block.id: block for block in text_blocks}
        for equation in equations:
            equation_source = json.loads(equation.source_reference)
            for text_id in equation_source["related_ids"]:
                text_block = text_by_id[text_id]
                text_source = json.loads(text_block.source_reference)
                text_source.setdefault("related_ids", [])
                if equation.id not in text_source["related_ids"]:
                    text_source["related_ids"].append(equation.id)
                text_source.setdefault("equation_references", []).append(
                    {
                        "equation_id": equation.id,
                        "relation": "nearest_same_page_text",
                        "mineru_locator": equation_source["mineru_locator"],
                    }
                )
                text_block.source_reference = json.dumps(
                    text_source, ensure_ascii=False, sort_keys=True
                )
        return equations

    def _convert_middle_tables(
        self,
        records: list[dict[str, Any]],
        provenance: dict[str, str],
        source_file: str,
    ) -> list[Table]:
        """Map typed table blocks without inferring textual table references."""
        tables: list[Table] = []
        for record in records:
            if record["type"] != "table":
                continue
            block = record["block"]
            locator = f"/pages/{record['page_idx']}/blocks/{record['position']}"
            tables.append(
                Table(
                    id=f"{provenance['paper_id']}-table-{len(tables) + 1:03d}",
                    page_number=record["page_number"],
                    content=record["text"],
                    source_reference=self._middle_source_reference(
                        provenance,
                        source_file=source_file,
                        page=record["page_number"],
                        locator=locator,
                        raw_type="table",
                        raw_index=block.get("index"),
                        position=record["position"],
                        bbox=block.get("bbox"),
                    ),
                )
            )
        return tables

    @staticmethod
    def _content_json_path(raw_root: Path) -> Path:
        candidates = sorted((raw_root / "json").glob("*_content.json"))
        if len(candidates) != 1:
            raise ValueError(
                "MinerU raw output must contain exactly one *_content.json file."
            )
        return candidates[0]

    @staticmethod
    def _required_string(payload: dict[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Raw metadata field '{field}' must be a non-empty string.")
        return value

    @staticmethod
    def _split_pages(markdown: str) -> list[tuple[int, str]]:
        markers = list(_PAGE_MARKER.finditer(markdown))
        if not markers:
            raise ValueError("MinerU Markdown contains no page markers.")

        declared_totals = {int(marker.group(2)) for marker in markers}
        page_numbers = [int(marker.group(1)) for marker in markers]
        if len(declared_totals) != 1 or page_numbers != list(
            range(1, len(markers) + 1)
        ):
            raise ValueError("MinerU Markdown page markers are not continuous.")
        if declared_totals != {len(markers)}:
            raise ValueError("MinerU Markdown page total does not match page markers.")

        pages: list[tuple[int, str]] = []
        for index, marker in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(markdown)
            pages.append((int(marker.group(1)), markdown[marker.end() : end].strip()))
        return pages

    def _convert_pages(
        self,
        page_chunks: list[tuple[int, str]],
        content_path: Path,
        raw_root: Path,
        provenance: dict[str, str],
    ) -> list[Page]:
        source_file = content_path.relative_to(raw_root).as_posix()
        return [
            Page(
                id=f"{provenance['paper_id']}-page-{page_number:03d}",
                page_number=page_number,
                content=content,
                source_reference=self._source_reference(
                    provenance,
                    source_file=source_file,
                    page=page_number,
                    mineru_locator=None,
                ),
            )
            for page_number, content in page_chunks
        ]

    def _convert_sections(
        self,
        page_chunks: list[tuple[int, str]],
        content_path: Path,
        raw_root: Path,
        provenance: dict[str, str],
    ) -> list[Section]:
        source_file = content_path.relative_to(raw_root).as_posix()
        sections: list[Section] = []
        for page_number, page_content in page_chunks:
            for match in _HEADING.finditer(page_content):
                sections.append(
                    Section(
                        id=f"{provenance['paper_id']}-section-{len(sections) + 1:03d}",
                        page_number=page_number,
                        content=match.group(2).strip(),
                        source_reference=self._source_reference(
                            provenance,
                            source_file=source_file,
                            page=page_number,
                            mineru_locator=None,
                        ),
                    )
                )
        return sections

    def _convert_text_blocks(
        self,
        page_chunks: list[tuple[int, str]],
        content_path: Path,
        raw_root: Path,
        provenance: dict[str, str],
    ) -> tuple[list[TextBlock], dict[str, object]]:
        source_file = content_path.relative_to(raw_root).as_posix()
        candidates: list[dict[str, object]] = []
        for page_number, page_content in page_chunks:
            page_blocks = [
                block.strip()
                for block in re.split(r"\n\s*\n", page_content)
                if block.strip()
            ]
            for position, paragraph in enumerate(page_blocks):
                if _HEADING.fullmatch(paragraph):
                    continue
                if _IMAGE_PARAGRAPH.fullmatch(paragraph):
                    continue

                adjacent_formula = any(
                    0 <= neighbor < len(page_blocks)
                    and (
                        match := _IMAGE_REFERENCE.fullmatch(
                            page_blocks[neighbor]
                        )
                    )
                    is not None
                    and match.group("block_type").strip() == "Formula block"
                    for neighbor in (position - 1, position + 1)
                )
                text_block = TextBlock(
                    # IDs use the raw TextBlock sequence and therefore remain
                    # stable when a high-confidence block is later filtered.
                    id=f"{provenance['paper_id']}-text-{len(candidates) + 1:04d}",
                    page_number=page_number,
                    content=paragraph,
                    source_reference=self._source_reference(
                        provenance,
                        source_file=source_file,
                        page=page_number,
                        mineru_locator=None,
                    ),
                )
                candidates.append(
                    {
                        "element": text_block,
                        "position": position,
                        "page_block_count": len(page_blocks),
                        "protected": bool(
                            _FIGURE_CAPTION.fullmatch(paragraph)
                            or _TABLE_CAPTION.fullmatch(paragraph)
                            or _REFERENCE_ENTRY.match(paragraph)
                            or adjacent_formula
                        ),
                    }
                )

        return self._filter_repeated_boilerplate(
            candidates,
            page_count=len(page_chunks),
        )

    @staticmethod
    def _filter_repeated_boilerplate(
        candidates: list[dict[str, object]],
        *,
        page_count: int,
    ) -> tuple[list[TextBlock], dict[str, object]]:
        """Remove only high-confidence repeated decoration at page edges."""
        groups: dict[str, list[dict[str, object]]] = {}
        for candidate in candidates:
            element = candidate["element"]
            if not isinstance(element, TextBlock):
                raise TypeError("TextBlock candidate must contain a TextBlock.")
            groups.setdefault(element.content, []).append(candidate)

        filtered_texts: dict[str, dict[str, object]] = {}
        minimum_short_decoration_pages = max(3, (page_count + 1) // 2)
        for text, occurrences in groups.items():
            pages = sorted(
                {
                    element.page_number
                    for occurrence in occurrences
                    if isinstance(
                        element := occurrence["element"], TextBlock
                    )
                    and element.page_number is not None
                }
            )
            if len(pages) < 3 or any(
                bool(occurrence["protected"]) for occurrence in occurrences
            ):
                continue

            at_page_edge = all(
                int(occurrence["position"]) < 5
                or int(occurrence["position"])
                >= int(occurrence["page_block_count"]) - 4
                for occurrence in occurrences
            )
            if not at_page_edge:
                continue

            lowered = text.casefold()
            if "downloaded from" in lowered and (
                "terms and conditions" in lowered
                or "rules of use" in lowered
            ):
                reason = "repeated_page_edge_download_notice"
            elif "©" in text or "copyright" in lowered:
                reason = "repeated_page_edge_copyright_notice"
            elif (
                "http://" in lowered
                or "https://" in lowered
                or "www." in lowered
            ) and len(text) <= 200:
                reason = "repeated_page_edge_url_banner"
            elif (
                len(text) <= 120
                and len(pages) >= minimum_short_decoration_pages
            ):
                reason = "repeated_page_edge_short_decoration"
            else:
                continue

            filtered_texts[text] = {
                "filtered_text": text,
                "pages": pages,
                "occurrence_count": len(occurrences),
                "filter_reason": reason,
            }

        retained = [
            candidate["element"]
            for candidate in candidates
            if isinstance(candidate["element"], TextBlock)
            and candidate["element"].content not in filtered_texts
        ]
        groups_diagnostic = sorted(
            filtered_texts.values(),
            key=lambda group: (
                -int(group["occurrence_count"]),
                str(group["filtered_text"]),
            ),
        )
        diagnostics: dict[str, object] = {
            "before_text_blocks": len(candidates),
            "after_text_blocks": len(retained),
            "filtered_count": len(candidates) - len(retained),
            "boilerplate_group_count": len(groups_diagnostic),
            "groups": groups_diagnostic,
        }
        return retained, diagnostics

    @staticmethod
    def _image_contexts(
        page_chunks: list[tuple[int, str]],
    ) -> dict[str, dict[str, object]]:
        """Collect image labels and conservative adjacent-caption matches."""
        contexts: dict[str, dict[str, object]] = {}
        for page_number, page_content in page_chunks:
            blocks = [
                block.strip()
                for block in re.split(r"\n\s*\n", page_content)
                if block.strip()
            ]
            for index, block in enumerate(blocks):
                image_match = _IMAGE_REFERENCE.fullmatch(block)
                if image_match is None:
                    continue

                locator = image_match.group("locator")
                context: dict[str, object] = {
                    "page": page_number,
                    "block_type": image_match.group("block_type").strip(),
                    "caption": None,
                    "figure_number": None,
                }

                if index + 1 < len(blocks):
                    caption_candidate = blocks[index + 1]
                    caption_match = _FIGURE_CAPTION.fullmatch(caption_candidate)
                    if caption_match is not None:
                        context["caption"] = caption_candidate
                        context["figure_number"] = caption_match.group("number")

                contexts[locator] = context
        return contexts

    def _convert_figures(
        self,
        image_manifest: dict[str, Any],
        raw_root: Path,
        provenance: dict[str, str],
        *,
        image_contexts: dict[str, dict[str, object]],
        caption_source_file: str,
    ) -> list[Figure]:
        images = image_manifest.get("images")
        if not isinstance(images, list):
            raise ValueError("image_exports.json must contain an images array.")

        figures: list[Figure] = []
        for image in images:
            if not isinstance(image, dict):
                raise ValueError("Each image manifest entry must be a JSON object.")
            locator = self._required_string(image, "locator")
            filename = self._required_string(image, "file")
            locator_match = _LOCATOR_PAGE.search(locator)
            if locator_match is None:
                raise ValueError(f"Image locator has no page number: {locator}")
            page_number = int(locator_match.group(1))
            image_path = raw_root / "images" / filename
            if not image_path.is_file():
                raise FileNotFoundError(f"Exported MinerU image not found: {image_path}")

            context = image_contexts.get(locator, {})
            context_page = context.get("page")
            if context_page is not None and context_page != page_number:
                raise ValueError(
                    f"Image locator page disagrees with Markdown context: {locator}"
                )

            caption = context.get("caption")
            figure_number = context.get("figure_number")
            caption_matched = isinstance(caption, str) and isinstance(
                figure_number, str
            )
            is_scientific_figure = (
                context.get("block_type") == "Image block" and caption_matched
            )
            if not is_scientific_figure:
                continue

            caption_source_reference = {
                **provenance,
                "source_file": caption_source_file,
                "page": page_number,
                "mineru_locator": None,
                "evidence_type": "figure_caption",
                "relation": "same_page_immediately_after_image",
            }

            figures.append(
                Figure(
                    id=f"{provenance['paper_id']}-figure-{len(figures) + 1:03d}",
                    page_number=page_number,
                    content=json.dumps(
                        {
                            "image_path": (Path("images") / filename).as_posix(),
                            "mime_type": image.get("mime_type"),
                            "width": image.get("width"),
                            "height": image.get("height"),
                            "mineru_block_type": context.get("block_type"),
                            "caption_status": "matched",
                            "caption": caption,
                            "figure_number": figure_number,
                            "caption_source_reference": caption_source_reference,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    source_reference=self._source_reference(
                        provenance,
                        source_file="json/image_exports.json",
                        page=page_number,
                        mineru_locator=locator,
                    ),
                )
            )
        return figures

    @staticmethod
    def _formula_contexts(
        page_chunks: list[tuple[int, str]],
        text_blocks: list[TextBlock],
    ) -> dict[str, dict[str, object]]:
        """Collect Formula block type, optional math text, and adjacent text IDs."""
        text_ids: dict[tuple[int, str], list[str]] = {}
        for text_block in text_blocks:
            if text_block.page_number is None:
                continue
            text_ids.setdefault(
                (text_block.page_number, text_block.content), []
            ).append(text_block.id)

        contexts: dict[str, dict[str, object]] = {}
        for page_number, page_content in page_chunks:
            blocks = [
                block.strip()
                for block in re.split(r"\n\s*\n", page_content)
                if block.strip()
            ]
            for index, block in enumerate(blocks):
                image_match = _IMAGE_REFERENCE.fullmatch(block)
                if (
                    image_match is None
                    or image_match.group("block_type").strip() != "Formula block"
                ):
                    continue

                neighboring_math = [
                    blocks[position]
                    for position in (index - 1, index + 1)
                    if 0 <= position < len(blocks)
                    and _DISPLAY_MATH.fullmatch(blocks[position]) is not None
                ]
                markdown_math = (
                    neighboring_math[0] if len(neighboring_math) == 1 else None
                )

                related_text_block_ids: list[str] = []
                for direction in (-1, 1):
                    position = index + direction
                    while 0 <= position < len(blocks):
                        candidate = blocks[position]
                        if _IMAGE_REFERENCE.fullmatch(candidate) is not None:
                            position += direction
                            continue
                        if _HEADING.fullmatch(candidate) is not None:
                            break
                        candidate_ids = text_ids.get(
                            (page_number, candidate), []
                        )
                        if len(candidate_ids) == 1:
                            related_text_block_ids.append(candidate_ids[0])
                        break

                contexts[image_match.group("locator")] = {
                    "page": page_number,
                    "block_type": "Formula block",
                    "markdown_math": markdown_math,
                    "related_text_block_ids": list(
                        dict.fromkeys(related_text_block_ids)
                    ),
                }
        return contexts

    def _convert_equations(
        self,
        image_manifest: dict[str, Any],
        raw_root: Path,
        provenance: dict[str, str],
        *,
        formula_contexts: dict[str, dict[str, object]],
        text_blocks: list[TextBlock],
    ) -> list[Equation]:
        """Convert MinerU Formula block assets without reconstructing math."""
        images = image_manifest.get("images")
        if not isinstance(images, list):
            raise ValueError("image_exports.json must contain an images array.")

        equations: list[Equation] = []
        for image in images:
            if not isinstance(image, dict):
                raise ValueError("Each image manifest entry must be a JSON object.")
            locator = self._required_string(image, "locator")
            context = formula_contexts.get(locator)
            if context is None:
                continue

            filename = self._required_string(image, "file")
            locator_match = _LOCATOR_PAGE.search(locator)
            if locator_match is None:
                raise ValueError(f"Formula locator has no page number: {locator}")
            page_number = int(locator_match.group(1))
            if context.get("page") != page_number:
                raise ValueError(
                    f"Formula locator page disagrees with Markdown context: {locator}"
                )
            image_path = raw_root / "images" / filename
            if not image_path.is_file():
                raise FileNotFoundError(
                    f"Exported MinerU formula image not found: {image_path}"
                )

            markdown_math = context.get("markdown_math")
            if isinstance(markdown_math, str):
                content = markdown_math
                representation_type = "markdown_math"
            else:
                content = ""
                representation_type = "image_only"

            equation_number = self._equation_number(content)
            related_ids = context.get("related_text_block_ids", [])
            if not isinstance(related_ids, list):
                raise ValueError("Formula related TextBlock IDs must be a list.")

            equation = Equation(
                id=f"{provenance['paper_id']}-equation-{len(equations) + 1:03d}",
                page_number=page_number,
                content=content,
                source_reference=json.dumps(
                    {
                        **provenance,
                        "source_file": "json/image_exports.json",
                        "page": page_number,
                        "mineru_locator": locator,
                        "formula_image_path": (
                            Path("images") / filename
                        ).as_posix(),
                        "representation_type": representation_type,
                        "equation_number": equation_number,
                        "related_ids": related_ids,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                metadata=EquationMetadata(
                    representation_type=representation_type,
                    formula_image_path=(
                        Path("images") / filename
                    ).as_posix(),
                    equation_number=equation_number,
                    related_text_block_ids=tuple(
                        str(text_block_id) for text_block_id in related_ids
                    ),
                ),
            )
            equations.append(equation)

        text_blocks_by_id = {text_block.id: text_block for text_block in text_blocks}
        for equation in equations:
            equation_source = json.loads(equation.source_reference)
            for text_block_id in equation_source["related_ids"]:
                text_block = text_blocks_by_id.get(text_block_id)
                if text_block is None:
                    continue
                text_source = json.loads(text_block.source_reference)
                if equation.id not in text_source["related_ids"]:
                    text_source["related_ids"].append(equation.id)
                text_source.setdefault("equation_references", []).append(
                    {
                        "equation_id": equation.id,
                        "relation": "adjacent_formula_block",
                        "mineru_locator": equation_source["mineru_locator"],
                    }
                )
                text_block.source_reference = json.dumps(
                    text_source, ensure_ascii=False, sort_keys=True
                )
        return equations

    @staticmethod
    def _equation_number(content: str) -> str | None:
        """Extract only an explicit number from available Markdown math."""
        if not content:
            return None
        tag_match = _EQUATION_TAG.search(content)
        if tag_match is not None:
            return tag_match.group("number").strip()
        trailing_match = _TRAILING_EQUATION_NUMBER.search(content)
        return (
            trailing_match.group("number")
            if trailing_match is not None
            else None
        )

    @staticmethod
    def _detect_figure_references(text: str) -> list[dict[str, object]]:
        """Return normalized explicit Figure/Fig. references from body text."""
        normalized_text = _MARKDOWN_EMPHASIS.sub("", text)
        references: list[dict[str, object]] = []
        for group_match in _FIGURE_REFERENCE_GROUP.finditer(normalized_text):
            body = group_match.group("body")
            for token_match in _FIGURE_REFERENCE_TOKEN.finditer(body):
                raw_number = token_match.group("number")
                supplementary = raw_number.upper().startswith("S")
                figure_number = raw_number[1:] if supplementary else raw_number
                subfigure = token_match.group("subfigure")
                if subfigure:
                    subfigure = (
                        subfigure.strip("()")
                        .replace(" ", "")
                        .replace("\u2013", "-")
                        .replace("\u2014", "-")
                        .lower()
                    )
                reference_type = (
                    "supplementary_figure" if supplementary else "main_figure"
                )
                normalized_reference = (
                    f"Figure {'S' if supplementary else ''}{figure_number}"
                    f"{subfigure or ''}"
                )
                references.append(
                    {
                        "reference_text": token_match.group(0),
                        "reference_type": reference_type,
                        "normalized_reference": normalized_reference,
                        "figure_number": figure_number,
                        "subfigure_hint": subfigure,
                        "supplementary": supplementary,
                    }
                )
        return references

    def _link_figure_text_evidence(
        self,
        figures: list[Figure],
        text_blocks: list[TextBlock],
    ) -> list[FigureTextRelation]:
        """Create conservative bidirectional links from explicit text references."""
        relations: list[FigureTextRelation] = []
        figures_by_number: dict[str, tuple[Figure, dict[str, object]]] = {}
        for figure in figures:
            payload = json.loads(figure.content)
            figure_number = str(payload["figure_number"])
            payload["related_text_block_ids"] = []
            payload["textual_references"] = []
            figure.content = json.dumps(
                payload, ensure_ascii=False, sort_keys=True
            )

            source = json.loads(figure.source_reference)
            source["related_ids"] = []
            figure.source_reference = json.dumps(
                source, ensure_ascii=False, sort_keys=True
            )
            figures_by_number[figure_number] = (figure, payload)

        for text_block in text_blocks:
            text_evidence = text_block.evidence
            text_source = json.loads(text_block.source_reference)
            text_source["related_ids"] = []
            text_source["figure_references"] = []

            # A figure caption is evidence for the Figure itself, not a body citation.
            if _FIGURE_CAPTION.fullmatch(text_block.content.strip()) is None:
                detected = self._detect_figure_references(text_block.content)
                for reference in detected:
                    figure_entry = figures_by_number.get(
                        str(reference["figure_number"])
                    )
                    if bool(reference["supplementary"]):
                        status = "supplementary"
                        reference_type = "supplementary_figure"
                    elif figure_entry is not None:
                        status = "resolved"
                        reference_type = "main_figure"
                    else:
                        status = "unresolved"
                        reference_type = "unresolved"
                    resolved = status == "resolved"
                    text_reference = {
                        **reference,
                        "reference_type": reference_type,
                        "status": status,
                        "figure_id": figure_entry[0].id if resolved else None,
                    }
                    text_source["figure_references"].append(text_reference)
                    if not resolved or figure_entry is None:
                        continue

                    figure, figure_payload = figure_entry
                    if figure.id not in text_source["related_ids"]:
                        text_source["related_ids"].append(figure.id)
                    if text_block.id not in figure_payload["related_text_block_ids"]:
                        figure_payload["related_text_block_ids"].append(text_block.id)
                    figure_payload["textual_references"].append(
                        {
                            "text_block_id": text_block.id,
                            "text_block_page": text_block.page_number,
                            "reference_text": reference["reference_text"],
                            "reference_type": reference["reference_type"],
                            "normalized_reference": reference[
                                "normalized_reference"
                            ],
                            "figure_number": reference["figure_number"],
                            "subfigure_hint": reference["subfigure_hint"],
                        }
                    )
                    relations.append(
                        FigureTextRelation(
                            id=(
                                f"{figure.id}-text-relation-"
                                f"{len(relations) + 1:04d}"
                            ),
                            figure_id=figure.id,
                            text_block_id=text_block.id,
                            relation_type="explicit_figure_reference",
                            reference_text=str(reference["reference_text"]),
                            normalized_reference=str(
                                reference["normalized_reference"]
                            ),
                            subfigure_hint=(
                                str(reference["subfigure_hint"])
                                if reference["subfigure_hint"] is not None
                                else None
                            ),
                            evidence=Evidence(
                                paper_id=text_evidence.paper_id,
                                parser_name=text_evidence.parser_name,
                                parser_version=text_evidence.parser_version,
                                source_file=text_evidence.source_file,
                                page=text_evidence.page,
                                mineru_locator=text_evidence.mineru_locator,
                                details={
                                    "reference_type": "main_figure",
                                    "relation_type": (
                                        "explicit_figure_reference"
                                    ),
                                },
                            ),
                        )
                    )

            text_block.source_reference = json.dumps(
                text_source, ensure_ascii=False, sort_keys=True
            )

        for figure, payload in figures_by_number.values():
            figure.content = json.dumps(
                payload, ensure_ascii=False, sort_keys=True
            )
            source = json.loads(figure.source_reference)
            source["related_ids"] = list(payload["related_text_block_ids"])
            figure.source_reference = json.dumps(
                source, ensure_ascii=False, sort_keys=True
            )
        return relations

    @staticmethod
    def _source_reference(
        provenance: dict[str, str],
        *,
        source_file: str,
        page: int | None,
        mineru_locator: str | None,
    ) -> str:
        return json.dumps(
            {
                **provenance,
                "source_file": source_file,
                "page": page,
                "mineru_locator": mineru_locator,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
