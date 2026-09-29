"""Run the local P001 FAISS dry-run with deterministic mock vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import PaperObjectChunker
from src.registry import RegistryManager
from src.vectorstore import IndexManager


def prepare_p001_vectorstore_dry_run(
    project_root: str | Path = PROJECT_ROOT,
) -> dict[str, object]:
    root = Path(project_root)
    paper_id = "P001"
    paper_object_path = root / "data" / "papers" / paper_id / "paper_object.yaml"
    payload = yaml.safe_load(paper_object_path.read_text(encoding="utf-8"))
    source_file = paper_object_path.relative_to(root).as_posix()
    chunks = PaperObjectChunker().chunk(payload, source_file=source_file)
    record = RegistryManager(root / "data" / "papers" / "registry.yaml").require_paper(paper_id)
    status = record.get("vectorstore_status")
    if status not in {"pending", "in_progress", "completed", "failed", "skipped"}:
        raise RuntimeError("P001 vectorstore_status is missing or invalid")
    storage_path = Path("data") / "vectorstore" / f"{paper_id}.faiss"
    report = IndexManager().dry_run(
        chunks,
        paper_id=paper_id,
        storage_path=storage_path,
        registry_vectorstore_status=status,
    )
    destination = root / "data" / "papers" / paper_id / "vectorstore_report.yaml"
    destination.write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    report = prepare_p001_vectorstore_dry_run(args.project_root)
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
