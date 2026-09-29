import json
from pathlib import Path

import pytest
import yaml

from scripts.prepare_p001_vectorstore import prepare_p001_vectorstore_dry_run
from src.embedding import EmbeddingChunk
from src.vectorstore import FaissStore, IndexManager, VectorStoreError, build_mock_vectors


def _chunk(number: int) -> EmbeddingChunk:
    return EmbeddingChunk(
        chunk_id=f"P001-summary-{number:04d}",
        paper_id="P001",
        source_file="data/papers/P001/paper_object.yaml",
        evidence_ids=(f"E{number:05d}",),
        text=f"Evidence-linked content {number}",
    )


def _paper_object() -> dict:
    return {
        "paper_identity": {"paper_id": "P001"},
        "source": {"evidence_index": [{"evidence_id": "E00001"}]},
        "knowledge": {
            "summary": "## Result\nSupported statement [E00001].",
            "parameters": None,
            "performance": None,
            "mechanism": None,
        },
    }


def test_faiss_store_add_and_cosine_search() -> None:
    store = FaissStore()
    chunks = [_chunk(1), _chunk(2)]
    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])
    hits = store.search([0.9, 0.1], top_k=1)
    assert store.size == 2
    assert store.dimension == 2
    assert hits[0].chunk.chunk_id == chunks[0].chunk_id
    assert hits[0].score > 0.9


def test_faiss_store_save_and_load_preserves_evidence(tmp_path: Path) -> None:
    store = FaissStore()
    chunks = [_chunk(1), _chunk(2)]
    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])
    index_path = store.save(tmp_path / "P001.faiss")
    loaded = FaissStore.load(index_path)
    hit = loaded.search([0.0, 1.0], top_k=1)[0]
    assert loaded.size == 2
    assert hit.chunk.evidence_ids == ("E00002",)
    metadata = json.loads(
        (tmp_path / "P001.faiss.meta.json").read_text(encoding="utf-8")
    )
    assert metadata["backend"] == "faiss.IndexFlatIP"
    assert metadata["count"] == 2


def test_faiss_store_rejects_invalid_vectors_and_duplicates() -> None:
    store = FaissStore()
    with pytest.raises(VectorStoreError, match="equal lengths"):
        store.add([_chunk(1)], [])
    with pytest.raises(VectorStoreError, match="zero vectors"):
        store.add([_chunk(1)], [[0.0, 0.0]])
    store.add([_chunk(1)], [[1.0, 0.0]])
    with pytest.raises(VectorStoreError, match="duplicate chunk_id"):
        store.add([_chunk(1)], [[0.0, 1.0]])


def test_index_manager_uses_deterministic_mock_vectors_without_persistence() -> None:
    chunks = [_chunk(1), _chunk(2)]
    assert build_mock_vectors(chunks) == build_mock_vectors(chunks)
    report = IndexManager().dry_run(
        chunks,
        paper_id="P001",
        storage_path="data/vectorstore/P001.faiss",
        registry_vectorstore_status="pending",
    )
    assert report["chunk_count"] == 2
    assert report["index_count"] == 2
    assert report["embedding_api_calls"] == 0
    assert report["index_saved"] is False


def test_p001_vectorstore_dry_run_writes_report(tmp_path: Path) -> None:
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
            "embedding_status": "pending", "vectorstore_status": "pending",
            "rag_status": "pending",
        }],
    }
    (tmp_path / "data/papers/registry.yaml").write_text(
        yaml.safe_dump(registry, sort_keys=False), encoding="utf-8"
    )
    report = prepare_p001_vectorstore_dry_run(tmp_path)
    saved = yaml.safe_load((paper_dir / "vectorstore_report.yaml").read_text(encoding="utf-8"))
    assert saved == report
    assert report["chunk_count"] == 1
    assert report["index_count"] == 1
    assert report["storage_path"] == "data/vectorstore/P001.faiss"
    assert report["registry_vectorstore_status"] == "pending"
    assert not (tmp_path / "data/vectorstore/P001.faiss").exists()
