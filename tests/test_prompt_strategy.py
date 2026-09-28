import json

from src.knowledge import (
    EvidenceChunker,
    ExtractionContext,
    ExtractionTask,
    KnowledgePromptBuilder,
    KnowledgeValidator,
    PromptStrategyRegistry,
    StrategyPromptBuilder,
    StrategyKnowledgeExtractor,
    load_knowledge_schema,
)
from src.llm import MockLLMAdapter
from src.schema import Document, Equation, Figure, Metadata, Section, Table, TextBlock


def strategy_document(long_text: str = "measurement text") -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "title", "metadata.json"),
        sections=[
            Section("section-1", 1, "Introduction", "s1"),
            Section("section-2", 2, "Results", "s2"),
        ],
        text_blocks=[
            TextBlock("text-1", 1, long_text, "t1"),
            TextBlock("text-2", 2, "mechanism discussion", "t2"),
        ],
        figures=[Figure("figure-1", 2, "Figure 1", "f1")],
        tables=[Table("table-1", 2, "responsivity table", "tb1")],
        equations=[Equation("equation-1", 2, "R=I/P", "e1")],
    )


def test_chunks_preserve_task_section_and_element_type_boundaries() -> None:
    evidence = KnowledgePromptBuilder.evidence_from_document(strategy_document())
    strategy = PromptStrategyRegistry().get(ExtractionTask.SUMMARY)
    chunks = EvidenceChunker(max_content_chars=800).chunk(evidence, strategy)

    assert chunks
    for chunk in chunks:
        assert chunk.task is ExtractionTask.SUMMARY
        assert {item.section_id for item in chunk.evidence} == {chunk.section_id}
        assert {item.element_type for item in chunk.evidence} == {chunk.element_type}
        assert sum(
            len(json.dumps(item.as_dict(), ensure_ascii=False))
            for item in chunk.evidence
        ) <= 800
    assert {chunk.section_id for chunk in chunks} >= {"section-1", "section-2"}


def test_strategy_prompt_length_is_bounded() -> None:
    document = strategy_document("x" * 30_000)
    context = ExtractionContext("P001", document, load_knowledge_schema())
    evidence = KnowledgePromptBuilder.evidence_from_document(document)
    strategy = PromptStrategyRegistry().get(ExtractionTask.PARAMETER)
    chunks = EvidenceChunker(max_content_chars=5_000).chunk(evidence, strategy)
    builder = StrategyPromptBuilder(max_prompt_chars=12_000)

    prompts = [builder.build(context, strategy, chunk) for chunk in chunks]
    assert len(prompts) > 1
    assert max(map(len, prompts)) <= 12_000


def test_strategy_selection_filters_elements_by_task() -> None:
    registry = PromptStrategyRegistry()
    assert registry.get("summary").prompt_file == "summary_prompt.md"
    assert "Table" in registry.get("parameter").element_types
    assert "Equation" not in registry.get("parameter").element_types
    assert "Equation" in registry.get("mechanism").element_types
    assert registry.get("mechanism").response_shape == {"mechanism": []}
    evidence = KnowledgePromptBuilder.evidence_from_document(strategy_document())
    parameter_chunks = EvidenceChunker().chunk(evidence, registry.get("parameter"))
    mechanism_chunks = EvidenceChunker().chunk(evidence, registry.get("mechanism"))
    assert any(chunk.element_type == "Table" for chunk in parameter_chunks)
    assert any(chunk.element_type == "Equation" for chunk in mechanism_chunks)
    assert all(chunk.element_type != "Equation" for chunk in parameter_chunks)


def test_strategy_extractor_merges_mock_chunk_responses() -> None:
    response = json.dumps({
        "research_problem": [],
        "methodology": [],
        "results": [],
        "innovation": [],
        "limitations": [],
        "summary": "Chunk summary.",
        "key_points": [],
        "fields": {},
        "mechanism": [],
    })
    adapter = MockLLMAdapter(default_response=response)
    schema = load_knowledge_schema()
    extractor = StrategyKnowledgeExtractor(
        adapter,
        chunker=EvidenceChunker(max_content_chars=800),
        prompt_builder=StrategyPromptBuilder(max_prompt_chars=12_000),
    )
    draft = extractor.extract(ExtractionContext(
        "P001", strategy_document(), schema, source_document="parsed/P001"
    ))

    assert len(adapter.generate_calls) > 3
    assert max(map(len, adapter.generate_calls)) <= 12_000
    assert draft.summary.startswith("# Summary")
    assert KnowledgeValidator(schema).validate(draft).valid
