"""Run the P001 Evidence-aware retrieval dry-run without LLM generation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import PaperObjectChunker
from src.rag import RAGQuery, Retriever, build_mock_query_vector
from src.registry import RegistryManager
from src.vectorstore import IndexManager, build_mock_vectors

DEFAULT_QUERY = "What material and device structure are reported for P001?"


def run_p001_rag_dry_run(
    project_root: str | Path = PROJECT_ROOT,
    *,
    question: str = DEFAULT_QUERY,
    top_k: int = 5,
) -> dict[str, object]:
    root = Path(project_root)
    paper_id = "P001"
    object_path = root / "data" / "papers" / paper_id / "paper_object.yaml"
    payload = yaml.safe_load(object_path.read_text(encoding="utf-8"))
    chunks = PaperObjectChunker().chunk(
        payload, source_file=object_path.relative_to(root).as_posix()
    )
    dimension = 16
    store = IndexManager().build(chunks, build_mock_vectors(chunks, dimension=dimension))
    retriever = Retriever(
        store, lambda text: build_mock_query_vector(text, dimension=dimension)
    )
    response = RAGQuery(retriever).query(question, top_k=top_k)
    registry_status = RegistryManager(
        root / "data" / "papers" / "registry.yaml"
    ).require_paper(paper_id)["rag_status"]
    report: dict[str, object] = {
        "paper_id": paper_id,
        "mode": "dry_run",
        "backend": "faiss.IndexFlatIP",
        "vector_source": "deterministic_mock",
        "llm_generation": False,
        "llm_api_calls": 0,
        "registry_rag_status": registry_status,
        **response.as_dict(),
    }
    destination = root / "data" / "papers" / paper_id / "rag_report.yaml"
    destination.write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default=DEFAULT_QUERY)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    report = run_p001_rag_dry_run(
        args.project_root, question=args.question, top_k=args.top_k
    )
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
