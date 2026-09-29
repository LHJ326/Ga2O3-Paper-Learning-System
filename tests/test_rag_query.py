from pathlib import Path

import pytest
import yaml

from scripts.query_p001_rag import run_p001_rag_dry_run
from src.embedding import EmbeddingChunk
from src.rag import QueryResponse, RAGQuery, Retriever, RetrievalResult
from src.vectorstore import FaissStore


def _chunk(number: int) -> EmbeddingChunk:
    return EmbeddingChunk(
        chunk_id=f"P001-summary-{number:04d}",
        paper_id="P001",
        source_file="data/papers/P001/paper_object.yaml",
        evidence_ids=(f"E{number:05d}",),
        text=f"content {number}",
    )


def _paper_object() -> dict:
    return {
        "paper_identity": {"paper_id": "P001"},
        "source": {"evidence_index": [
            {"evidence_id": "E00001"}, {"evidence_id": "E00002"}
        ]},
        "knowledge": {
            "summary": "## Results\nFirst claim [E00001].\nSecond claim [E00002].",
            "parameters": None,
            "performance": None,
            "mechanism": None,
        },
    }


def test_retriever_returns_evidence_aware_structured_results() -> None:
    store = FaissStore()
    store.add([_chunk(1), _chunk(2)], [[1.0, 0.0], [0.0, 1.0]])
    results = Retriever(store, lambda _: [1.0, 0.0]).search("material?", top_k=1)
    assert len(results) == 1
    assert results[0].paper_id == "P001"
    assert results[0].chunk_id == "P001-summary-0001"
    assert results[0].evidence_ids == ("E00001",)
    assert results[0].source == "data/papers/P001/paper_object.yaml"
    assert results[0].similarity == pytest.approx(1.0)


def test_query_interface_returns_schema_without_generated_answer() -> None:
    store = FaissStore()
    store.add([_chunk(1)], [[1.0, 0.0]])
    response = RAGQuery(Retriever(store, lambda _: [1.0, 0.0])).query(
        "What is reported?", top_k=3
    )
    assert isinstance(response, QueryResponse)
    assert response.as_dict() == {
        "query": "What is reported?",
        "top_k": 3,
        "results": [{
            "paper_id": "P001",
            "chunk_id": "P001-summary-0001",
            "similarity": 1.0,
            "evidence_ids": ["E00001"],
            "source": "data/papers/P001/paper_object.yaml",
        }],
    }


def test_query_validation_rejects_blank_question_and_invalid_top_k() -> None:
    retriever = Retriever(FaissStore(), lambda _: [1.0])
    with pytest.raises(ValueError, match="non-empty"):
        retriever.search(" ")
    with pytest.raises(ValueError, match="positive"):
        retriever.search("question", top_k=0)
    with pytest.raises(ValueError, match="Evidence IDs"):
        RetrievalResult("P001", "chunk", 1.0, (), "source")


def test_p001_rag_dry_run_writes_structured_report(tmp_path: Path) -> None:
    paper_dir = tmp_path / "data/papers/P001"
    paper_dir.mkdir(parents=True)
    (paper_dir / "paper_object.yaml").write_text(
        yaml.safe_dump(_paper_object(), sort_keys=False), encoding="utf-8"
    )
    registry = {
        "registry_version": "2.0",
        "paper_record_fields": [],
        "lifecycle_status_values": ["pending", "in_progress", "completed", "failed", "skipped"],
        "lifecycle_status_template": {},
        "processing_status_values": [],
        "processing_status_template": {},
        "papers": [{
            "paper_id": "P001", "title": None, "authors": None, "year": None,
            "journal": None, "DOI": None, "source_pdf": None,
            "metadata_path": None, "parsed_path": None,
            "processing_status": "completed", "metadata_status": "completed",
            "knowledge_status": "completed", "object_status": "completed",
            "embedding_status": "pending", "rag_status": "pending",
        }],
    }
    (tmp_path / "data/papers/registry.yaml").write_text(
        yaml.safe_dump(registry, sort_keys=False), encoding="utf-8"
    )
    report = run_p001_rag_dry_run(tmp_path, question="What is reported?", top_k=2)
    saved = yaml.safe_load((paper_dir / "rag_report.yaml").read_text(encoding="utf-8"))
    assert saved == report
    assert report["query"] == "What is reported?"
    assert report["top_k"] == 2
    assert len(report["results"]) == 2
    assert all(item["evidence_ids"] for item in report["results"])
    assert report["llm_generation"] is False
    assert report["llm_api_calls"] == 0
