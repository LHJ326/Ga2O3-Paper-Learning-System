"""Local FAISS vector-store integration for evidence-linked chunks."""

from .faiss_store import FaissStore
from .index_manager import IndexManager, build_mock_vectors
from .schema import SearchHit, VectorStore, VectorStoreError

__all__ = [
    "FaissStore",
    "IndexManager",
    "SearchHit",
    "VectorStore",
    "VectorStoreError",
    "build_mock_vectors",
]
