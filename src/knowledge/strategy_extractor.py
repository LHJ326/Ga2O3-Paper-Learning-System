"""Chunked, task-specific knowledge extraction for long papers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.llm import LLMAdapter

from .extractor import ExtractionContext, KnowledgeDraft, KnowledgeExtractor
from .llm_extractor import KnowledgeResponseError, LLMKnowledgeExtractor
from .prompt_builder import KnowledgePromptBuilder, PROMPTS_ROOT, PromptEvidence
from .strategy import EvidenceChunk, EvidenceChunker, ExtractionTask, PromptStrategy, PromptStrategyRegistry


class StrategyPromptBuilder:
    def __init__(
        self,
        *,
        prompts_root: str | Path = PROMPTS_ROOT,
        max_prompt_chars: int = 24_000,
    ) -> None:
        if max_prompt_chars < 1:
            raise ValueError("max_prompt_chars must be positive")
        self.prompts_root = Path(prompts_root)
        self.max_prompt_chars = max_prompt_chars

    def build(
        self,
        context: ExtractionContext,
        strategy: PromptStrategy,
        chunk: EvidenceChunk,
    ) -> str:
        contract = (self.prompts_root / strategy.prompt_file).read_text(encoding="utf-8").strip()
        task = {
            "paper_id": context.paper_id,
            "task": strategy.task.value,
            "section_id": chunk.section_id,
            "element_type": chunk.element_type,
            "chunk_index": chunk.index,
            "domain_id": context.schema.domain_id,
            "domain_fields": (
                context.schema.domain_fields
                if strategy.task is ExtractionTask.PARAMETER
                else {"mechanism": context.schema.domain_fields.get("mechanism", {})}
                if strategy.task is ExtractionTask.MECHANISM
                else {}
            ),
            "required_response": strategy.response_shape,
            "evidence": [item.as_dict() for item in chunk.evidence],
        }
        prompt = (
            f"{contract}\n\n"
            "Process only this evidence chunk. Return exactly one JSON object and no "
            "Markdown code fence. Cite only supplied evidence IDs. Empty or unsupported "
            "fields must be returned as empty values.\n\n"
            f"Extraction task:\n{json.dumps(task, ensure_ascii=False)}"
        )
        if len(prompt) > self.max_prompt_chars:
            raise ValueError(
                f"strategy prompt exceeds {self.max_prompt_chars} characters: {len(prompt)}"
            )
        return prompt


class StrategyKnowledgeExtractor(KnowledgeExtractor):
    """Run bounded prompts and merge task results without a whole-paper call."""

    def __init__(
        self,
        llm: LLMAdapter,
        *,
        registry: PromptStrategyRegistry | None = None,
        chunker: EvidenceChunker | None = None,
        prompt_builder: StrategyPromptBuilder | None = None,
    ) -> None:
        super().__init__(llm)
        self.registry = registry or PromptStrategyRegistry()
        self.chunker = chunker or EvidenceChunker()
        self.prompt_builder = prompt_builder or StrategyPromptBuilder()
        self.evidence_builder = KnowledgePromptBuilder()

    def extract(self, context: ExtractionContext) -> KnowledgeDraft:
        evidence = self.evidence_builder.evidence_from_document(context.document)
        responses: dict[ExtractionTask, list[dict[str, Any]]] = {
            task: [] for task in ExtractionTask
        }
        for strategy in self.registry.all():
            for chunk in self.chunker.chunk(evidence, strategy):
                prompt = self.prompt_builder.build(context, strategy, chunk)
                responses[strategy.task].append(
                    LLMKnowledgeExtractor._load_response(self.generate(prompt))
                )

        core = self._merge_core(context, responses[ExtractionTask.SUMMARY])
        domain = self._merge_domain(
            context,
            responses[ExtractionTask.PARAMETER],
            responses[ExtractionTask.MECHANISM],
        )
        references = LLMKnowledgeExtractor._collect_evidence_refs(
            {"core": core, "domain": domain}
        )
        core["evidence_traceability"] = {
            "source_document": context.source_document,
            "evidence_index": [
                self._evidence_record(item)
                for item in evidence if item.evidence_id in references
            ],
        }
        summary, key_points = self._merge_views(responses[ExtractionTask.SUMMARY])
        return KnowledgeDraft(context.paper_id, core, domain, summary, key_points)

    @staticmethod
    def _merge_core(
        context: ExtractionContext, responses: list[dict[str, Any]]
    ) -> dict[str, Any]:
        core = context.schema.new_core()
        identity = dict(core.get("paper_identity") or {})
        identity["paper_id"] = context.paper_id
        if isinstance(context.metadata.get("title"), str):
            identity["title"] = context.metadata["title"]
        core["paper_identity"] = identity
        for field in ("research_problem", "methodology", "results", "innovation", "limitations"):
            merged: list[Any] = []
            for response in responses:
                value = response.get(field, [])
                if not isinstance(value, list):
                    raise KnowledgeResponseError(f"summary response.{field} must be a list")
                merged.extend(value)
            core[field] = merged
        return core

    @staticmethod
    def _merge_domain(
        context: ExtractionContext,
        parameter_responses: list[dict[str, Any]],
        mechanism_responses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        for response in parameter_responses:
            proposed = response.get("fields", {})
            if not isinstance(proposed, Mapping):
                raise KnowledgeResponseError("parameter response.fields must be an object")
            for name, value in proposed.items():
                if isinstance(value, list):
                    fields.setdefault(name, []).extend(value)
                elif isinstance(value, Mapping):
                    fields.setdefault(name, {}).update(value)
                elif value is not None:
                    fields[name] = value
        mechanisms: list[Any] = []
        for response in mechanism_responses:
            value = response.get("mechanism", [])
            if not isinstance(value, list):
                raise KnowledgeResponseError("mechanism response.mechanism must be a list")
            mechanisms.extend(value)
        if mechanisms:
            fields["mechanism"] = mechanisms
        return {
            "schema_version": "1.0",
            "paper_id": context.paper_id,
            "domain_id": context.schema.domain_id,
            "schema_path": (
                context.schema.domain_path.as_posix()
                if context.schema.domain_path is not None else None
            ),
            "fields": fields,
        }

    @staticmethod
    def _merge_views(responses: list[dict[str, Any]]) -> tuple[str, str]:
        summaries: list[str] = []
        points: list[str] = []
        for response in responses:
            summary = response.get("summary")
            if isinstance(summary, str) and summary.strip():
                summaries.append(summary.strip())
            key_points = response.get("key_points", [])
            if isinstance(key_points, str):
                points.append(key_points.strip())
            elif isinstance(key_points, list):
                points.extend(str(point).strip() for point in key_points if str(point).strip())
            else:
                raise KnowledgeResponseError("summary response.key_points must be a string or list")
        return (
            "# Summary\n\n" + "\n\n".join(summaries),
            "# Key Points\n\n" + "\n".join(f"- {point}" for point in points),
        )

    @staticmethod
    def _evidence_record(item: PromptEvidence) -> dict[str, Any]:
        return {
            "evidence_id": item.evidence_id,
            "element_id": item.element_id,
            "element_type": item.element_type,
            "page": item.page,
            "source_reference": item.source_reference,
            "quote": item.content,
        }
