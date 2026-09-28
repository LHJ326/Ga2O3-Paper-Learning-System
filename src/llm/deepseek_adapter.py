"""DeepSeek implementation of the provider-neutral LLM interface."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeAlias
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from .base import ChatMessage, LLMAdapter


load_dotenv()


DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"

DeepSeekTransport: TypeAlias = Callable[
    [str, Mapping[str, str], bytes, float], Mapping[str, Any]
]


class DeepSeekConfigurationError(RuntimeError):
    """Raised when required local DeepSeek configuration is unavailable."""


class DeepSeekAPIError(RuntimeError):
    """Raised when DeepSeek cannot return a usable completion."""


def _http_transport(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout: float,
) -> Mapping[str, Any]:
    request = Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise DeepSeekAPIError(
            f"DeepSeek API returned HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise DeepSeekAPIError(f"DeepSeek API request failed: {error.reason}") from error

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as error:
        raise DeepSeekAPIError("DeepSeek API returned invalid JSON") from error
    if not isinstance(parsed, Mapping):
        raise DeepSeekAPIError("DeepSeek API returned a non-object response")
    return parsed


class DeepSeekLLMAdapter(LLMAdapter):
    """Synchronous adapter for DeepSeek's Chat Completions endpoint.

    The API key is read exclusively from ``DEEPSEEK_API_KEY`` when a request is
    made. A transport may be injected for deterministic tests; production use
    defaults to the standard-library HTTPS transport.
    """

    def __init__(
        self,
        *,
        model: str = "deepseek-v4-flash",
        timeout: float = 60.0,
        transport: DeepSeekTransport | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.model = model
        self.timeout = timeout
        self._transport = transport or _http_transport

    def generate(self, prompt: str) -> str:
        """Generate text by sending the prompt as one user message."""
        return self.chat([{"role": "user", "content": prompt}])

    def chat(self, messages: Sequence[ChatMessage]) -> str:
        """Return the assistant content for an ordered message sequence."""
        normalized = self._normalize_messages(messages)
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise DeepSeekConfigurationError(
                f"environment variable {DEEPSEEK_API_KEY_ENV} is not set"
            )

        body = json.dumps(
            {"model": self.model, "messages": normalized, "stream": False},
            ensure_ascii=False,
        ).encode("utf-8")
        response = self._transport(
            DEEPSEEK_API_URL,
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            body,
            self.timeout,
        )
        return self._content_from_response(response)

    @staticmethod
    def _normalize_messages(messages: Sequence[ChatMessage]) -> list[dict[str, str]]:
        if not messages:
            raise ValueError("messages must not be empty")
        normalized: list[dict[str, str]] = []
        for index, message in enumerate(messages):
            role = message.get("role")
            content = message.get("content")
            if not isinstance(role, str) or not role:
                raise ValueError(f"messages[{index}].role must be a non-empty string")
            if not isinstance(content, str):
                raise ValueError(f"messages[{index}].content must be a string")
            normalized.append({"role": role, "content": content})
        return normalized

    @staticmethod
    def _content_from_response(response: Mapping[str, Any]) -> str:
        try:
            choices = response["choices"]
            message = choices[0]["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise DeepSeekAPIError(
                "DeepSeek API response does not contain assistant content"
            ) from error
        if not isinstance(content, str):
            raise DeepSeekAPIError("DeepSeek assistant content is not text")
        return content
