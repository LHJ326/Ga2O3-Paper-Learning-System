import json
from pathlib import Path

import yaml

from src.knowledge import (
    QualityReportWriter,
    SummaryKnowledgeValidator,
    SummaryQualityAnalyzer,
    check_parameter_ranges,
    check_summary_structure,
)


COMPLETE_SUMMARY = """# Summary

## Research Objective
- Build a detector [E00001].

## Material/System
- Beta-Ga2O3 system [E00001].

## Device Structure
- Metal-semiconductor-metal structure [E00001].

## Mechanism
- Photoconductive gain [E00001].

## Performance
- Responsivity was measured [E00001].

## Innovation
- A new architecture was demonstrated [E00001].

## Limitation
- Response speed remains limited [E00001].
"""


def write_inputs(knowledge: Path, summary: str = COMPLETE_SUMMARY) -> None:
    knowledge.mkdir(parents=True)
    (knowledge / "summary.md").write_text(summary, encoding="utf-8")
    task = {
        "evidence": [{
            "evidence_id": "E00001",
            "element_id": "P100-text-1",
            "element_type": "TextBlock",
            "page": 2,
            "source_reference": {"source_file": "document.json", "page": 2},
            "content": "Evidence text",
        }]
    }
    prompt_record = {
        "call_index": 1,
        "prompt": "Contract\nExtraction task:\n" + json.dumps(task),
    }
    (knowledge / "summary_extraction_prompts.json").write_text(
        json.dumps([prompt_record]), encoding="utf-8"
    )
    (knowledge / "summary_extraction_responses.json").write_text(
        json.dumps([{"call_index": 1, "response": "{}"}]), encoding="utf-8"
    )


def test_summary_section_check_reports_completeness_and_missing_items() -> None:
    complete = check_summary_structure(COMPLETE_SUMMARY)
    assert complete.score == 100.0
    assert complete.missing_sections == ()

    incomplete = check_summary_structure("## Research Objective\n\n## Performance")
    assert incomplete.score == round(200 / 7, 2)
    assert "Mechanism" in incomplete.missing_sections


def test_evidence_check_requires_id_page_and_source_locator(tmp_path: Path) -> None:
    knowledge = tmp_path / "papers" / "P100" / "knowledge"
    write_inputs(
        knowledge,
        COMPLETE_SUMMARY + "\n- Unsupported conclusion without evidence.\n",
    )
    report = SummaryQualityAnalyzer().analyze(
        paper_id="P100", knowledge_path=knowledge
    )
    assert report.evidence.total_claims == 8
    assert report.evidence.supported_claims == 7
    assert report.evidence.unsupported_claims == 1
    assert report.evidence.coverage == 87.5


def test_parameter_check_generates_warnings_without_modifying_text() -> None:
    summary = (
        "Wavelength was 99999 nm. Responsivity was 2e9 A/W. "
        "Detectivity was 3e21 Jones. Response time was 2e6 s. "
        "The on/off ratio was 1e18."
    )
    result = check_parameter_ranges(summary)
    assert result.status == "warning"
    assert {warning.parameter for warning in result.warnings} == {
        "wavelength", "responsivity", "detectivity", "response time", "on/off ratio"
    }
    assert "99999 nm" in summary


def test_report_writer_outputs_required_yaml_and_json(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    knowledge = papers / "P100" / "knowledge"
    write_inputs(knowledge)
    validator = SummaryKnowledgeValidator(papers_root=papers)
    report, paths = validator.validate_and_write("P100")

    quality = yaml.safe_load(paths["quality_report"].read_text(encoding="utf-8"))
    log = json.loads(paths["validation_log"].read_text(encoding="utf-8"))
    assert quality["paper_id"] == "P100"
    assert quality["structure_score"] == 100.0
    assert quality["evidence_score"] == 100.0
    assert quality["parameter_check"]["status"] == "pass"
    assert quality["overall_status"] == "pass"
    assert quality["review_required"] is False
    assert log["validation_schema_version"] == "1.0"
    assert report.overall_status == "pass"
