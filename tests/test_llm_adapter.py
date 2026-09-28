from collections.abc import Sequence

from src.knowledge import ExtractionContext, KnowledgeDraft, KnowledgeExtractor
from src.llm import ChatMessage, LLMAdapter, MockLLMAdapter


class ExampleExtractor(KnowledgeExtractor):
    def extract(self, context: ExtractionContext) -> KnowledgeDraft:
        summary = self.generate(f"Summarize {context.paper_id}")
        key_points = self.chat([
            {"role": "system", "content": "Extract evidence-grounded key points."},
            {"role": "user", "content": context.paper_id},
        ])
        return KnowledgeDraft(
            paper_id=context.paper_id,
            core={},
            domain={},
            summary=summary,
            key_points=key_points,
        )


def test_adapter_interface_is_provider_neutral() -> None:
    assert LLMAdapter.__abstractmethods__ == {"generate", "chat"}

    class MinimalAdapter(LLMAdapter):
        def generate(self, prompt: str) -> str:
            return prompt

        def chat(self, messages: Sequence[ChatMessage]) -> str:
            return messages[-1]["content"]

    adapter = MinimalAdapter()
    assert adapter.generate("prompt") == "prompt"
    assert adapter.chat([{"role": "user", "content": "hello"}]) == "hello"


def test_mock_adapter_returns_queued_responses_and_records_calls() -> None:
    adapter = MockLLMAdapter(
        generate_responses=["generated"],
        chat_responses=["chatted"],
        default_response="fallback",
    )
    messages = [{"role": "user", "content": "question"}]

    assert adapter.generate("prompt") == "generated"
    assert adapter.chat(messages) == "chatted"
    assert adapter.generate("another") == "fallback"
    assert adapter.generate_calls == ["prompt", "another"]
    assert adapter.chat_calls == [({"role": "user", "content": "question"},)]


def test_extractor_calls_injected_llm_adapter() -> None:
    adapter = MockLLMAdapter(
        generate_responses=["Paper summary"],
        chat_responses=["- Key point"],
    )
    extractor = ExampleExtractor(adapter)
    context = ExtractionContext(
        paper_id="P101",
        document=object(),
        schema=object(),  # type: ignore[arg-type]
    )

    draft = extractor.extract(context)

    assert draft.summary == "Paper summary"
    assert draft.key_points == "- Key point"
    assert adapter.generate_calls == ["Summarize P101"]
    assert adapter.chat_calls[0][-1]["content"] == "P101"
