"""Model-neutral parameter extraction contracts and JSON implementation."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.llm import LLMAdapter

from .parameter_schema import ParameterSchema


PARAMETER_PROMPT = Path(__file__).with_name("prompts") / "parameter_prompt.md"


@dataclass(frozen=True)
class ParameterExtractionContext:
    paper_id: str
    schema: ParameterSchema
    evidence: tuple[Mapping[str, Any], ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParameterDraft:
    schema_version: str
    paper_id: str
    domain_id: str
    parameters: dict[str, dict[str, Any]]
    evidence_index: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "paper_id": self.paper_id,
            "domain_id": self.domain_id,
            "parameters": self.parameters,
            "evidence_index": self.evidence_index,
        }


class ParameterResponseError(ValueError):
    """Raised when a model response is not a parameter draft."""


class ParameterExtractor(ABC):
    def __init__(self, llm: LLMAdapter) -> None:
        self.llm = llm

    @abstractmethod
    def extract(self, context: ParameterExtractionContext) -> ParameterDraft:
        raise NotImplementedError


class ParameterPromptBuilder:
    def __init__(self, prompt_path: str | Path = PARAMETER_PROMPT) -> None:
        self.prompt_path = Path(prompt_path)

    def build(self, context: ParameterExtractionContext) -> str:
        contract = self.prompt_path.read_text(encoding="utf-8").strip()
        payload = {
            "paper_id": context.paper_id,
            "metadata": dict(context.metadata),
            "parameter_schema": {
                "schema_version": context.schema.schema_version,
                "domain_id": context.schema.domain_id,
                "sections": context.schema.sections,
            },
            "evidence": [dict(item) for item in context.evidence],
            "required_response": {
                "schema_version": context.schema.schema_version,
                "paper_id": context.paper_id,
                "domain_id": context.schema.domain_id,
                "parameters": context.schema.new_parameters(),
                "evidence_index": "list of referenced supplied Evidence records",
            },
        }
        return (
            f"{contract}\n\nReturn exactly one JSON object and no Markdown code fence.\n\n"
            f"Parameter extraction task:\n{json.dumps(payload, ensure_ascii=False)}"
        )


class LLMParameterExtractor(ParameterExtractor):
    def __init__(
        self,
        llm: LLMAdapter,
        *,
        prompt_builder: ParameterPromptBuilder | None = None,
    ) -> None:
        super().__init__(llm)
        self.prompt_builder = prompt_builder or ParameterPromptBuilder()

    def extract(self, context: ParameterExtractionContext) -> ParameterDraft:
        response = self.llm.generate(self.prompt_builder.build(context)).strip()
        if response.startswith("```") and response.endswith("```"):
            response = "\n".join(response.splitlines()[1:-1]).strip()
        try:
            payload = json.loads(response)
        except json.JSONDecodeError as error:
            raise ParameterResponseError("parameter response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise ParameterResponseError("parameter response must be a JSON object")
        parameters = payload.get("parameters")
        evidence_index = payload.get("evidence_index")
        if not isinstance(parameters, dict):
            raise ParameterResponseError("parameter response.parameters must be an object")
        if not isinstance(evidence_index, list):
            raise ParameterResponseError("parameter response.evidence_index must be a list")
        return ParameterDraft(
            schema_version=str(payload.get("schema_version", "")),
            paper_id=str(payload.get("paper_id", "")),
            domain_id=str(payload.get("domain_id", "")),
            parameters=parameters,
            evidence_index=evidence_index,
        )
