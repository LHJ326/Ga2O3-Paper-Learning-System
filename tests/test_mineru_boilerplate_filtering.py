import json
from pathlib import Path

from src.parser.adapters import MinerUAdapter
from src.schema.document import TextBlock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
P001_RAW_OUTPUT = PROJECT_ROOT / "data" / "parsed" / "P001" / "mineru" / "raw"


def _document():
    return MinerUAdapter().convert(P001_RAW_OUTPUT)


def test_p001_repeated_page_boilerplate_is_filtered_and_diagnosed() -> None:
    document = _document()
    metadata = json.loads(document.metadata.content)
    diagnostics = metadata["boilerplate_filter"]

    assert diagnostics["before_text_blocks"] == 214
    assert diagnostics["after_text_blocks"] == 156
    assert diagnostics["filtered_count"] == 58
    assert diagnostics["boilerplate_group_count"] == 5
    assert len(document.text_blocks) == 156

    reasons = {group["filter_reason"] for group in diagnostics["groups"]}
    assert reasons == {
        "repeated_page_edge_download_notice",
        "repeated_page_edge_copyright_notice",
        "repeated_page_edge_url_banner",
        "repeated_page_edge_short_decoration",
    }
    assert all(group["pages"] for group in diagnostics["groups"])
    assert sum(
        group["occurrence_count"] for group in diagnostics["groups"]
    ) == 58


def test_filter_preserves_scientific_structure_body_and_references() -> None:
    document = _document()
    contents = [block.content for block in document.text_blocks]

    assert len(document.sections) == 10
    assert len(document.figures) == 6
    assert len(document.equations) == 6
    assert any("To solve the above problems" in text for text in contents)
    assert any("Device Fabrication:" in text for text in contents)
    assert any(text.startswith("[1] N. Brown") for text in contents)
    assert any(text.startswith("Figure 1.") for text in contents)
    assert any("Table S1 (Supporting Information)" in text for text in contents)
    assert any("could be calculated" in text for text in contents)


def test_filtered_document_retains_complete_text_evidence() -> None:
    document = _document()
    required = {
        "paper_id",
        "parser_name",
        "parser_version",
        "source_file",
        "page",
    }

    assert all(
        required <= json.loads(block.source_reference).keys()
        for block in document.text_blocks
    )


def test_generic_filter_requires_repetition_edge_and_decoration_evidence() -> None:
    def candidate(
        identifier: str,
        page: int,
        text: str,
        position: int,
        *,
        protected: bool = False,
    ) -> dict[str, object]:
        return {
            "element": TextBlock(
                id=identifier,
                page_number=page,
                content=text,
                source_reference="{}",
            ),
            "position": position,
            "page_block_count": 10,
            "protected": protected,
        }

    candidates = []
    for page in (1, 2, 3):
        candidates.extend(
            [
                candidate(
                    f"url-{page}",
                    page,
                    "[www.publisher.example](https://publisher.example)",
                    0,
                ),
                candidate(
                    f"body-{page}",
                    page,
                    "The measured response remained stable under repeated tests.",
                    5,
                ),
                candidate(
                    f"ref-{page}",
                    page,
                    "[1] A. Author, Journal 2025, 1, 1.",
                    9,
                    protected=True,
                ),
            ]
        )

    retained, diagnostics = MinerUAdapter._filter_repeated_boilerplate(
        candidates,
        page_count=3,
    )
    retained_ids = {block.id for block in retained}

    assert diagnostics["filtered_count"] == 3
    assert diagnostics["boilerplate_group_count"] == 1
    assert all(f"url-{page}" not in retained_ids for page in (1, 2, 3))
    assert all(f"body-{page}" in retained_ids for page in (1, 2, 3))
    assert all(f"ref-{page}" in retained_ids for page in (1, 2, 3))
