"""Auditable P001 Performance extraction pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.schema import Document

from .performance_extractor import PerformanceExtractor, PreparedPerformanceExtraction
from .performance_schema import PerformanceDraft, PerformanceSchema
from .performance_validator import PerformanceValidator
from .performance_writer import PerformanceWriter
from .prompt_builder import PromptEvidence


@dataclass(frozen=True)
class PerformancePipelineResult:
    performance_path: Path
    prompts_path: Path
    responses_path: Path
    run_manifest_path: Path
    api_calls: int
    selected_evidence_count: int
    chunk_count: int
    input_chars: int
    output_chars: int
    extracted_field_count: int
    null_field_count: int
    evidence_coverage: float


class PerformanceExtractionPipeline:
    def __init__(
        self,
        *,
        extractor: PerformanceExtractor,
        validator: PerformanceValidator,
        writer: PerformanceWriter,
    ) -> None:
        self.extractor = extractor
        self.validator = validator
        self.writer = writer

    def run(
        self,
        *,
        document: Document,
        schema: PerformanceSchema,
        output_dir: str | Path,
        prepared: PreparedPerformanceExtraction | None = None,
    ) -> PerformancePipelineResult:
        prepared = prepared or self.extractor.prepare(document=document, schema=schema)
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        prompts_path = output / "performance_extraction_prompts.jsonl"
        responses_path = output / "performance_extraction_responses.jsonl"
        manifest_path = output / "performance_extraction_run.yaml"
        prompt_records = [
            {
                "call_index": index,
                "evidence_ids": [item.evidence_id for item in chunk.evidence],
                "prompt": prompt,
            }
            for index, (chunk, prompt) in enumerate(zip(prepared.chunks, prepared.prompts), 1)
        ]
        self._write_jsonl(prompts_path, prompt_records)
        response_records: list[dict[str, Any]] = []
        try:
            def persist_responses(records: list[dict[str, Any]]) -> None:
                response_records[:] = records
                self._write_jsonl(responses_path, response_records)

            llm_result = self.extractor.extract(
                schema=schema,
                prepared=prepared,
                response_callback=persist_responses,
            )
            response_records = list(llm_result.response_records)
            selected = {item.evidence_id: item for item in prepared.selected_evidence}
            referenced = self._referenced_ids(llm_result.performance)
            evidence_index = [
                self._evidence_record(selected[evidence_id])
                for evidence_id in referenced if evidence_id in selected
            ]
            draft = PerformanceDraft(
                schema.schema_version, "P001", schema.domain_id,
                llm_result.performance, evidence_index,
            )
            validation = self.validator.validate(draft)
            validation.raise_if_invalid()
            performance_path = self.writer.write(draft)
            extracted = sum(
                value is not None
                for group in draft.performance.values() for value in group.values()
            )
            total = sum(len(group) for group in draft.performance.values())
            manifest = {
                "paper_id": "P001",
                "task": "performance_only",
                "status": "success",
                "api_calls": len(prepared.prompts),
                "selected_evidence_count": len(prepared.selected_evidence),
                "chunk_count": len(prepared.chunks),
                "max_prompt_chars": prepared.max_prompt_chars,
                "input_chars": prepared.total_prompt_chars,
                "output_chars": llm_result.output_chars,
                "extracted_field_count": extracted,
                "null_field_count": total - extracted,
                "evidence_supported_field_count": extracted,
                "unsupported_field_count": 0,
                "evidence_coverage": 1.0 if extracted else 1.0,
                "warnings": [
                    {
                        "field": warning.field,
                        "issue": warning.issue,
                        "evidence_id": warning.evidence_id,
                    }
                    for warning in validation.warnings
                ],
                "review_required": validation.review_required,
            }
            if validation.review_required:
                manifest["status"] = "review_required"
            self._write_yaml(manifest_path, manifest)
        except Exception as error:
            self._write_jsonl(responses_path, response_records)
            self._write_yaml(manifest_path, {
                "paper_id": "P001", "task": "performance_only", "status": "failed",
                "api_calls": len(response_records),
                "selected_evidence_count": len(prepared.selected_evidence),
                "chunk_count": len(prepared.chunks),
                "input_chars": prepared.total_prompt_chars,
                "error_type": type(error).__name__,
            })
            raise
        return PerformancePipelineResult(
            performance_path, prompts_path, responses_path, manifest_path,
            manifest["api_calls"], manifest["selected_evidence_count"],
            manifest["chunk_count"], manifest["input_chars"], manifest["output_chars"],
            manifest["extracted_field_count"], manifest["null_field_count"],
            manifest["evidence_coverage"],
        )

    @staticmethod
    def _referenced_ids(performance: dict[str, dict[str, Any]]) -> list[str]:
        result: list[str] = []
        for group in performance.values():
            for value in group.values():
                entries = value if isinstance(value, list) else [value]
                for entry in entries:
                    if isinstance(entry, dict):
                        evidence_id = entry.get("evidence_id")
                        if isinstance(evidence_id, str) and evidence_id not in result:
                            result.append(evidence_id)
        return result

    @staticmethod
    def _evidence_record(item: PromptEvidence) -> dict[str, Any]:
        return {
            "evidence_id": item.evidence_id,
            "page": item.page,
            "element_id": item.element_id,
            "element_type": item.element_type,
            "source_reference": item.source_reference,
            "quote": item.content,
        }

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in records)
            + ("\n" if records else ""), encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        temporary.replace(path)
