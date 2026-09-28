from __future__ import annotations

import argparse

from .pipeline import ingest_directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Import PDFs into Paper Objects")
    parser.add_argument("input_directory")
    parser.add_argument("--papers-root", default="data/papers")
    parser.add_argument("--metadata-root", default="data/metadata")
    parser.add_argument("--registry", default="data/papers/registry.yaml")
    parser.add_argument("--recursive", action="store_true")
    args = parser.parse_args()
    results = ingest_directory(
        args.input_directory,
        papers_root=args.papers_root,
        metadata_root=args.metadata_root,
        registry_path=args.registry,
        recursive=args.recursive,
    )
    for item in results:
        print(f"{item.paper_id}\t{item.source_pdf}")


if __name__ == "__main__":
    main()
