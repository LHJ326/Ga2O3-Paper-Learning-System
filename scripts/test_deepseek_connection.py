"""Send one minimal DeepSeek request without touching paper data."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable

from src.llm import (
    DeepSeekAPIError,
    DeepSeekConfigurationError,
    DeepSeekLLMAdapter,
    LLMAdapter,
)
from src.llm.deepseek_adapter import DEEPSEEK_API_KEY_ENV


MINIMAL_PROMPT = "Reply with exactly: DeepSeek connection OK"


def run_connection_test(
    *,
    adapter: LLMAdapter | None = None,
    adapter_factory: Callable[[], LLMAdapter] = DeepSeekLLMAdapter,
) -> str:
    """Check configuration, make one minimal request, and print its response."""
    if not os.environ.get(DEEPSEEK_API_KEY_ENV, "").strip():
        raise DeepSeekConfigurationError(
            f"environment variable {DEEPSEEK_API_KEY_ENV} is not set"
        )
    client = adapter if adapter is not None else adapter_factory()
    response = client.generate(MINIMAL_PROMPT)
    print("DeepSeek response:")
    print(response)
    return response


def main() -> int:
    try:
        run_connection_test()
    except (DeepSeekConfigurationError, DeepSeekAPIError) as error:
        print(f"DeepSeek connection test failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
