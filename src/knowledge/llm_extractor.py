"""LLM-backed extraction that produces validator-compatible drafts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from src.llm import LLMAdapter

from .extractor import ExtractionContext, KnowledgeDraft, KnowledgeExtractor
from .prompt_builder import KnowledgePromptBuilder, PromptEvidence
from .schema import CORE_FIELDS


class KnowledgeResponseError(ValueError):
    """Raised when an LLM response cannot be converted into a draft."""


class LLMKnowledgeExtractor(KnowledgeExtractor):
    def __init__(
        self,
        llm: LLMAdapter,
        *,
        prompt_builder: KnowledgePromptBuilder | None = None,
    ) -> None:
        super().__init__(llm)
        self.prompt_builder = prompt_builder or KnowledgePromptBuilder()

    def extract(self, context: ExtractionContext) -> KnowledgeDraft:
        evidence = self.prompt_builder.evidence_from_document(context.document)
        response = self.generate(self.prompt_builder.build(context, evidence))
        payload = self._load_response(response)
        core = self._build_core(context, payload, evidence)
        domain = self._build_domain(context, payload)
        summary = payload.get("summary")
        key_points = payload.get("key_points")
        if not isinstance(summary, str) or not summary.strip():
            raise KnowledgeResponseError("response.summary must be a non-empty string")
        if not isinstance(key_points, str) or not key_points.strip():
            raise KnowledgeResponseError("response.key_points must be a non-empty string")
        return KnowledgeDraft(
            paper_id=context.paper_id,
            core=core,
            domain=domain,
            summary=summary,
            key_points=key_points,
        )

    @staticmethod
    def _load_response(response: str) -> dict[str, Any]:
        text = response.strip()
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]).strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise KnowledgeResponseError("LLM response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise KnowledgeResponseError("LLM response must be a JSON object")
        return payload

    def _build_core(
        self,
        context: ExtractionContext,
        payload: Mapping[str, Any],
        evidence: list[PromptEvidence],
    ) -> dict[str, Any]:
        proposed = payload.get("core")
        if not isinstance(proposed, Mapping):
            raise KnowledgeResponseError("response.core must be an object")
        core = context.schema.new_core()
        for field in CORE_FIELDS:
            if field in proposed and field != "evidence_traceability":
                core[field] = proposed[field]

        identity = core.get("paper_identity")
        if not isinstance(identity, dict):
            identity = {}
        identity["paper_id"] = context.paper_id
        core["paper_identity"] = identity

        referenced = self._collect_evidence_refs({"core": core, "domain": payload.get("domain")})
        core["evidence_traceability"] = {
            "source_document": context.source_document,
            "evidence_index": [
                {
                    "evidence_id": item.evidence_id,
                    "element_id": item.element_id,
                    "element_type": item.element_type,
                    "page": item.page,
                    "source_reference": item.source_reference,
                    "quote": item.content,
                }
                for item in evidence
                if item.evidence_id in referenced
            ],
        }
        return core

    @staticmethod
    def _build_domain(
        context: ExtractionContext, payload: Mapping[str, Any]
    ) -> dict[str, Any]:
        proposed = payload.get("domain")
        if not isinstance(proposed, Mapping):
            raise KnowledgeResponseError("response.domain must be an object")
        fields = proposed.get("fields")
        if not isinstance(fields, Mapping):
            raise KnowledgeResponseError("response.domain.fields must be an object")
        return {
            "schema_version": "1.0",
            "paper_id": context.paper_id,
            "domain_id": context.schema.domain_id,
            "schema_path": (
                context.schema.domain_path.as_posix()
                if context.schema.domain_path is not None else None
            ),
            "fields": dict(fields),
        }

    @staticmethod
    def _collect_evidence_refs(value: Any) -> set[str]:
        references: set[str] = set()
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if key == "evidence_refs" and isinstance(nested, list):
                    references.update(item for item in nested if isinstance(item, str))
                else:
                    references.update(LLMKnowledgeExtractor._collect_evidence_refs(nested))
        elif isinstance(value, list):
            for nested in value:
                references.update(LLMKnowledgeExtractor._collect_evidence_refs(nested))
        return references
