import os
from pathlib import Path

import pytest

from src.llm.deepseek_adapter import DeepSeekLLMAdapter, load_dotenv


def test_dotenv_loading_allows_adapter_initialization_without_printing_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    fake_key = "test-only-deepseek-key-never-send"
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    test_env = tmp_path / ".env"
    test_env.write_text(f"DEEPSEEK_API_KEY={fake_key}\n", encoding="utf-8")

    assert load_dotenv(dotenv_path=test_env, override=True)
    adapter = DeepSeekLLMAdapter()

    assert isinstance(adapter, DeepSeekLLMAdapter)
    assert os.getenv("DEEPSEEK_API_KEY") == fake_key
    captured = capsys.readouterr()
    assert fake_key not in captured.out
    assert fake_key not in captured.err
