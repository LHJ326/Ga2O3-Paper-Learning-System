"""Tests for parser adapter contracts and Phase 1.5D-1A placeholders."""

from pathlib import Path

import pytest

from src.parser.adapters import MinerUAdapter, ParserAdapter
from src.schema.document import Document, Metadata


def _document() -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata(
            id="metadata-P001",
            page_number=None,
            content="Placeholder metadata",
            source_reference="P001",
        ),
    )


def test_parser_adapter_interface_exists() -> None:
    assert ParserAdapter.__abstractmethods__ == {"parse", "convert", "validate"}


def test_mineru_adapter_can_be_instantiated() -> None:
    assert isinstance(MinerUAdapter(), ParserAdapter)


def test_mineru_adapter_methods_are_placeholders() -> None:
    adapter = MinerUAdapter()

    with pytest.raises(NotImplementedError, match="parsing"):
        adapter.parse(Path("paper.pdf"))

    with pytest.raises(NotImplementedError, match="schema conversion"):
        adapter.convert(object())

    with pytest.raises(NotImplementedError, match="validation"):
        adapter.validate(_document())
