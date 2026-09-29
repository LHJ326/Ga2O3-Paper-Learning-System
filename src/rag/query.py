"""Public natural-language query interface for retrieval-only RAG."""

from __future__ import annotations

from .response_schema import QueryResponse
from .retriever import Retriever


class RAGQuery:
    """Return structured retrieval results without generating an answer."""

    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever

    def query(self, question: str, *, top_k: int = 5) -> QueryResponse:
        results = self.retriever.search(question, top_k=top_k)
        return QueryResponse(query=question, top_k=top_k, results=tuple(results))
