from pathlib import Path

import pytest
import yaml

from src.metadata import MetadataImportError, import_metadata, parse_metadata


def test_parse_bibtex_normalizes_canonical_fields(tmp_path: Path) -> None:
    source = tmp_path / "paper.bib"
    source.write_text(
        """@article{sample,
        title = {A Lightweight Metadata Pipeline},
        author = {Doe, Jane and Smith, John},
        year = {2025},
        journal = {Journal of Tests},
        doi = {https://doi.org/10.1234/ABC.Def},
        keywords = {Ga2O3; metadata, pipelines}
        }""",
        encoding="utf-8",
    )
    item = parse_metadata(source, paper_id="P101")
    assert item.paper_id == "P101"
    assert item.title == "A Lightweight Metadata Pipeline"
    assert item.authors == ("Doe, Jane", "Smith, John")
    assert item.year == 2025
    assert item.journal == "Journal of Tests"
    assert item.doi == "10.1234/abc.def"
    assert item.keywords == ("Ga2O3", "metadata", "pipelines")
    assert item.citation.endswith("https://doi.org/10.1234/abc.def")


def test_parse_ris_handles_repeated_fields_and_continuation(tmp_path: Path) -> None:
    source = tmp_path / "paper.ris"
    source.write_text(
        """TY  - JOUR
TI  - A Long Scientific
      Title
AU  - Doe, Jane
AU  - Smith, John
PY  - 2024/05/01
JO  - Test Journal
DO  - doi: 10.5555/Example
KW  - oxide
KW  - ultraviolet; detector
ER  -
""",
        encoding="utf-8",
    )
    item = parse_metadata(source, paper_id="P102")
    assert item.title == "A Long Scientific Title"
    assert item.authors == ("Doe, Jane", "Smith, John")
    assert item.year == 2024
    assert item.doi == "10.5555/example"
    assert item.keywords == ("oxide", "ultraviolet", "detector")


def test_parse_metadata_rejects_unsupported_extension(tmp_path: Path) -> None:
    source = tmp_path / "paper.txt"
    source.write_text("not metadata", encoding="utf-8")
    with pytest.raises(MetadataImportError, match="Unsupported"):
        parse_metadata(source, paper_id="P103")


def test_bibtex_requires_exactly_one_record(tmp_path: Path) -> None:
    source = tmp_path / "many.bib"
    source.write_text(
        "@article{a,title={A}}\n@article{b,title={B}}\n", encoding="utf-8"
    )
    with pytest.raises(MetadataImportError, match="exactly one"):
        parse_metadata(source, paper_id="P104")


def test_import_writes_yaml_and_marks_registry_metadata_ready(tmp_path: Path) -> None:
    source = tmp_path / "paper.ris"
    source.write_text("TY  - JOUR\nTI  - Real Paper\nER  -\n", encoding="utf-8")
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        yaml.safe_dump({"papers": [{
            "paper_id": "P105",
            "processing_status": {
                "imported": True,
                "metadata_ready": False,
                "parsed": False,
                "figures_processed": False,
                "tables_processed": False,
                "knowledge_ready": False,
            },
        }]}),
        encoding="utf-8",
    )
    output = import_metadata(
        source,
        paper_id="P105",
        metadata_root=tmp_path / "metadata",
        registry_path=registry,
    )
    metadata = yaml.safe_load(output.read_text(encoding="utf-8"))
    updated = yaml.safe_load(registry.read_text(encoding="utf-8"))["papers"][0]
    assert metadata["paper_id"] == "P105"
    assert metadata["title"] == "Real Paper"
    assert updated["metadata_path"] == output.as_posix()
    assert updated["processing_status"]["imported"] is True
    assert updated["processing_status"]["metadata_ready"] is True
    assert updated["processing_status"]["parsed"] is False


def test_import_upgrades_legacy_scalar_processing_status(tmp_path: Path) -> None:
    source = tmp_path / "paper.bib"
    source.write_text("@article{x,title={Legacy Status}}", encoding="utf-8")
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        yaml.safe_dump({"papers": [{
            "paper_id": "P106", "processing_status": "imported"
        }]}),
        encoding="utf-8",
    )
    import_metadata(
        source, paper_id="P106", metadata_root=tmp_path / "metadata",
        registry_path=registry,
    )
    status = yaml.safe_load(registry.read_text(encoding="utf-8"))["papers"][0]["processing_status"]
    assert status["imported"] is True
    assert status["metadata_ready"] is True
    assert status["parsed"] is False


def test_unregistered_paper_does_not_write_metadata(tmp_path: Path) -> None:
    source = tmp_path / "paper.ris"
    source.write_text("TY  - JOUR\nTI  - Unregistered\nER  -\n", encoding="utf-8")
    registry = tmp_path / "registry.yaml"
    registry.write_text("papers: []\n", encoding="utf-8")
    metadata_root = tmp_path / "metadata"
    with pytest.raises(MetadataImportError, match="exactly one existing"):
        import_metadata(
            source, paper_id="P107", metadata_root=metadata_root,
            registry_path=registry,
        )
    assert not (metadata_root / "P107.yaml").exists()
