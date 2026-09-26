from src.schema.document import Document, Figure, Metadata, TextBlock


def test_document_can_be_instantiated() -> None:
    metadata = Metadata(
        id="metadata-1",
        page_number=None,
        content="Title: Example Ga2O3 photodetector paper",
        source_reference="example.pdf#metadata",
    )

    document = Document(document_id="document-1", metadata=metadata)

    assert document.document_id == "document-1"
    assert document.metadata == metadata
    assert document.pages == []
    assert document.sections == []
    assert document.figures == []
    assert document.tables == []
    assert document.equations == []
    assert document.text_blocks == []


def test_figure_can_be_created() -> None:
    figure = Figure(
        id="figure-1",
        page_number=3,
        content="Figure 1. Device architecture.",
        source_reference="example.pdf#page=3&figure=1",
    )

    assert figure.id == "figure-1"
    assert figure.page_number == 3
    assert figure.content == "Figure 1. Device architecture."
    assert figure.source_reference == "example.pdf#page=3&figure=1"


def test_text_block_can_be_created() -> None:
    text_block = TextBlock(
        id="text-block-1",
        page_number=2,
        content="The responsivity increases under UV illumination.",
        source_reference="example.pdf#page=2&block=1",
    )

    assert text_block.id == "text-block-1"
    assert text_block.page_number == 2
    assert text_block.content.startswith("The responsivity")
    assert text_block.source_reference == "example.pdf#page=2&block=1"
