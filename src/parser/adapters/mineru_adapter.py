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
        for index, image in enumerate(images, start=1):
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
            caption_source_reference = None
            if caption_matched:
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
                    id=f"{provenance['paper_id']}-figure-{index:03d}",
                    page_number=page_number,
                    content=json.dumps(
                        {
                            "image_path": (Path("images") / filename).as_posix(),
                            "mime_type": image.get("mime_type"),
                            "width": image.get("width"),
                            "height": image.get("height"),
                            "mineru_block_type": context.get("block_type"),
                            "caption_status": (
                                "matched" if caption_matched else "unmatched"
                            ),
                            "caption": caption if caption_matched else None,
                            "figure_number": (
                                figure_number if caption_matched else None
                            ),
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
