import json
from collections.abc import Mapping
from typing import Any

import pytest

from src.llm import (
    DeepSeekConfigurationError,
    DeepSeekLLMAdapter,
    LLMAdapter,
)


def test_missing_api_key_fails_before_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    called = False

    def transport(
        url: str, headers: Mapping[str, str], body: bytes, timeout: float
    ) -> Mapping[str, Any]:
        nonlocal called
        called = True
        return {}

    adapter = DeepSeekLLMAdapter(transport=transport)
    with pytest.raises(DeepSeekConfigurationError, match="DEEPSEEK_API_KEY"):
        adapter.generate("test")
    assert not called


def test_mock_transport_exercises_generate_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-key")
    captured: dict[str, Any] = {}

    def transport(
        url: str, headers: Mapping[str, str], body: bytes, timeout: float
    ) -> Mapping[str, Any]:
        captured.update(
            url=url,
            headers=dict(headers),
            payload=json.loads(body),
            timeout=timeout,
        )
        return {"choices": [{"message": {"content": "mock response"}}]}

    adapter = DeepSeekLLMAdapter(
        model="test-model", timeout=12.0, transport=transport
    )

    assert adapter.generate("Summarize the paper") == "mock response"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["payload"] == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Summarize the paper"}],
        "stream": False,
    }
    assert captured["headers"]["Authorization"] == "Bearer test-only-key"
    assert captured["timeout"] == 12.0


def test_adapter_interface_and_chat_are_consistent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-key")
    received_messages: list[dict[str, str]] = []

    def transport(
        url: str, headers: Mapping[str, str], body: bytes, timeout: float
    ) -> Mapping[str, Any]:
        received_messages.extend(json.loads(body)["messages"])
        return {"choices": [{"message": {"content": "chat response"}}]}

    adapter = DeepSeekLLMAdapter(transport=transport)
    assert isinstance(adapter, LLMAdapter)
    assert adapter.chat([
        {"role": "system", "content": "Use evidence only."},
        {"role": "user", "content": "Extract parameters."},
    ]) == "chat response"
    assert received_messages == [
        {"role": "system", "content": "Use evidence only."},
        {"role": "user", "content": "Extract parameters."},
    ]
