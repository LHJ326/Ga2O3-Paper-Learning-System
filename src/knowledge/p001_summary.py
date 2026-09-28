"""Evidence-validated, summary-only extraction for P001."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.llm import LLMAdapter
from src.schema import Document

from .extractor import ExtractionContext, KnowledgeDraft
from .llm_extractor import LLMKnowledgeExtractor
from .prompt_builder import KnowledgePromptBuilder, PromptEvidence
from .schema import KnowledgeSchema
from .strategy import EvidenceChunker, ExtractionTask, PromptStrategyRegistry
from .strategy_extractor import StrategyKnowledgeExtractor, StrategyPromptBuilder
from .validator import KnowledgeValidator


@dataclass(frozen=True)
class SummaryExtractionResult:
    summary_path: Path
    prompts_path: Path
    responses_path: Path
    run_manifest_path: Path
    evidence_count: int
    input_chars: int
    output_chars: int
    api_response_status: str


class P001SummaryExtractor:
    """Run the Summary strategy only and persist no other knowledge view."""

    def __init__(
        self,
        llm: LLMAdapter,
        *,
        chunker: EvidenceChunker | None = None,
        prompt_builder: StrategyPromptBuilder | None = None,
    ) -> None:
        self.llm = llm
        self.chunker = chunker or EvidenceChunker()
        self.prompt_builder = prompt_builder or StrategyPromptBuilder()
        self.evidence_builder = KnowledgePromptBuilder()
        self.strategy = PromptStrategyRegistry().get(ExtractionTask.SUMMARY)

    def run(
        self,
        *,
        document: Document,
        schema: KnowledgeSchema,
        output_dir: str | Path,
        source_document: str,
        metadata: dict[str, Any] | None = None,
    ) -> SummaryExtractionResult:
        if document.document_id != "P001":
            raise ValueError("summary-only D1 extraction is restricted to P001")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        context = ExtractionContext(
            paper_id="P001",
            document=document,
            schema=schema,
            metadata=metadata or {},
            source_document=source_document,
        )
        evidence = self.evidence_builder.evidence_from_document(document)
        chunks = self.chunker.chunk(evidence, self.strategy)
        prompt_records: list[dict[str, Any]] = []
        response_records: list[dict[str, Any]] = []
        call_records: list[dict[str, Any]] = []
        responses: list[dict[str, Any]] = []
        input_chars = 0
        output_chars = 0
        prompts_path = output_path / "summary_extraction_prompts.jsonl"
        responses_path = output_path / "summary_extraction_responses.jsonl"
        manifest_path = output_path / "summary_extraction_run.yaml"

        try:
            prepared_calls: list[tuple[int, Any, str]] = []
            for call_index, chunk in enumerate(chunks, start=1):
                prompt = self.prompt_builder.build(context, self.strategy, chunk)
                prompt_records.append({
                    "call_index": call_index,
                    "section_id": chunk.section_id,
                    "element_type": chunk.element_type,
                    "chunk_index": chunk.index,
                    "evidence_ids": [item.evidence_id for item in chunk.evidence],
                    "prompt": prompt,
                })
                prepared_calls.append((call_index, chunk, prompt))
                input_chars += len(prompt)
            self._write_prompts(prompts_path, prompt_records)
            self._write_manifest(
                manifest_path,
                status="running",
                evidence_count=len(evidence),
                chunk_count=len(chunks),
                input_chars=input_chars,
                output_chars=0,
                calls=[],
            )

            for call_index, chunk, prompt in prepared_calls:
                response = self.llm.generate(prompt)
                output_chars += len(response)
                responses.append(LLMKnowledgeExtractor._load_response(response))
                response_records.append({
                    "call_index": call_index,
                    "section_id": chunk.section_id,
                    "element_type": chunk.element_type,
                    "response": response,
                })
                call_records.append({
                    "call_index": call_index,
                    "status": "success",
                    "input_chars": len(prompt),
                    "output_chars": len(response),
                })
                self._write_responses(responses_path, response_records)
                self._write_manifest(
                    manifest_path,
                    status="running",
                    evidence_count=len(evidence),
                    chunk_count=len(chunks),
                    input_chars=input_chars,
                    output_chars=output_chars,
                    calls=call_records,
                )

            responses = self._normalize_summary_responses(responses)
            core = StrategyKnowledgeExtractor._merge_core(context, responses)
            references = LLMKnowledgeExtractor._collect_evidence_refs(core)
            core["evidence_traceability"] = {
                "source_document": source_document,
                "evidence_index": [
                    self._evidence_record(item)
                    for item in evidence if item.evidence_id in references
                ],
            }
            domain = {
                "schema_version": "1.0",
                "paper_id": "P001",
                "domain_id": schema.domain_id,
                "schema_path": schema.domain_path.as_posix() if schema.domain_path else None,
                "fields": {},
            }
            draft = KnowledgeDraft("P001", core, domain, "# Summary", "# Key Points")
            KnowledgeValidator(schema).validate(draft).raise_if_invalid()
            summary = self._render_summary(core)

            summary_path = output_path / "summary.md"
            self._write_text(summary_path, summary)
        except Exception as error:
            call_records.append({
                "call_index": len(call_records) + 1,
                "status": "failed",
                "error_type": type(error).__name__,
            })
            self._write_prompts(prompts_path, prompt_records)
            self._write_responses(responses_path, response_records)
            self._write_manifest(
                manifest_path,
                status="failed",
                evidence_count=len(evidence),
                chunk_count=len(chunks),
                input_chars=input_chars,
                output_chars=output_chars,
                calls=call_records,
            )
            raise
        self._write_manifest(
            manifest_path,
            status="success",
            evidence_count=len(evidence),
            chunk_count=len(chunks),
            input_chars=input_chars,
            output_chars=output_chars,
            summary_chars=len(summary),
            calls=call_records,
            referenced_evidence_count=len(core["evidence_traceability"]["evidence_index"]),
        )
        return SummaryExtractionResult(
            summary_path=summary_path,
            prompts_path=prompts_path,
            responses_path=responses_path,
            run_manifest_path=manifest_path,
            evidence_count=len(evidence),
            input_chars=input_chars,
            output_chars=output_chars,
            api_response_status="success",
        )

    @staticmethod
    def _normalize_summary_responses(
        responses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        specifications = {
            "research_problem": ("statement", ("claim", "problem")),
            "methodology": ("description", ("statement", "method")),
            "results": ("claim", ("statement", "result")),
            "innovation": ("claim", ("statement", "innovation")),
            "limitations": ("statement", ("claim", "limitation")),
        }
        normalized_responses: list[dict[str, Any]] = []
        for response in responses:
            normalized = dict(response)
            for field, (text_field, aliases) in specifications.items():
                value = response.get(field, [])
                items = value if isinstance(value, list) else [value]
                normalized_items: list[dict[str, Any]] = []
                for item in items:
                    if isinstance(item, str):
                        text = item.strip()
                        refs = list(dict.fromkeys(re.findall(r"\bE\d{5}\b", text)))
                    elif isinstance(item, dict):
                        raw_text = item.get(text_field)
                        if not isinstance(raw_text, str):
                            raw_text = next(
                                (item.get(alias) for alias in aliases if isinstance(item.get(alias), str)),
                                "",
                            )
                        text = raw_text.strip()
                        raw_refs = item.get("evidence_refs", [])
                        if isinstance(raw_refs, str):
                            raw_refs = re.findall(r"\bE\d{5}\b", raw_refs)
                        refs = list(dict.fromkeys(
                            ref for ref in raw_refs if isinstance(ref, str)
                        )) if isinstance(raw_refs, list) else []
                        if not refs:
                            refs = list(dict.fromkeys(re.findall(r"\bE\d{5}\b", text)))
                    else:
                        continue
                    if text and refs:
                        normalized_items.append({text_field: text, "evidence_refs": refs})
                normalized[field] = normalized_items
            normalized_responses.append(normalized)
        return normalized_responses

    @staticmethod
    def _render_summary(core: dict[str, Any]) -> str:
        sections = (
            ("Research Objective", "research_problem", "statement", 5,
             ("aim", "target", "develop", "need", "propos", "energy-efficient")),
            ("Core Innovations", "innovation", "claim", 8,
             ("novel", "innovative", "new scheme", "first", "photosensitive", "solar-blind")),
            ("Experimental Results", "results", "claim", 12,
             ("91.07", "10^6", "254.4", "3.25", "78.44", "retention", "endurance")),
            ("Methodology", "methodology", "description", 8,
             ("fabricat", "measur", "evaluat", "vgg-8", "cifar-10", "characteriz")),
            ("Reported Limitations", "limitations", "statement", 5,
             ("limit", "difficult", "compromis", "cannot", "challenge", "power consumption")),
        )
        lines = ["# P001 Knowledge Summary"]
        for heading, field, text_field, limit, keywords in sections:
            lines.extend(["", f"## {heading}", ""])
            candidates: list[tuple[int, int, dict[str, Any]]] = []
            for position, item in enumerate(core.get(field, [])):
                text = item[text_field].strip()
                lowered = text.casefold()
                score = sum(3 for keyword in keywords if keyword in lowered)
                score += min(3, len(re.findall(r"\d", text)))
                candidates.append((-score, position, item))
            selected: list[tuple[set[str], dict[str, Any]]] = []
            for _, _, item in sorted(candidates):
                text = item[text_field].strip()
                tokens = set(re.findall(r"[a-z0-9]+", text.casefold()))
                if any(
                    tokens and previous
                    and len(tokens & previous) / len(tokens | previous) >= 0.62
                    for previous, _ in selected
                ):
                    continue
                selected.append((tokens, item))
                if len(selected) >= limit:
                    break
            for _, item in selected:
                text = item[text_field].strip()
                refs = tuple(dict.fromkeys(item["evidence_refs"]))
                citations = " ".join(f"[{ref}]" for ref in refs if f"[{ref}]" not in text)
                lines.append(f"- {text}{(' ' + citations) if citations else ''}")
            if not selected:
                lines.append("- Not explicitly identified in the extracted evidence.")
        return "\n".join(lines)

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
    def _write_text(path: Path, text: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
        temporary.replace(path)

    @classmethod
    def _write_prompts(cls, path: Path, records: list[dict[str, Any]]) -> None:
        cls._write_text(
            path,
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
        )

    @classmethod
    def _write_responses(cls, path: Path, records: list[dict[str, Any]]) -> None:
        cls._write_text(
            path,
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records),
        )

    @classmethod
    def _write_manifest(cls, path: Path, **payload: Any) -> None:
        cls._write_text(path, yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))
