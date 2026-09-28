"""Bounded Evidence selection, prompting, and LLM extraction for performance."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from src.llm import LLMAdapter
from src.schema import Document

from .material_device_extraction import MaterialDeviceChunker
from .performance_schema import PERFORMANCE_FIELDS, PerformanceSchema
from .prompt_builder import KnowledgePromptBuilder, PromptEvidence


class PerformanceExtractionError(RuntimeError):
    pass


class PerformanceChunkLimitError(PerformanceExtractionError):
    pass


@dataclass(frozen=True)
class PerformanceChunk:
    index: int
    evidence: tuple[PromptEvidence, ...]


@dataclass(frozen=True)
class PreparedPerformanceExtraction:
    selected_evidence: tuple[PromptEvidence, ...]
    chunks: tuple[PerformanceChunk, ...]
    prompts: tuple[str, ...]

    @property
    def max_prompt_chars(self) -> int:
        return max((len(prompt) for prompt in self.prompts), default=0)

    @property
    def total_prompt_chars(self) -> int:
        return sum(map(len, self.prompts))


@dataclass(frozen=True)
class PerformanceLLMResult:
    performance: dict[str, dict[str, Any]]
    response_records: tuple[dict[str, Any], ...]
    output_chars: int


class PerformanceEvidenceSelector:
    _WEIGHTS = {
        "responsivity": 8,
        "detectivity": 8,
        "eqe": 8,
        "external quantum efficiency": 8,
        "response time": 7,
        "rise time": 7,
        "decay time": 7,
        "photocurrent": 7,
        "dark current": 7,
        "on off ratio": 6,
        "on/off ratio": 6,
        "wavelength": 5,
        "spectral response": 7,
        "stability": 6,
        "stable": 4,
        "endurance": 5,
        "cycle": 3,
        "operation time": 5,
        "bias voltage": 5,
        " v": 1,
        "a/w": 7,
        "jones": 7,
        " nm": 2,
    }
    _LOW_PRIORITY_TERMS = (
        "fabrication", "mechanical exfoliation", "photoresist", "lithography",
        "introduction", "background",
    )
    _ELEMENT_TYPES = frozenset({"Section", "TextBlock", "Figure", "Table"})

    @staticmethod
    def normalize(value: str) -> str:
        text = re.sub(r"<[^>]+>", "", value.casefold())
        return re.sub(r"\s+", " ", text)

    def score(self, item: PromptEvidence, section_titles: dict[str, str]) -> int:
        if item.element_type not in self._ELEMENT_TYPES:
            return 0
        content = self.normalize(item.content)
        score = sum(weight * content.count(term) for term, weight in self._WEIGHTS.items())
        score -= 8 * sum(content.count(term) for term in self._LOW_PRIORITY_TERMS)
        section = section_titles.get(item.section_id, "")
        if "introduction" in section:
            score -= 8
        if "experimental" in section and not any(
            term in content for term in self._WEIGHTS if term.strip() not in {"v", "nm"}
        ):
            score -= 5
        if item.element_type == "Figure" and score > 0:
            score += 5
        return score

    def select(self, evidence: Iterable[PromptEvidence]) -> list[PromptEvidence]:
        items = list(evidence)
        section_titles = {
            item.element_id: self.normalize(item.content)
            for item in items if item.element_type == "Section"
        }
        scored = [
            (self.score(item, section_titles), position, item)
            for position, item in enumerate(items)
        ]
        selected = [entry for entry in scored if entry[0] >= 7]
        # A deterministic cap is a safety boundary, not a paper-specific rule.
        if len(selected) > 30:
            selected = sorted(selected, key=lambda entry: (-entry[0], entry[1]))[:30]
            selected.sort(key=lambda entry: entry[1])
        return [entry[2] for entry in selected]


class PerformancePromptBuilder:
    def __init__(self, *, max_prompt_chars: int = 18_000) -> None:
        self.max_prompt_chars = max_prompt_chars

    def build(
        self, *, paper_id: str, schema: PerformanceSchema, chunk: PerformanceChunk
    ) -> str:
        task = {
            "paper_id": paper_id,
            "task": "performance_only",
            "chunk_index": chunk.index,
            "performance_schema": schema.groups,
            "observation_contract": schema.observation_contract,
            "required_response": schema.new_performance(),
            "evidence": [item.as_dict() for item in chunk.evidence],
        }
        prompt = (
            "# Performance Extraction Contract\n\n"
            "Extract only explicitly reported performance observations from the "
            "supplied Evidence. Never infer, calculate, convert, correct, or use "
            "outside knowledge. Unknown fields must be null. Every non-null field "
            "must be an object or list of objects containing value, unit, evidence_id, "
            "page, and source_type. Numeric values require the authors' unit. Copy page "
            "and source_type from the cited Evidence exactly. Use only Evidence IDs in "
            "this chunk. Return only the four requested performance groups; do not "
            "return material, device, fabrication, mechanism, comparison, or summary. "
            "Return exactly one JSON object without a Markdown fence.\n\n"
            f"Extraction task:\n{json.dumps(task, ensure_ascii=False)}"
        )
        if len(prompt) > self.max_prompt_chars:
            raise ValueError(
                f"performance prompt exceeds {self.max_prompt_chars} characters: {len(prompt)}"
            )
        return prompt


class PerformanceResponseParser:
    @staticmethod
    def parse(response: str) -> dict[str, dict[str, Any]]:
        text = response.strip()
        if text.startswith("```") and text.endswith("```"):
            text = "\n".join(text.splitlines()[1:-1]).strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise PerformanceExtractionError("performance response is not valid JSON") from error
        if isinstance(payload, dict) and isinstance(payload.get("performance"), dict):
            payload = payload["performance"]
        if not isinstance(payload, dict):
            raise PerformanceExtractionError("performance response must be an object")
        unknown_groups = set(payload) - set(PERFORMANCE_FIELDS)
        if unknown_groups:
            raise PerformanceExtractionError(
                f"performance response contains forbidden groups: {sorted(unknown_groups)}"
            )
        parsed: dict[str, dict[str, Any]] = {}
        for group, fields in PERFORMANCE_FIELDS.items():
            value = payload.get(group, {})
            if not isinstance(value, dict):
                raise PerformanceExtractionError(f"response.{group} must be an object")
            unknown = set(value) - set(fields)
            if unknown:
                raise PerformanceExtractionError(
                    f"response.{group} contains unknown fields: {sorted(unknown)}"
                )
            parsed[group] = {field: value.get(field) for field in fields}
        return parsed


class PerformanceExtractor:
    def __init__(
        self,
        llm: LLMAdapter,
        *,
        selector: PerformanceEvidenceSelector | None = None,
        prompt_builder: PerformancePromptBuilder | None = None,
        max_chunks: int = 8,
        max_content_chars: int = 12_000,
    ) -> None:
        self.llm = llm
        self.selector = selector or PerformanceEvidenceSelector()
        self.prompt_builder = prompt_builder or PerformancePromptBuilder()
        self.max_chunks = max_chunks
        self._chunker = MaterialDeviceChunker(max_content_chars=max_content_chars)
        self._evidence_builder = KnowledgePromptBuilder()

    def prepare(
        self, *, document: Document, schema: PerformanceSchema
    ) -> PreparedPerformanceExtraction:
        if document.document_id != "P001":
            raise ValueError("B2 extraction is restricted to P001")
        selected = self.selector.select(
            self._evidence_builder.evidence_from_document(document)
        )
        raw_chunks = self._chunker.chunk(selected)
        chunks = tuple(
            PerformanceChunk(index, chunk.evidence)
            for index, chunk in enumerate(raw_chunks, start=1)
        )
        prompts = tuple(
            self.prompt_builder.build(paper_id="P001", schema=schema, chunk=chunk)
            for chunk in chunks
        )
        prepared = PreparedPerformanceExtraction(tuple(selected), chunks, prompts)
        if len(chunks) > self.max_chunks:
            raise PerformanceChunkLimitError(
                f"filtered evidence requires {len(chunks)} chunks; limit is "
                f"{self.max_chunks}; no API call was made"
            )
        return prepared

    def extract(
        self,
        *,
        schema: PerformanceSchema,
        prepared: PreparedPerformanceExtraction,
        response_callback: Callable[[list[dict[str, Any]]], None] | None = None,
    ) -> PerformanceLLMResult:
        responses: list[dict[str, dict[str, Any]]] = []
        records: list[dict[str, Any]] = []
        output_chars = 0
        for index, prompt in enumerate(prepared.prompts, start=1):
            raw = self.llm.generate(prompt)
            output_chars += len(raw)
            responses.append(PerformanceResponseParser.parse(raw))
            records.append({"call_index": index, "response": raw})
            if response_callback:
                response_callback(records)
        return PerformanceLLMResult(
            self._merge(schema, responses), tuple(records), output_chars
        )

    @staticmethod
    def _merge(
        schema: PerformanceSchema,
        responses: list[dict[str, dict[str, Any]]],
    ) -> dict[str, dict[str, Any]]:
        performance = schema.new_performance()
        for group, fields in PERFORMANCE_FIELDS.items():
            for field in fields:
                observations: list[dict[str, Any]] = []
                seen: set[str] = set()
                for response in responses:
                    value = response[group][field]
                    candidates = value if isinstance(value, list) else [value]
                    for candidate in candidates:
                        if candidate is None:
                            continue
                        if not isinstance(candidate, dict):
                            raise PerformanceExtractionError(
                                f"response.{group}.{field} must be null, object, or list"
                            )
                        key = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
                        if key not in seen:
                            seen.add(key)
                            observations.append(candidate)
                if len(observations) == 1:
                    performance[group][field] = observations[0]
                elif observations:
                    performance[group][field] = observations
        return performance
