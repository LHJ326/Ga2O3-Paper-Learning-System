"""Convert preserved MinerU raw output into the project Document schema."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ...schema.document import Document, Figure, Metadata, Page, Section, TextBlock
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
        text_blocks = self._convert_text_blocks(
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
        self._link_figure_text_evidence(figures, text_blocks)

        metadata_content = json.dumps(
            {
                "paper_id": paper_id,
                "parser_name": parser_name,
                "parser_version": parser_version,
                "parser_tier": run_metadata.get("parser_tier"),
                "checksum": run_metadata.get("checksum"),
                "parse": parse_info,
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
            text_blocks=text_blocks,
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
    ) -> list[TextBlock]:
        source_file = content_path.relative_to(raw_root).as_posix()
        text_blocks: list[TextBlock] = []
        for page_number, page_content in page_chunks:
            for paragraph in re.split(r"\n\s*\n", page_content):
                paragraph = paragraph.strip()
                if not paragraph or _HEADING.fullmatch(paragraph):
                    continue
                if _IMAGE_PARAGRAPH.fullmatch(paragraph):
                    continue
                text_blocks.append(
                    TextBlock(
                        id=f"{provenance['paper_id']}-text-{len(text_blocks) + 1:04d}",
                        page_number=page_number,
                        content=paragraph,
                        source_reference=self._source_reference(
                            provenance,
                            source_file=source_file,
                            page=page_number,
                            mineru_locator=None,
                        ),
                    )
                )
        return text_blocks

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
    ) -> None:
        """Create conservative bidirectional links from explicit text references."""
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
