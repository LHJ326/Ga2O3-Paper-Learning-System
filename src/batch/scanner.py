"""Discover P-series papers without modifying the library."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PAPER_ID_PATTERN = re.compile(r"^P(?P<number>\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class PaperCandidate:
    paper_id: str
    object_dir: Path
    source_pdf: Path | None


class PaperScanner:
    def __init__(self, papers_root: str | Path = "data/papers") -> None:
        self.papers_root = Path(papers_root)

    def scan(self) -> list[PaperCandidate]:
        if not self.papers_root.is_dir():
            raise FileNotFoundError(f"papers directory does not exist: {self.papers_root}")
        discovered: dict[str, dict[str, Path | None]] = {}
        for path in self.papers_root.iterdir():
            if path.is_dir():
                match = PAPER_ID_PATTERN.fullmatch(path.name)
                if match:
                    paper_id = f"P{int(match.group('number')):03d}"
                    discovered.setdefault(paper_id, {})["object_dir"] = path
            elif path.is_file() and path.suffix.casefold() == ".pdf":
                match = PAPER_ID_PATTERN.fullmatch(path.stem)
                if match:
                    paper_id = f"P{int(match.group('number')):03d}"
                    discovered.setdefault(paper_id, {})["source_pdf"] = path
        candidates: list[PaperCandidate] = []
        for paper_id in sorted(discovered, key=lambda value: int(value[1:])):
            record = discovered[paper_id]
            candidates.append(PaperCandidate(
                paper_id,
                Path(record.get("object_dir") or self.papers_root / paper_id),
                record.get("source_pdf"),
            ))
        return candidates
