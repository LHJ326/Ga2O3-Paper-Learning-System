import json
from pathlib import Path

from src.knowledge import (
    ExtractionContext,
    KnowledgeDraft,
    KnowledgeExtractionPipeline,
    KnowledgeExtractor,
    KnowledgeValidator,
    KnowledgeWriter,
    LLMKnowledgeExtractor,
    load_knowledge_schema,
)
from src.llm import MockLLMAdapter
from src.schema import Document, Metadata, TextBlock


def parsed_document() -> Document:
    return Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "Test paper", "metadata.json"),
        text_blocks=[TextBlock(
            id="P001-text-1",
            page_number=1,
            content="The responsivity is 2.5 A/W at 254 nm.",
            source_reference='{"source_file":"P001.json","page":1}',
        )],
    )


def response_payload() -> str:
    return json.dumps({
        "core": {
            "paper_identity": {"title": "Test paper"},
            "research_problem": [{
                "statement": "Measure UV photodetector performance.",
                "evidence_refs": ["E00001"],
            }],
            "methodology": [],
            "results": [{
                "claim": "Responsivity reached 2.5 A/W at 254 nm.",
                "metric": "responsivity",
                "value": 2.5,
                "unit": "A/W",
                "conditions": "254 nm",
                "evidence_refs": ["E00001"],
            }],
            "innovation": [],
            "limitations": [],
        },
        "domain": {"fields": {
            "optical_performance": [{
                "metric": "responsivity",
                "value": 2.5,
                "unit": "A/W",
                "conditions": "254 nm",
                "evidence_refs": ["E00001"],
            }],
        }},
        "summary": "# Summary\n\nResponsivity was 2.5 A/W at 254 nm [E00001].",
        "key_points": "# Key Points\n\n- 2.5 A/W at 254 nm [E00001].",
    })


def test_llm_extractor_uses_mock_adapter_and_builds_traceable_draft() -> None:
    schema = load_knowledge_schema()
    adapter = MockLLMAdapter(generate_responses=[response_payload()])
    extractor = LLMKnowledgeExtractor(adapter)
    draft = extractor.extract(ExtractionContext(
        paper_id="P001",
        document=parsed_document(),
        schema=schema,
        source_document="data/parsed/P001/mineru/raw",
    ))

    assert draft.paper_id == "P001"
    assert draft.core["paper_identity"]["paper_id"] == "P001"
    assert draft.core["evidence_traceability"]["evidence_index"][0]["element_id"] == "P001-text-1"
    assert draft.domain["fields"]["optical_performance"][0]["value"] == 2.5
    assert "E00001" in adapter.generate_calls[0]


class StaticExtractor(KnowledgeExtractor):
    def __init__(self, draft: KnowledgeDraft) -> None:
        super().__init__(MockLLMAdapter())
        self.draft = draft
        self.calls = 0

    def extract(self, context: ExtractionContext) -> KnowledgeDraft:
        self.calls += 1
        return self.draft


def test_pipeline_runs_extractor_validator_and_writer(tmp_path: Path) -> None:
    schema = load_knowledge_schema()
    draft = LLMKnowledgeExtractor(
        MockLLMAdapter(generate_responses=[response_payload()])
    ).extract(ExtractionContext(
        paper_id="P001",
        document=parsed_document(),
        schema=schema,
        source_document="data/parsed/P001/mineru/raw",
    ))
    extractor = StaticExtractor(draft)
    papers_root = tmp_path / "papers"
    (papers_root / "P001").mkdir(parents=True)
    validator = KnowledgeValidator(schema)
    pipeline = KnowledgeExtractionPipeline(
        extractor=extractor,
        validator=validator,
        writer=KnowledgeWriter(validator=validator, papers_root=papers_root),
    )

    paths = pipeline.run(
        paper_id="P001",
        document=parsed_document(),
        schema=schema,
        source_document="data/parsed/P001/mineru/raw",
    )

    assert extractor.calls == 1
    assert paths["summary"].is_file()
    assert paths["key_points"].is_file()
    assert paths["device_parameters"].is_file()
    assert "2.5" in paths["device_parameters"].read_text(encoding="utf-8")
