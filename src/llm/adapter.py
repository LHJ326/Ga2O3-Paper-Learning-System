"""Deterministic adapters used by the framework and its tests."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence

from .base import ChatMessage, LLMAdapter


class MockLLMAdapter(LLMAdapter):
    """Return configured responses without network or model access.

    Calls are recorded so orchestration tests can assert exactly what the
    extractor sent to the model boundary. When response queues are exhausted,
    the configured default response is returned.
    """

    def __init__(
        self,
        *,
        generate_responses: Iterable[str] = (),
        chat_responses: Iterable[str] = (),
        default_response: str = "",
    ) -> None:
        self._generate_responses = deque(generate_responses)
        self._chat_responses = deque(chat_responses)
        self.default_response = default_response
        self.generate_calls: list[str] = []
        self.chat_calls: list[tuple[dict[str, str], ...]] = []

    def generate(self, prompt: str) -> str:
        self.generate_calls.append(prompt)
        if self._generate_responses:
            return self._generate_responses.popleft()
        return self.default_response

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        snapshot = tuple(dict(message) for message in messages)
        self.chat_calls.append(snapshot)
        if self._chat_responses:
            return self._chat_responses.popleft()
        return self.default_response
