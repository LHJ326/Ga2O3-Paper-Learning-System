"""Bounded, auditable Material and Device extraction for P001."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

import yaml

from src.llm import LLMAdapter
from src.schema import Document

from .parameter_extractor import ParameterDraft, ParameterResponseError
from .parameter_schema import ParameterSchema, REQUIRED_PARAMETER_FIELDS
from .parameter_writer import ParameterWriter
from .prompt_builder import KnowledgePromptBuilder, PromptEvidence
from .material_device_schema import MaterialDeviceSchema, load_material_device_schema
from .material_device_validator import MaterialDeviceValidator


ALLOWED_SECTIONS = ("material", "device")
ALLOWED_FIELDS = {
    section: REQUIRED_PARAMETER_FIELDS[section] for section in ALLOWED_SECTIONS
}


class MaterialDeviceExtractionError(RuntimeError):
    """Raised before writing when a B1 response violates its narrow contract."""


class ChunkLimitError(MaterialDeviceExtractionError):
    """Raised before API use when filtered evidence still needs too many chunks."""


@dataclass(frozen=True)
class MaterialDeviceChunk:
    index: int
    evidence: tuple[PromptEvidence, ...]


@dataclass(frozen=True)
class PreparedMaterialDeviceExtraction:
    selected_evidence: tuple[PromptEvidence, ...]
    chunks: tuple[MaterialDeviceChunk, ...]
    prompts: tuple[str, ...]

    @property
    def max_prompt_chars(self) -> int:
        return max((len(prompt) for prompt in self.prompts), default=0)

    @property
    def total_prompt_chars(self) -> int:
        return sum(map(len, self.prompts))


@dataclass(frozen=True)
class MaterialDeviceExtractionResult:
    parameters_path: Path
    prompts_path: Path
    responses_path: Path
    run_manifest_path: Path
    api_calls: int
    selected_evidence_count: int
    chunk_count: int
    input_chars: int
    output_chars: int
    extracted_fields: tuple[str, ...]
    null_fields: tuple[str, ...]
    evidence_supported_fields: int
    unsupported_fields: int
    warnings: tuple[str, ...]
    review_required: bool


class MaterialDeviceEvidenceFilter:
    """Select evidence using domain terms without paper-specific IDs or text."""

    _WEIGHTS = {
        "ga2o3": 3,
        "beta-ga2o3": 4,
        "mos2": 4,
        "mlg": 4,
        "graphene": 4,
        "semiconductor": 2,
        "dielectric": 3,
        "heterostructure": 4,
        "doping": 3,
        "dopant": 3,
        "defect": 2,
        "substrate": 3,
        "device": 1,
        "structure": 3,
        "architecture": 3,
        "electrode": 3,
        "gate": 2,
        "floating gate": 5,
        "source": 1,
        "drain": 2,
        "fabrication": 4,
        "fabricated": 4,
        "layer": 1,
        "thickness": 3,
    }
    _ELEMENT_TYPES = frozenset({"Section", "TextBlock", "Figure", "Table"})
    _PERFORMANCE_TERMS = (
        "responsivity",
        "detectivity",
        "response time",
        "photocurrent",
        "performance",
        "stability",
    )
    _PREFERRED_SECTION_TERMS = (
        "material", "fabrication", "device structure", "experimental"
    )
    _LOW_PRIORITY_SECTION_TERMS = (
        "introduction", "discussion", "conclusion"
    )
    _STRUCTURAL_FIGURE_TERMS = (
        "schematic structure",
        "device structure",
        "fabrication",
        "cross section",
        "architecture",
        "electrode",
        "substrate",
        "heterostructure",
        "layer structure",
    )
    _PERFORMANCE_FIGURE_TERMS = (
        "storage performance",
        "electrical performance",
        "physical mechanism",
        "comparison",
        "synapse simulation",
        "neuromorphic computing",
    )

    @classmethod
    def normalize(cls, value: str) -> str:
        text = re.sub(r"<[^>]+>", "", value.casefold())
        text = text.replace("𝛽", "beta").replace("β", "beta")
        return re.sub(r"[^a-z0-9]+", " ", text).strip()

    def score(
        self,
        item: PromptEvidence,
        section_titles: dict[str, str] | None = None,
    ) -> int:
        if item.element_type not in self._ELEMENT_TYPES:
            return 0
        content = self.normalize(item.content)
        score = sum(
            weight * len(re.findall(rf"\b{re.escape(term)}\b", content))
            for term, weight in self._WEIGHTS.items()
        )
        score -= 8 * sum(content.count(term) for term in self._PERFORMANCE_TERMS)

        section_title = (section_titles or {}).get(item.section_id, "")
        if any(term in section_title for term in self._PREFERRED_SECTION_TERMS):
            score += 8
        if any(term in section_title for term in self._LOW_PRIORITY_SECTION_TERMS):
            score -= 6
        if any(term in content for term in ("device fabrication", "fabrication method")):
            score += 10

        if item.element_type == "Figure":
            if not any(term in content for term in self._STRUCTURAL_FIGURE_TERMS):
                return 0
            if any(term in content for term in self._PERFORMANCE_FIGURE_TERMS):
                score -= 30
        return score

    def select(self, evidence: Iterable[PromptEvidence]) -> list[PromptEvidence]:
        items = list(evidence)
        section_titles = {
            item.element_id: self.normalize(item.content)
            for item in items if item.element_type == "Section"
        }
        # A single generic occurrence of "device", "source", or "layer" is not
        # sufficiently specific. Performance-only contexts are deferred to their
        # own extraction phase, while experimental/structure contexts are raised.
        return [
            item for item in items
            if self.score(item, section_titles) >= 10
        ]


class MaterialDeviceChunker:
    """Pack filtered evidence tightly while preserving document order."""

    def __init__(self, *, max_content_chars: int = 12_000) -> None:
        if max_content_chars < 1:
            raise ValueError("max_content_chars must be positive")
        self.max_content_chars = max_content_chars

    def chunk(self, evidence: Iterable[PromptEvidence]) -> list[MaterialDeviceChunk]:
        chunks: list[MaterialDeviceChunk] = []
        current: list[PromptEvidence] = []
        current_size = 0
        for original in evidence:
            for item in self._split_oversized(original):
                size = self._size(item)
                if current and current_size + size > self.max_content_chars:
                    chunks.append(MaterialDeviceChunk(len(chunks) + 1, tuple(current)))
                    current, current_size = [], 0
                current.append(item)
                current_size += size
        if current:
            chunks.append(MaterialDeviceChunk(len(chunks) + 1, tuple(current)))
        return chunks

    def _split_oversized(self, item: PromptEvidence) -> list[PromptEvidence]:
        if self._size(item) <= self.max_content_chars:
            return [item]
        budget = self.max_content_chars - self._size(replace(item, content=""))
        if budget < 1:
            raise ValueError("chunk budget cannot contain Evidence locator metadata")
        return [
            replace(item, content=item.content[start:start + budget])
            for start in range(0, len(item.content), budget)
        ]

    @staticmethod
    def _size(item: PromptEvidence) -> int:
        return len(json.dumps(item.as_dict(), ensure_ascii=False))


class MaterialDevicePromptBuilder:
    """Build a strict Material/Device-only prompt from one bounded chunk."""

    def __init__(self, *, max_prompt_chars: int = 18_000) -> None:
        self.max_prompt_chars = max_prompt_chars

    def build(
        self,
        *,
        paper_id: str,
        schema: ParameterSchema,
        task_schema: MaterialDeviceSchema,
        chunk: MaterialDeviceChunk,
    ) -> str:
        field_schema = task_schema.sections
        empty = {
            section: {field: None for field in ALLOWED_FIELDS[section]}
            for section in ALLOWED_SECTIONS
        }
        task = {
            "paper_id": paper_id,
            "task": "material_device_only",
            "chunk_index": chunk.index,
            "task_schema_version": task_schema.schema_version,
            "task_domain_id": task_schema.domain_id,
            "field_schema": field_schema,
            "required_response": empty,
            "evidence": [item.as_dict() for item in chunk.evidence],
        }
        prompt = (
            "# Material and Device Structure Extraction Contract\n\n"
            "Extract only the requested material and device fields from the supplied "
            "Evidence. Never infer, estimate, calculate, correct the authors, or use "
            "outside/domain knowledge. Return null when this chunk does not explicitly "
            "support a field. Every non-null structured object (and every list item) "
            "must contain a non-empty evidence_refs list using only supplied Evidence "
            "IDs. Preserve the authors' terminology and units. Do not return performance, "
            "mechanism, comparison, or summary fields. Return exactly one JSON object "
            "with top-level material and device mappings and no Markdown fence.\n\n"
            f"Extraction task:\n{json.dumps(task, ensure_ascii=False)}"
        )
        if len(prompt) > self.max_prompt_chars:
            raise ValueError(
                f"material/device prompt exceeds {self.max_prompt_chars} characters: "
                f"{len(prompt)}"
            )
        return prompt


class MaterialDeviceResponseParser:
    """Parse the narrow B1 response and reject expansion into other groups."""

    @staticmethod
    def parse(response: str) -> dict[str, dict[str, Any]]:
        text = response.strip()
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()[1:-1]
            text = "\n".join(lines).strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ParameterResponseError("material/device response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise ParameterResponseError("material/device response must be an object")
        if isinstance(payload.get("parameters"), dict):
            payload = payload["parameters"]
        unknown_sections = set(payload) - set(ALLOWED_SECTIONS)
        if unknown_sections:
            raise ParameterResponseError(
                f"material/device response contains forbidden sections: {sorted(unknown_sections)}"
            )
        parsed: dict[str, dict[str, Any]] = {}
        for section in ALLOWED_SECTIONS:
            value = payload.get(section, {})
            if not isinstance(value, dict):
                raise ParameterResponseError(f"response.{section} must be an object")
            unknown_fields = set(value) - set(ALLOWED_FIELDS[section])
            if unknown_fields:
                raise ParameterResponseError(
                    f"response.{section} contains unknown fields: {sorted(unknown_fields)}"
                )
            parsed[section] = {
                field: value.get(field) for field in ALLOWED_FIELDS[section]
            }
        return parsed


class P001MaterialDeviceExtractor:
    """Perform a bounded real or mocked B1 extraction and persist provenance."""

    def __init__(
        self,
        llm: LLMAdapter,
        *,
        evidence_filter: MaterialDeviceEvidenceFilter | None = None,
        chunker: MaterialDeviceChunker | None = None,
        prompt_builder: MaterialDevicePromptBuilder | None = None,
        task_schema: MaterialDeviceSchema | None = None,
        max_chunks: int = 8,
    ) -> None:
        self.llm = llm
        self.evidence_filter = evidence_filter or MaterialDeviceEvidenceFilter()
        self.chunker = chunker or MaterialDeviceChunker()
        self.prompt_builder = prompt_builder or MaterialDevicePromptBuilder()
        self.task_schema = task_schema or load_material_device_schema()
        self.max_chunks = max_chunks
        self.evidence_builder = KnowledgePromptBuilder()

    def prepare(
        self, *, document: Document, schema: ParameterSchema
    ) -> PreparedMaterialDeviceExtraction:
        if document.document_id != "P001":
            raise ValueError("B1 extraction is restricted to P001")
        selected = self.evidence_filter.select(
            self.evidence_builder.evidence_from_document(document)
        )
        chunks = self.chunker.chunk(selected)
        prompts = tuple(
            self.prompt_builder.build(
                paper_id="P001", schema=schema, task_schema=self.task_schema,
                chunk=chunk,
            )
            for chunk in chunks
        )
        prepared = PreparedMaterialDeviceExtraction(
            tuple(selected), tuple(chunks), prompts
        )
        if len(prepared.chunks) > self.max_chunks:
            raise ChunkLimitError(
                f"filtered evidence requires {len(prepared.chunks)} chunks; "
                f"limit is {self.max_chunks}; no API call was made"
            )
        return prepared

    def run(
        self,
        *,
        document: Document,
        schema: ParameterSchema,
        output_dir: str | Path,
        papers_root: str | Path,
        prepared: PreparedMaterialDeviceExtraction | None = None,
    ) -> MaterialDeviceExtractionResult:
        prepared = prepared or self.prepare(document=document, schema=schema)
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        prompts_path = output / "device_extraction_prompts.jsonl"
        responses_path = output / "device_extraction_responses.jsonl"
        manifest_path = output / "device_extraction_run.yaml"
        prompt_records = [
            {
                "call_index": index,
                "evidence_ids": [item.evidence_id for item in chunk.evidence],
                "prompt": prompt,
            }
            for index, (chunk, prompt) in enumerate(
                zip(prepared.chunks, prepared.prompts), start=1
            )
        ]
        self._write_jsonl(prompts_path, prompt_records)
        responses: list[dict[str, Any]] = []
        response_records: list[dict[str, Any]] = []
        output_chars = 0
        try:
            for index, prompt in enumerate(prepared.prompts, start=1):
                raw = self.llm.generate(prompt)
                output_chars += len(raw)
                responses.append(MaterialDeviceResponseParser.parse(raw))
                response_records.append({"call_index": index, "response": raw})
                self._write_jsonl(responses_path, response_records)
            parameters = self._merge_responses(schema, responses)
            selected_by_id = {
                item.evidence_id: item for item in prepared.selected_evidence
            }
            referenced = self._referenced_ids(parameters)
            evidence_index = [
                self._evidence_record(selected_by_id[evidence_id])
                for evidence_id in referenced if evidence_id in selected_by_id
            ]
            draft = ParameterDraft(
                schema.schema_version,
                "P001",
                schema.domain_id,
                parameters,
                evidence_index,
            )
            validation = MaterialDeviceValidator(schema).validate(draft)
            validation.raise_if_invalid()
            parameters_path = ParameterWriter(
                validator=MaterialDeviceValidator(schema), papers_root=papers_root
            ).write(draft)
            metrics = self._quality_metrics(parameters, selected_by_id)
            manifest = {
                "paper_id": "P001",
                "task": "material_device_only",
                "status": "success",
                "api_calls": len(prepared.prompts),
                "selected_evidence_count": len(prepared.selected_evidence),
                "chunk_count": len(prepared.chunks),
                "max_prompt_chars": prepared.max_prompt_chars,
                "input_chars": prepared.total_prompt_chars,
                "output_chars": output_chars,
                **metrics,
            }
            self._write_yaml(manifest_path, manifest)
        except Exception as error:
            self._write_jsonl(responses_path, response_records)
            self._write_yaml(manifest_path, {
                "paper_id": "P001",
                "task": "material_device_only",
                "status": "failed",
                "api_calls": len(response_records),
                "selected_evidence_count": len(prepared.selected_evidence),
                "chunk_count": len(prepared.chunks),
                "input_chars": prepared.total_prompt_chars,
                "output_chars": output_chars,
                "error_type": type(error).__name__,
            })
            raise
        return MaterialDeviceExtractionResult(
            parameters_path=parameters_path,
            prompts_path=prompts_path,
            responses_path=responses_path,
            run_manifest_path=manifest_path,
            api_calls=manifest["api_calls"],
            selected_evidence_count=manifest["selected_evidence_count"],
            chunk_count=manifest["chunk_count"],
            input_chars=manifest["input_chars"],
            output_chars=manifest["output_chars"],
            extracted_fields=tuple(manifest["extracted_fields"]),
            null_fields=tuple(manifest["null_fields"]),
            evidence_supported_fields=manifest["evidence_supported_fields"],
            unsupported_fields=manifest["unsupported_fields"],
            warnings=tuple(manifest["warnings"]),
            review_required=manifest["review_required"],
        )

    @staticmethod
    def _merge_responses(
        schema: ParameterSchema, responses: list[dict[str, dict[str, Any]]]
    ) -> dict[str, dict[str, Any]]:
        parameters = schema.new_parameters()
        for section in ALLOWED_SECTIONS:
            for field in ALLOWED_FIELDS[section]:
                values: list[dict[str, Any]] = []
                seen: set[str] = set()
                for response in responses:
                    value = response[section][field]
                    candidates = value if isinstance(value, list) else [value]
                    for candidate in candidates:
                        if candidate is None:
                            continue
                        if not isinstance(candidate, dict):
                            raise ParameterResponseError(
                                f"response.{section}.{field} must be null, object, or list"
                            )
                        key = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
                        if key not in seen:
                            seen.add(key)
                            values.append(candidate)
                if len(values) == 1:
                    parameters[section][field] = values[0]
                elif values:
                    parameters[section][field] = values
        return parameters

    @staticmethod
    def _referenced_ids(parameters: dict[str, dict[str, Any]]) -> list[str]:
        references: list[str] = []
        for section in ALLOWED_SECTIONS:
            for value in parameters[section].values():
                entries = value if isinstance(value, list) else [value]
                for entry in entries:
                    if isinstance(entry, dict) and isinstance(entry.get("evidence_refs"), list):
                        for evidence_id in entry["evidence_refs"]:
                            if isinstance(evidence_id, str) and evidence_id not in references:
                                references.append(evidence_id)
        return references

    @classmethod
    def _quality_metrics(
        cls,
        parameters: dict[str, dict[str, Any]],
        evidence: dict[str, PromptEvidence],
    ) -> dict[str, Any]:
        extracted: list[str] = []
        nulls: list[str] = []
        supported = 0
        unsupported = 0
        warnings: list[str] = []
        for section in ALLOWED_SECTIONS:
            for field, value in parameters[section].items():
                name = f"{section}.{field}"
                if value is None:
                    nulls.append(name)
                    continue
                extracted.append(name)
                entries = value if isinstance(value, list) else [value]
                refs = [
                    ref
                    for entry in entries if isinstance(entry, dict)
                    for ref in entry.get("evidence_refs", [])
                    if isinstance(ref, str)
                ]
                if refs and all(ref in evidence for ref in refs):
                    supported += 1
                else:
                    unsupported += 1
                    warnings.append(f"{name}: missing or unknown Evidence reference")
                for entry in entries:
                    if isinstance(entry, dict) and not cls._entry_has_textual_support(entry, evidence):
                        warnings.append(
                            f"{name}: extracted wording needs human grounding review"
                        )
        return {
            "extracted_field_count": len(extracted),
            "null_field_count": len(nulls),
            "extracted_fields": extracted,
            "null_fields": nulls,
            "evidence_supported_fields": supported,
            "unsupported_fields": unsupported,
            "evidence_coverage": round(supported / len(extracted), 4) if extracted else 1.0,
            "warnings": warnings,
            "review_required": bool(unsupported or warnings),
        }

    @staticmethod
    def _entry_has_textual_support(
        entry: dict[str, Any], evidence: dict[str, PromptEvidence]
    ) -> bool:
        texts = " ".join(
            evidence[ref].content
            for ref in entry.get("evidence_refs", [])
            if isinstance(ref, str) and ref in evidence
        )
        normalized_evidence = MaterialDeviceEvidenceFilter.normalize(texts)
        scalar_values = [
            value for key, value in entry.items()
            if key != "evidence_refs" and isinstance(value, str) and len(value.strip()) >= 3
        ]
        if not scalar_values:
            return True
        for value in scalar_values:
            normalized = MaterialDeviceEvidenceFilter.normalize(value)
            meaningful = [token for token in normalized.split() if len(token) >= 3]
            if meaningful and not any(token in normalized_evidence for token in meaningful):
                return False
        return True

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

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(path)

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
            + ("\n" if records else ""),
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _write_yaml(path: Path, payload: Any) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        temporary.replace(path)
