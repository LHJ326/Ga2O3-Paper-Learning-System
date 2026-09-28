import pytest

from scripts.test_deepseek_connection import MINIMAL_PROMPT, run_connection_test
from src.llm import DeepSeekConfigurationError, MockLLMAdapter


def test_connection_script_reports_missing_key_before_creating_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    factory_called = False

    def factory() -> MockLLMAdapter:
        nonlocal factory_called
        factory_called = True
        return MockLLMAdapter(default_response="unexpected")

    with pytest.raises(DeepSeekConfigurationError, match="DEEPSEEK_API_KEY"):
        run_connection_test(adapter_factory=factory)
    assert not factory_called


def test_connection_script_supports_mock_adapter_without_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-key")
    adapter = MockLLMAdapter(default_response="DeepSeek connection OK")

    response = run_connection_test(adapter=adapter)

    assert response == "DeepSeek connection OK"
    assert adapter.generate_calls == [MINIMAL_PROMPT]
    assert capsys.readouterr().out == (
        "DeepSeek response:\nDeepSeek connection OK\n"
    )
