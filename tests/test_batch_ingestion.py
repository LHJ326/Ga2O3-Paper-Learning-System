from pathlib import Path

import pytest
import yaml

from src.ingestion import (
    IngestionError,
    ingest_directory,
    next_paper_id,
    scan_pdf_directory,
)


def registry_file(path: Path, papers=None) -> Path:
    path.write_text(
        yaml.safe_dump({"registry_version": "1.0", "papers": papers or []}),
        encoding="utf-8",
    )
    return path


def test_pdf_scan_is_filtered_and_deterministically_sorted(tmp_path: Path) -> None:
    (tmp_path / "b.PDF").write_bytes(b"b")
    (tmp_path / "A.pdf").write_bytes(b"a")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.pdf").write_bytes(b"c")
    assert [path.name for path in scan_pdf_directory(tmp_path)] == ["A.pdf", "b.PDF"]
    assert [path.name for path in scan_pdf_directory(tmp_path, recursive=True)] == [
        "A.pdf", "b.PDF", "c.pdf"
    ]


def test_paper_id_generation_checks_registry_and_legacy_pdf(tmp_path: Path) -> None:
    papers_root = tmp_path / "papers"
    papers_root.mkdir()
    (papers_root / "P001.pdf").write_bytes(b"legacy")
    registry = registry_file(
        tmp_path / "registry.yaml", [{"paper_id": "P004"}]
    )
    assert next_paper_id(registry_path=registry, papers_root=papers_root) == "P005"


def test_ingestion_creates_complete_paper_object_and_registry_record(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "paper.pdf").write_bytes(b"%PDF synthetic")
    papers_root = tmp_path / "papers"
    registry = registry_file(tmp_path / "registry.yaml")
    result = ingest_directory(
        incoming,
        papers_root=papers_root,
        metadata_root=tmp_path / "metadata",
        registry_path=registry,
    )
    assert len(result) == 1 and result[0].paper_id == "P001"
    object_path = papers_root / "P001"
    assert {item.name for item in object_path.iterdir()} == {
        "source", "metadata", "parsed", "assets", "knowledge", "status.yaml"
    }
    assert (object_path / "source" / "paper.pdf").read_bytes() == b"%PDF synthetic"
    status = yaml.safe_load((object_path / "status.yaml").read_text(encoding="utf-8"))
    assert status["imported"] is True
    assert status["metadata_ready"] is False
    record = yaml.safe_load(registry.read_text(encoding="utf-8"))["papers"][0]
    assert record["paper_id"] == "P001"
    assert record["processing_status"]["imported"] is True
    assert record["parsed_path"].endswith("papers/P001/parsed")


def test_batch_assigns_stable_sequential_ids(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "z.pdf").write_bytes(b"z")
    (incoming / "a.pdf").write_bytes(b"a")
    papers_root = tmp_path / "papers"
    papers_root.mkdir()
    (papers_root / "P001.pdf").write_bytes(b"legacy")
    registry = registry_file(tmp_path / "registry.yaml")
    result = ingest_directory(
        incoming, papers_root=papers_root, metadata_root=tmp_path / "metadata",
        registry_path=registry,
    )
    assert [item.paper_id for item in result] == ["P002", "P003"]
    assert result[0].source_pdf.name == "a.pdf"
    assert result[1].source_pdf.name == "z.pdf"


def test_matching_bibtex_is_normalized_and_linked(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "device.pdf").write_bytes(b"pdf")
    (incoming / "device.bib").write_text(
        """@article{x,
        title={A Real Device Paper},
        author={Doe, Jane and Smith, John},
        year={2025},
        journal={Device Journal},
        doi={10.1000/Test}
        }""",
        encoding="utf-8",
    )
    papers_root = tmp_path / "papers"
    metadata_root = tmp_path / "metadata"
    registry = registry_file(tmp_path / "registry.yaml")
    result = ingest_directory(
        incoming, papers_root=papers_root, metadata_root=metadata_root,
        registry_path=registry,
    )[0]
    assert result.normalized_metadata == metadata_root / "P001.yaml"
    assert (papers_root / "P001" / "metadata" / "device.bib").is_file()
    normalized = yaml.safe_load(result.normalized_metadata.read_text(encoding="utf-8"))
    assert normalized["title"] == "A Real Device Paper"
    record = yaml.safe_load(registry.read_text(encoding="utf-8"))["papers"][0]
    assert record["title"] == "A Real Device Paper"
    assert record["DOI"] == "10.1000/test"
    assert record["processing_status"]["metadata_ready"] is True
    status = yaml.safe_load(
        (papers_root / "P001" / "status.yaml").read_text(encoding="utf-8")
    )
    assert status["metadata_ready"] is True


def test_ambiguous_metadata_sidecars_are_rejected_before_object_creation(tmp_path: Path) -> None:
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    (incoming / "paper.pdf").write_bytes(b"pdf")
    (incoming / "paper.bib").write_text("@article{x,title={X}}", encoding="utf-8")
    (incoming / "paper.ris").write_text("TY  - JOUR\nTI  - X\nER  -\n", encoding="utf-8")
    papers_root = tmp_path / "papers"
    registry = registry_file(tmp_path / "registry.yaml")
    with pytest.raises(IngestionError, match="Multiple metadata"):
        ingest_directory(
            incoming, papers_root=papers_root, metadata_root=tmp_path / "metadata",
            registry_path=registry,
        )
    assert not (papers_root / "P001").exists()
    assert yaml.safe_load(registry.read_text(encoding="utf-8"))["papers"] == []
