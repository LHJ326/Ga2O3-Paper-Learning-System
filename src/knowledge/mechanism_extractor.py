"""Task-specific Evidence selection and LLM extraction for mechanisms."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from src.llm import LLMAdapter
from src.schema import Document

from .material_device_extraction import MaterialDeviceChunker
from .mechanism_schema import MECHANISM_FIELDS, MechanismSchema
from .prompt_builder import KnowledgePromptBuilder, PromptEvidence


class MechanismExtractionError(RuntimeError):
    pass


class MechanismChunkLimitError(MechanismExtractionError):
    pass


@dataclass(frozen=True)
class MechanismChunk:
    index: int
    evidence: tuple[PromptEvidence, ...]


@dataclass(frozen=True)
class PreparedMechanismExtraction:
    selected_evidence: tuple[PromptEvidence, ...]
    chunks: tuple[MechanismChunk, ...]
    prompts: tuple[str, ...]

    @property
    def max_prompt_chars(self) -> int:
        return max((len(prompt) for prompt in self.prompts), default=0)

    @property
    def total_prompt_chars(self) -> int:
        return sum(map(len, self.prompts))

    @property
    def estimated_input_tokens(self) -> int:
        # Official guidance: one English character is approximately 0.3 token.
        return round(self.total_prompt_chars * 0.3)

    @property
    def estimated_input_cost_usd(self) -> tuple[float, float]:
        tokens_million = self.estimated_input_tokens / 1_000_000
        return tokens_million * 0.15, tokens_million * 0.30


@dataclass(frozen=True)
class MechanismLLMResult:
    mechanisms: dict[str, Any]
    response_records: tuple[dict[str, Any], ...]
    output_chars: int


class MechanismEvidenceSelector:
    _WEIGHTS = {
        "mechanism": 6, "photogeneration": 8, "photo-generated": 7,
        "photogenerated": 7, "carrier": 4, "transport": 5, "transfer": 4,
        "tunnel": 6, "recombination": 8, "trap": 6, "defect": 6,
        "vacancy": 7, "interface": 5, "band alignment": 8,
        "energy band": 6, "barrier": 5, "gain": 5, "depletion": 5,
        "adsorption": 5, "desorption": 5, "working principle": 8,
        "operating principle": 8, "programming": 3, "erasing": 3,
    }
    _LOW_PRIORITY = (
        "responsivity", "detectivity", "response time", "photocurrent",
        "fabrication", "mechanical exfoliation", "photoresist", "lithography",
    )
    _ELEMENT_TYPES = frozenset({"Section", "TextBlock", "Figure", "Equation"})

    @staticmethod
    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value.casefold()))

    def score(self, item: PromptEvidence, section_titles: dict[str, str]) -> int:
        if item.element_type not in self._ELEMENT_TYPES:
            return 0
        content = self.normalize(item.content)
        score = sum(weight * content.count(term) for term, weight in self._WEIGHTS.items())
        score -= 7 * sum(content.count(term) for term in self._LOW_PRIORITY)
        if "introduction" in section_titles.get(item.section_id, ""):
            score -= 5
        if item.element_type == "Figure" and score > 0:
            score += 4
        if item.element_type == "Equation" and not content.strip():
            return 0
        return score

    def select(self, evidence: Iterable[PromptEvidence]) -> list[PromptEvidence]:
        items = list(evidence)
        titles = {
            item.element_id: self.normalize(item.content)
            for item in items if item.element_type == "Section"
        }
        scored = [(self.score(item, titles), index, item) for index, item in enumerate(items)]
        selected = [entry for entry in scored if entry[0] >= 6]
        if len(selected) > 30:
            selected = sorted(selected, key=lambda entry: (-entry[0], entry[1]))[:30]
            selected.sort(key=lambda entry: entry[1])
        return [entry[2] for entry in selected]


class MechanismPromptBuilder:
    def __init__(self, *, max_prompt_chars: int = 18_000) -> None:
        self.max_prompt_chars = max_prompt_chars

    def build(self, *, paper_id: str, schema: MechanismSchema, chunk: MechanismChunk) -> str:
        task = {
            "paper_id": paper_id,
            "task": "mechanism_only",
            "chunk_index": chunk.index,
            "mechanism_schema": schema.fields,
            "observation_contract": schema.observation_contract,
            "required_response": schema.new_mechanisms(),
            "evidence": [item.as_dict() for item in chunk.evidence],
        }
        prompt = (
            "# Mechanism Extraction Contract\n\n"
            "Extract only mechanisms explicitly stated in the supplied Evidence. Never "
            "infer a mechanism from general domain knowledge, calculate missing facts, "
            "or correct the authors. Unknown fields must be null. Every non-null field "
            "must be an object or list of objects with value, evidence_id, page, "
            "source_type, confidence (0 to 1), and review_status (unreviewed or "
            "review_required). Copy page and source_type exactly from the cited Evidence. "
            "Use only Evidence IDs supplied in this chunk. Do not return summary, "
            "material, device, fabrication, performance, or comparison fields. Return "
            "exactly one JSON object without a Markdown fence.\n\n"
            f"Extraction task:\n{json.dumps(task, ensure_ascii=False)}"
        )
        if len(prompt) > self.max_prompt_chars:
            raise ValueError(
                f"mechanism prompt exceeds {self.max_prompt_chars} characters: {len(prompt)}"
            )
        return prompt


class MechanismResponseParser:
    @staticmethod
    def parse(response: str) -> dict[str, Any]:
        text = response.strip()
        if text.startswith("```") and text.endswith("```"):
            text = "\n".join(text.splitlines()[1:-1]).strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise MechanismExtractionError("mechanism response is not valid JSON") from error
        if isinstance(payload, dict) and isinstance(payload.get("mechanisms"), dict):
            payload = payload["mechanisms"]
        if not isinstance(payload, dict):
            raise MechanismExtractionError("mechanism response must be an object")
        unknown = set(payload) - set(MECHANISM_FIELDS)
        if unknown:
            raise MechanismExtractionError(f"unknown mechanism fields: {sorted(unknown)}")
        return {field: payload.get(field) for field in MECHANISM_FIELDS}


class MechanismExtractor:
    def __init__(
        self, llm: LLMAdapter, *, selector: MechanismEvidenceSelector | None = None,
        prompt_builder: MechanismPromptBuilder | None = None, max_chunks: int = 8,
        max_content_chars: int = 12_000,
    ) -> None:
        self.llm = llm
        self.selector = selector or MechanismEvidenceSelector()
        self.prompt_builder = prompt_builder or MechanismPromptBuilder()
        self.max_chunks = max_chunks
        self._chunker = MaterialDeviceChunker(max_content_chars=max_content_chars)
        self._evidence_builder = KnowledgePromptBuilder()

    def prepare(self, *, document: Document, schema: MechanismSchema) -> PreparedMechanismExtraction:
        if document.document_id != "P001":
            raise ValueError("B3 extraction is restricted to P001")
        selected = self.selector.select(self._evidence_builder.evidence_from_document(document))
        chunks = tuple(
            MechanismChunk(index, chunk.evidence)
            for index, chunk in enumerate(self._chunker.chunk(selected), 1)
        )
        prompts = tuple(
            self.prompt_builder.build(paper_id="P001", schema=schema, chunk=chunk)
            for chunk in chunks
        )
        prepared = PreparedMechanismExtraction(tuple(selected), chunks, prompts)
        if len(chunks) > self.max_chunks:
            raise MechanismChunkLimitError(
                f"filtered evidence requires {len(chunks)} chunks; limit is {self.max_chunks}; "
                "no API call was made"
            )
        return prepared

    def extract(
        self, *, schema: MechanismSchema, prepared: PreparedMechanismExtraction,
        response_callback: Callable[[list[dict[str, Any]]], None] | None = None,
    ) -> MechanismLLMResult:
        responses: list[dict[str, Any]] = []
        records: list[dict[str, Any]] = []
        output_chars = 0
        for index, prompt in enumerate(prepared.prompts, 1):
            raw = self.llm.generate(prompt)
            output_chars += len(raw)
            responses.append(MechanismResponseParser.parse(raw))
            records.append({"call_index": index, "response": raw})
            if response_callback:
                response_callback(records)
        return MechanismLLMResult(self._merge(schema, responses), tuple(records), output_chars)

    @staticmethod
    def _merge(schema: MechanismSchema, responses: list[dict[str, Any]]) -> dict[str, Any]:
        result = schema.new_mechanisms()
        for field in MECHANISM_FIELDS:
            values: list[dict[str, Any]] = []
            seen: set[str] = set()
            for response in responses:
                raw = response[field]
                candidates = raw if isinstance(raw, list) else [raw]
                for candidate in candidates:
                    if candidate is None:
                        continue
                    if not isinstance(candidate, dict):
                        raise MechanismExtractionError(
                            f"response.{field} must be null, object, or list"
                        )
                    key = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
                    if key not in seen:
                        seen.add(key)
                        values.append(candidate)
            result[field] = values[0] if len(values) == 1 else values or None
        return result
