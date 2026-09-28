"""Build evidence-bounded prompts from a Unified Document."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.schema import Document, DocumentElement

from .extractor import ExtractionContext


PROMPTS_ROOT = Path(__file__).with_name("prompts")
PROMPT_FILES = (
    "summary_prompt.md",
    "parameter_prompt.md",
    "mechanism_prompt.md",
)


@dataclass(frozen=True)
class PromptEvidence:
    evidence_id: str
    element_id: str
    element_type: str
    page: int
    source_reference: str
    content: str
    section_id: str = "unsectioned"

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "page": self.page,
            "source_reference": self.source_reference,
            "content": self.content,
            "section_id": self.section_id,
        }


class KnowledgePromptBuilder:
    """Serialize schemas and traceable document elements into one JSON task."""

    def __init__(self, prompts_root: str | Path = PROMPTS_ROOT) -> None:
        self.prompts_root = Path(prompts_root)

    @staticmethod
    def evidence_from_document(document: Document) -> list[PromptEvidence]:
        evidence: list[PromptEvidence] = []
        sections = sorted(
            document.sections,
            key=lambda item: (item.page_number or 0, item.id),
        )

        def section_for(element: DocumentElement) -> str:
            candidates = [
                section for section in sections
                if section.page_number is not None
                and element.page_number is not None
                and section.page_number <= element.page_number
            ]
            return candidates[-1].id if candidates else "unsectioned"

        groups: tuple[list[DocumentElement], ...] = (
            sections,
            document.text_blocks,
            document.figures,
            document.tables,
            document.equations,
        )
        for group in groups:
            for element in group:
                if not isinstance(element.page_number, int) or element.page_number < 1:
                    continue
                evidence.append(PromptEvidence(
                    evidence_id=f"E{len(evidence) + 1:05d}",
                    element_id=element.id,
                    element_type=type(element).__name__,
                    page=element.page_number,
                    source_reference=element.source_reference,
                    content=element.content,
                    section_id=(
                        element.id if type(element).__name__ == "Section"
                        else section_for(element)
                    ),
                ))
        return evidence

    def build(
        self,
        context: ExtractionContext,
        evidence: list[PromptEvidence],
    ) -> str:
        contracts = "\n\n".join(
            (self.prompts_root / name).read_text(encoding="utf-8").strip()
            for name in PROMPT_FILES
        )
        task = {
            "paper_id": context.paper_id,
            "metadata": dict(context.metadata),
            "core_schema": context.schema.core,
            "domain_extension": context.schema.domain,
            "evidence": [item.as_dict() for item in evidence],
            "required_response": {
                "core": {
                    "paper_identity": "mapping",
                    "research_problem": "list",
                    "methodology": "list",
                    "results": "list",
                    "innovation": "list",
                    "limitations": "list",
                },
                "domain": {"fields": "mapping"},
                "summary": "Markdown string",
                "key_points": "Markdown string",
            },
        }
        return (
            f"{contracts}\n\n"
            "Return exactly one JSON object and no Markdown code fence. "
            "Every populated claim or domain value must cite evidence_refs "
            "from the supplied evidence IDs. Do not reproduce the evidence_index; "
            "the pipeline constructs it deterministically.\n\n"
            f"Extraction task:\n{json.dumps(task, ensure_ascii=False)}"
        )
