import json
from pathlib import Path

import pytest
import yaml

from scripts.prepare_p001_embeddings import prepare_p001_dry_run
from src.embedding import (
    EmbeddingAdapter,
    EmbeddingChunk,
    EmbeddingSchemaError,
    LocalVectorStore,
    PaperObjectChunker,
    VectorStoreError,
)


def _paper_object() -> dict:
    return {
        "paper_identity": {"paper_id": "P001"},
        "source": {
            "evidence_index": [
                {"evidence_id": "E00001"},
                {"evidence_id": "E00002"},
            ]
        },
        "knowledge": {
            "summary": "## Objective\nEvidence-backed result [E00001].\nUnsupported prose.",
            "parameters": {
                "material": {
                    "semiconductor": {
                        "value": "Ga2O3",
                        "evidence_id": "E00002",
                        "page": 1,
                    }
                }
            },
            "performance": None,
            "mechanism": None,
        },
    }


def _chunk(chunk_id: str, text: str = "text") -> EmbeddingChunk:
    return EmbeddingChunk(chunk_id, "P001", "paper_object.yaml", ("E00001",), text)


class StubEmbeddingAdapter(EmbeddingAdapter):
    def embed(self, texts):
        return [[float(len(text)), 1.0] for text in texts]


def test_embedding_chunk_schema_and_adapter_contract() -> None:
    chunk = _chunk("P001-summary-0001")
    assert chunk.as_dict()["evidence_ids"] == ["E00001"]
    assert StubEmbeddingAdapter().embed(["abc"]) == [[3.0, 1.0]]
    with pytest.raises(EmbeddingSchemaError, match="at least one"):
        EmbeddingChunk("id", "P001", "source", (), "text")


def test_paper_object_chunker_is_deterministic_and_evidence_first() -> None:
    chunker = PaperObjectChunker()
    first = chunker.chunk(_paper_object(), source_file="data/papers/P001/paper_object.yaml")
    second = chunker.chunk(_paper_object(), source_file="data/papers/P001/paper_object.yaml")
    assert first == second
    assert [item.chunk_id for item in first] == [
        "P001-summary-0001", "P001-parameters-0001"
    ]
    assert all(item.evidence_ids for item in first)
    assert all("Unsupported prose" not in item.text for item in first)


def test_chunker_rejects_unresolved_evidence() -> None:
    payload = _paper_object()
    payload["knowledge"]["summary"] = "Claim [E99999]."
    with pytest.raises(EmbeddingSchemaError, match="unknown Evidence"):
        PaperObjectChunker().chunk(payload, source_file="paper_object.yaml")


def test_local_vector_store_add_search_and_save(tmp_path: Path) -> None:
    store = LocalVectorStore()
    chunks = [_chunk("c1", "one"), _chunk("c2", "two")]
    store.add(chunks, [[1.0, 0.0], [0.0, 1.0]])
    results = store.search([0.9, 0.1], top_k=1)
    assert results[0].chunk.chunk_id == "c1"
    assert results[0].score > 0.9
    output = store.save(tmp_path / "vectors.json")
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["dimension"] == 2
    assert len(saved["entries"]) == 2
    with pytest.raises(VectorStoreError, match="equal lengths"):
        store.add([_chunk("c3")], [])


def test_p001_dry_run_writes_report_without_vectors(tmp_path: Path) -> None:
    (tmp_path / "data/papers/P001").mkdir(parents=True)
    (tmp_path / "data/papers/P001/paper_object.yaml").write_text(
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
    report = prepare_p001_dry_run(tmp_path)
    saved = yaml.safe_load(
        (tmp_path / "data/papers/P001/embedding_report.yaml").read_text(encoding="utf-8")
    )
    assert report["adapter_calls"] == 0
    assert report["vectors_generated"] == 0
    assert report["vector_store_written"] is False
    assert report["registry_embedding_status"] == "pending"
    assert saved == report
