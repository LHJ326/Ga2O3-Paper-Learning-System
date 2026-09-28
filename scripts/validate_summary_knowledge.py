"""Validate one existing evidence-linked paper summary without model access."""

from __future__ import annotations

import argparse

from src.knowledge import SummaryKnowledgeValidator


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_id", help="Existing Paper Object ID, for example P001")
    args = parser.parse_args()
    report, paths = SummaryKnowledgeValidator().validate_and_write(args.paper_id)
    print(f"Paper: {report.paper_id}")
    print(f"Structure score: {report.structure.score}")
    print(f"Evidence score: {report.evidence.coverage}")
    print(f"Overall status: {report.overall_status}")
    print(f"Review required: {report.review_required}")
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
