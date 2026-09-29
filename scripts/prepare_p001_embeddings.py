"""Create the P001 embedding dry-run report without calling an embedding API."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import PaperObjectChunker, build_dry_run_report
from src.registry import RegistryManager


def prepare_p001_dry_run(project_root: str | Path = PROJECT_ROOT) -> dict[str, object]:
    root = Path(project_root)
    paper_id = "P001"
    object_path = root / "data" / "papers" / paper_id / "paper_object.yaml"
    registry = RegistryManager(root / "data" / "papers" / "registry.yaml")
    record = registry.require_paper(paper_id)
    if record["object_status"] != "completed":
        raise RuntimeError("P001 object_status must be completed before embedding preparation")
    source_file = object_path.relative_to(root).as_posix()
    payload = yaml.safe_load(object_path.read_text(encoding="utf-8"))
    chunks = PaperObjectChunker().chunk(payload, source_file=source_file)
    report = build_dry_run_report(
        chunks,
        paper_id=paper_id,
        source_file=source_file,
        registry_embedding_status=record["embedding_status"],
    )
    destination = root / "data" / "papers" / paper_id / "embedding_report.yaml"
    destination.write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    report = prepare_p001_dry_run(args.project_root)
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
