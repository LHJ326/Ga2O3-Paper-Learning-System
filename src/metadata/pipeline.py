"""Normalize one RIS or BibTeX record and update its Registry lifecycle."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import bibtexparser
import yaml


class MetadataImportError(ValueError):
    """Raised when a metadata source cannot become one unambiguous record."""


@dataclass(frozen=True)
class PaperMetadata:
    paper_id: str
    title: str
    authors: tuple[str, ...]
    year: int | None
    journal: str | None
    doi: str | None
    keywords: tuple[str, ...]
    citation: str

    def to_mapping(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authors"] = list(self.authors)
        payload["keywords"] = list(self.keywords)
        return payload


def _clean(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    while len(text) >= 2 and text[0] == "{" and text[-1] == "}":
        text = text[1:-1].strip()
    return text


def _normalize_doi(value: Any) -> str | None:
    text = _clean(value)
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text, flags=re.I)
    return text.casefold() or None


def _year(value: Any) -> int | None:
    match = re.search(r"(?:19|20)\d{2}", _clean(value))
    return int(match.group()) if match else None


def _keywords(values: list[str]) -> tuple[str, ...]:
    parts = [
        _clean(part)
        for value in values
        for part in re.split(r"\s*[;,]\s*", value)
    ]
    return tuple(dict.fromkeys(part for part in parts if part))


def _citation(
    authors: tuple[str, ...], title: str, journal: str | None,
    year: int | None, doi: str | None, explicit: str | None = None,
) -> str:
    if explicit and _clean(explicit):
        return _clean(explicit)
    pieces: list[str] = []
    if authors:
        pieces.append("; ".join(authors))
    pieces.append(title)
    if journal:
        pieces.append(journal)
    if year is not None:
        pieces.append(str(year))
    citation = ". ".join(piece.rstrip(".") for piece in pieces if piece) + "."
    if doi:
        citation += f" https://doi.org/{doi}"
    return citation


def _build_metadata(paper_id: str, raw: dict[str, Any]) -> PaperMetadata:
    title = _clean(raw.get("title"))
    if not title:
        raise MetadataImportError("Metadata record must contain a title")
    authors = tuple(_clean(item) for item in raw.get("authors", []) if _clean(item))
    year = _year(raw.get("year"))
    journal = _clean(raw.get("journal")) or None
    doi = _normalize_doi(raw.get("doi"))
    keywords = _keywords([str(item) for item in raw.get("keywords", [])])
    return PaperMetadata(
        paper_id=paper_id,
        title=title,
        authors=authors,
        year=year,
        journal=journal,
        doi=doi,
        keywords=keywords,
        citation=_citation(
            authors, title, journal, year, doi, raw.get("citation")
        ),
    )


def _parse_bib(path: Path, paper_id: str) -> PaperMetadata:
    library = bibtexparser.parse_file(path)
    if library.failed_blocks:
        raise MetadataImportError(f"BibTeX parse failed for {path}")
    if len(library.entries) != 1:
        raise MetadataImportError("A paper metadata file must contain exactly one BibTeX entry")
    entry = library.entries[0]
    fields = {key.casefold(): field.value for key, field in entry.fields_dict.items()}
    author_text = _clean(fields.get("author"))
    return _build_metadata(paper_id, {
        "title": fields.get("title"),
        "authors": re.split(r"\s+and\s+", author_text, flags=re.I) if author_text else [],
        "year": fields.get("year"),
        "journal": fields.get("journal") or fields.get("journaltitle"),
        "doi": fields.get("doi"),
        "keywords": [fields.get("keywords", "")],
        "citation": fields.get("citation"),
    })


def _ris_records(path: Path) -> list[dict[str, list[str]]]:
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    last_tag: str | None = None
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^([A-Z0-9]{2})\s{0,2}-\s?(.*)$", raw_line)
        if match:
            tag, value = match.groups()
            if tag == "ER":
                if current:
                    records.append(current)
                current = {}
                last_tag = None
                continue
            current.setdefault(tag, []).append(value.strip())
            last_tag = tag
        elif raw_line[:1].isspace() and last_tag and current.get(last_tag):
            current[last_tag][-1] = f"{current[last_tag][-1]} {raw_line.strip()}".strip()
    if current:
        records.append(current)
    return records


def _first(record: dict[str, list[str]], *tags: str) -> str | None:
    for tag in tags:
        if record.get(tag):
            return record[tag][0]
    return None


def _parse_ris(path: Path, paper_id: str) -> PaperMetadata:
    records = _ris_records(path)
    if len(records) != 1:
        raise MetadataImportError("A paper metadata file must contain exactly one RIS record")
    record = records[0]
    return _build_metadata(paper_id, {
        "title": _first(record, "TI", "T1"),
        "authors": record.get("AU", []) or record.get("A1", []),
        "year": _first(record, "PY", "Y1", "DA"),
        "journal": _first(record, "JO", "JF", "T2", "JA"),
        "doi": _first(record, "DO"),
        "keywords": record.get("KW", []),
        "citation": _first(record, "C1"),
    })


def parse_metadata(path: str | Path, *, paper_id: str) -> PaperMetadata:
    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix == ".bib":
        return _parse_bib(source, paper_id)
    if suffix == ".ris":
        return _parse_ris(source, paper_id)
    raise MetadataImportError(f"Unsupported metadata format: {source.suffix}")


def _status_mapping(value: Any) -> dict[str, bool]:
    names = (
        "imported", "metadata_ready", "parsed", "figures_processed",
        "tables_processed", "knowledge_ready",
    )
    if isinstance(value, dict):
        return {name: bool(value.get(name, False)) for name in names}
    status = str(value or "")
    if status not in names:
        return {name: False for name in names}
    position = names.index(status)
    return {name: index <= position for index, name in enumerate(names)}


def import_metadata(
    path: str | Path,
    *,
    paper_id: str,
    metadata_root: str | Path = "data/metadata",
    registry_path: str | Path = "data/papers/registry.yaml",
) -> Path:
    """Import one record and advance its existing Registry record."""
    registry_file = Path(registry_path)
    registry = yaml.safe_load(registry_file.read_text(encoding="utf-8"))
    papers = registry.get("papers", []) if isinstance(registry, dict) else []
    matches = [item for item in papers if item.get("paper_id") == paper_id]
    if len(matches) != 1:
        raise MetadataImportError(
            f"Registry must contain exactly one existing record for {paper_id}"
        )
    metadata = parse_metadata(path, paper_id=paper_id)
    output = Path(metadata_root) / f"{paper_id}.yaml"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(metadata.to_mapping(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    record = matches[0]
    status = _status_mapping(record.get("processing_status"))
    status["metadata_ready"] = True
    record["processing_status"] = status
    record["metadata_path"] = output.as_posix()
    record["title"] = metadata.title
    record["authors"] = list(metadata.authors)
    record["year"] = metadata.year
    record["journal"] = metadata.journal
    record["DOI"] = metadata.doi
    registry_file.write_text(
        yaml.safe_dump(registry, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return output
