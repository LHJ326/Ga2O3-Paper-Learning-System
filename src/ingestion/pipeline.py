"""Deterministic local PDF ingestion without parsing or model invocation."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..metadata import import_metadata


_PAPER_ID_RE = re.compile(r"^P(?P<number>\d{3,})$", re.IGNORECASE)
_OBJECT_DIRECTORIES = ("source", "metadata", "parsed", "assets", "knowledge")
_STATUS_NAMES = (
    "imported", "metadata_ready", "parsed", "figures_processed",
    "tables_processed", "knowledge_ready",
)


class IngestionError(ValueError):
    """Raised when a batch input cannot be imported unambiguously."""


@dataclass(frozen=True)
class IngestedPaper:
    paper_id: str
    object_path: Path
    source_pdf: Path
    metadata_source: Path | None
    normalized_metadata: Path | None


def scan_pdf_directory(path: str | Path, *, recursive: bool = False) -> list[Path]:
    """Return a stable, case-insensitive list of PDFs from one input directory."""
    root = Path(path)
    if not root.is_dir():
        raise IngestionError(f"PDF input directory does not exist: {root}")
    candidates = root.rglob("*") if recursive else root.iterdir()
    return sorted(
        (item for item in candidates if item.is_file() and item.suffix.casefold() == ".pdf"),
        key=lambda item: item.as_posix().casefold(),
    )


def _load_registry(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("papers"), list):
        raise IngestionError(f"Invalid Paper Registry: {path}")
    return payload


def _used_paper_numbers(registry: dict[str, Any], papers_root: Path) -> set[int]:
    names = [str(item.get("paper_id", "")) for item in registry["papers"]]
    if papers_root.is_dir():
        names.extend(
            item.stem if item.is_file() else item.name
            for item in papers_root.iterdir()
        )
    numbers: set[int] = set()
    for name in names:
        match = _PAPER_ID_RE.fullmatch(name)
        if match:
            numbers.add(int(match.group("number")))
    return numbers


def next_paper_id(
    *, registry_path: str | Path = "data/papers/registry.yaml",
    papers_root: str | Path = "data/papers",
) -> str:
    """Allocate the next P-series ID across Registry and legacy/object storage."""
    registry = _load_registry(Path(registry_path))
    used = _used_paper_numbers(registry, Path(papers_root))
    return f"P{max(used, default=0) + 1:03d}"


def _metadata_sidecar(pdf: Path) -> Path | None:
    matches = sorted(
        (
            item for item in pdf.parent.iterdir()
            if item.is_file()
            and item.stem.casefold() == pdf.stem.casefold()
            and item.suffix.casefold() in {".ris", ".bib"}
        ),
        key=lambda item: item.suffix.casefold(),
    )
    if len(matches) > 1:
        raise IngestionError(f"Multiple metadata sidecars found for {pdf.name}")
    return matches[0] if matches else None


def _status(*, paper_id: str, metadata_ready: bool = False) -> dict[str, Any]:
    values = {name: False for name in _STATUS_NAMES}
    values["imported"] = True
    values["metadata_ready"] = metadata_ready
    return {"paper_id": paper_id, **values}


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _create_object(
    papers_root: Path, paper_id: str, pdf: Path, sidecar: Path | None
) -> tuple[Path, Path]:
    object_path = papers_root / paper_id
    if object_path.exists():
        raise IngestionError(f"Paper object already exists: {object_path}")
    for name in _OBJECT_DIRECTORIES:
        (object_path / name).mkdir(parents=True, exist_ok=False)
    destination = object_path / "source" / pdf.name
    shutil.copy2(pdf, destination)
    if sidecar is not None:
        shutil.copy2(sidecar, object_path / "metadata" / sidecar.name)
    _write_yaml(object_path / "status.yaml", _status(paper_id=paper_id))
    return object_path, destination


def ingest_directory(
    input_directory: str | Path,
    *,
    papers_root: str | Path = "data/papers",
    metadata_root: str | Path = "data/metadata",
    registry_path: str | Path = "data/papers/registry.yaml",
    recursive: bool = False,
) -> list[IngestedPaper]:
    """Import PDFs and optional same-stem RIS/BibTeX sidecars in stable order."""
    pdfs = scan_pdf_directory(input_directory, recursive=recursive)
    papers_root = Path(papers_root)
    metadata_root = Path(metadata_root)
    registry_path = Path(registry_path)
    registry = _load_registry(registry_path)
    used = _used_paper_numbers(registry, papers_root)
    imported: list[IngestedPaper] = []
    papers_root.mkdir(parents=True, exist_ok=True)

    for pdf in pdfs:
        number = max(used, default=0) + 1
        paper_id = f"P{number:03d}"
        used.add(number)
        sidecar = _metadata_sidecar(pdf)
        object_path, source_pdf = _create_object(papers_root, paper_id, pdf, sidecar)
        processing_status = _status(paper_id=paper_id)
        processing_status.pop("paper_id")
        registry["papers"].append({
            "paper_id": paper_id,
            "title": None,
            "authors": [],
            "year": None,
            "journal": None,
            "DOI": None,
            "source_pdf": source_pdf.as_posix(),
            "metadata_path": None,
            "parsed_path": (object_path / "parsed").as_posix(),
            "processing_status": processing_status,
        })
        _write_yaml(registry_path, registry)

        normalized_metadata = None
        if sidecar is not None:
            normalized_metadata = import_metadata(
                sidecar,
                paper_id=paper_id,
                metadata_root=metadata_root,
                registry_path=registry_path,
            )
            _write_yaml(
                object_path / "status.yaml",
                _status(paper_id=paper_id, metadata_ready=True),
            )
            registry = _load_registry(registry_path)
        imported.append(IngestedPaper(
            paper_id=paper_id,
            object_path=object_path,
            source_pdf=source_pdf,
            metadata_source=sidecar,
            normalized_metadata=normalized_metadata,
        ))
    return imported
