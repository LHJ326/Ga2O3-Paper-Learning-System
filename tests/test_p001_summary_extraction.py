import json
from pathlib import Path

import yaml

from src.knowledge import load_knowledge_schema
from src.knowledge.p001_summary import P001SummaryExtractor
from src.llm import MockLLMAdapter
from src.schema import Document, Metadata, Section, TextBlock


def test_summary_only_extraction_writes_summary_and_diagnostics(tmp_path: Path) -> None:
    document = Document(
        document_id="P001",
        metadata=Metadata("metadata", 1, "Paper", "metadata.json"),
        sections=[Section("section-1", 1, "Results", "section.json")],
        text_blocks=[TextBlock(
            "text-1", 1, "The device reached 2.5 A/W.", "text.json"
        )],
    )
    response = json.dumps({
        "research_problem": [{
            "statement": "Develop a UV photodetector.",
            "evidence_refs": ["E00002"],
        }],
        "methodology": [],
        "results": [{
            "claim": "The device reached 2.5 A/W.",
            "evidence_refs": ["E00002"],
        }],
        "innovation": ["A device innovation was demonstrated [E00002]."],
        "limitations": [],
        "summary": "unused chunk summary",
        "key_points": [],
    })
    adapter = MockLLMAdapter(default_response=response)

    result = P001SummaryExtractor(adapter).run(
        document=document,
        schema=load_knowledge_schema(),
        output_dir=tmp_path / "knowledge",
        source_document="data/parsed/P001/mineru/raw",
    )

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "## Research Objective" in summary
    assert "## Core Innovations" in summary
    assert "## Experimental Results" in summary
    assert "[E00002]" in summary
    assert sum(line.startswith("- ") for line in summary.splitlines()) <= 38
    assert not (tmp_path / "knowledge" / "device_parameters.yaml").exists()
    manifest = yaml.safe_load(result.run_manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "success"
    assert manifest["evidence_count"] == 2
    assert manifest["input_chars"] > 0
    assert manifest["output_chars"] > 0
    assert result.responses_path.is_file()
    assert len(adapter.generate_calls) == 2
