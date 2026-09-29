"""Evidence-aware retrieval without language-model generation."""

from .query import RAGQuery
from .response_schema import QueryResponse, RetrievalResult, ResponseSchemaError
from .retriever import Retriever, build_mock_query_vector

__all__ = [
    "QueryResponse",
    "RAGQuery",
    "ResponseSchemaError",
    "RetrievalResult",
    "Retriever",
    "build_mock_query_vector",
]
