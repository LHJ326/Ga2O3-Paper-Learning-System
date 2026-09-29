"""Model-independent embedding foundation for evidence-linked Paper Objects."""

from .chunker import PaperObjectChunker, build_dry_run_report
from .embedder import EmbeddingAdapter
from .schema import EmbeddingChunk, EmbeddingSchemaError
from .vector_store import LocalVectorStore, SearchResult, VectorStoreError

__all__ = [
    "EmbeddingAdapter",
    "EmbeddingChunk",
    "EmbeddingSchemaError",
    "LocalVectorStore",
    "PaperObjectChunker",
    "SearchResult",
    "VectorStoreError",
    "build_dry_run_report",
]
